#!/usr/bin/env python3
"""
家里事任务查询脚本

用法:
  python3 query_tasks.py                                        # 今日验收截止日提醒
  python3 query_tasks.py --date 2026-06-15                      # 指定日期查询
  python3 query_tasks.py --mode my-tasks --executor 11723       # 查某人的进行中任务及到期时间
  python3 query_tasks.py --mode expiring --days 7               # 未来N天快到期的任务
  python3 query_tasks.py --status 5,10                          # 按状态筛选
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta

try:
    import pymysql
except ImportError:
    print(json.dumps({"error": "pymysql not installed. Run: pip install pymysql"}))
    sys.exit(1)

DB_CONFIG = {
    "host": "rr-2ze2z5m8919dglgt1po.mysql.rds.aliyuncs.com",
    "port": 3306,
    "user": "wms_query",
    "password": "^6u5K2cc4bQW%Rg",
    "database": "jls_core",
    "charset": "utf8mb4",
}

PRODUCT_DEPT_ID = "393819645"

STATUS_MAP = {
    1: "待启动", 5: "进行中", 10: "逾期进行中",
    15: "已完成", 20: "已验收", 25: "已驳回", 30: "已归档",
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def query_daily_reminder(target_date=None, statuses=None, executor=None):
    """场景一：今日/指定日期验收截止日提醒"""
    if target_date is None:
        date_expr = "CURDATE()"
        date_label = "今日"
    else:
        date_expr = f"'{target_date}'"
        date_label = target_date

    if statuses is None:
        statuses = [5, 10]
    status_str = ",".join(str(s) for s in statuses)

    executor_filter = f"AND t.executor = '{executor}'" if executor else ""

    sql = f"""
        SELECT t.executor, he.employee_name, he.dingding_user_id,
               t.task_content, t.current_status, t.acceptance_deadline
        FROM task t
        JOIN hris_ads.hris_employee he ON he.job_number = t.executor
        WHERE he.dept_id = '{PRODUCT_DEPT_ID}'
          AND he.deleted = 0
          AND he.status = 1
          AND DATE(t.acceptance_deadline) = DATE({date_expr})
          AND t.current_status IN ({status_str})
          {executor_filter}
        ORDER BY t.executor
    """

    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "mode": "daily_reminder",
            "has_tasks": False,
            "date": date_label,
            "message": f"{date_label}产品组无验收截止日在{'/'.join(STATUS_MAP.get(s, str(s)) for s in statuses)}的家里事任务",
            "mentions": [],
        }

    result_by_person = {}
    mentions = []
    for exec_id, name, dingding_uid, content, status, deadline in rows:
        status_name = STATUS_MAP.get(status, str(status))
        task_name = content.split("\n")[0][:50]
        key = (exec_id, name, dingding_uid)
        if key not in result_by_person:
            result_by_person[key] = []
            mentions.append({"name": name, "dingding_user_id": dingding_uid})
        result_by_person[key].append({"task": task_name, "status": status_name})

    lines = [f"【家里事提醒】{date_label}验收截止日任务：", ""]
    for (exec_id, name, _), tasks in result_by_person.items():
        lines.append(f"工号：{exec_id}  姓名：{name}")
        for t in tasks:
            lines.append(f"  - {t['task']}（{t['status']}）")
        lines.append("")

    return {
        "mode": "daily_reminder",
        "has_tasks": True,
        "date": date_label,
        "message": "\n".join(lines),
        "mentions": mentions,
        "task_count": len(rows),
        "person_count": len(result_by_person),
    }


def query_my_tasks(job_number):
    """场景四：某人的所有进行中任务及到期时间"""
    sql = f"""
        SELECT t.task_code, t.task_content, t.current_status,
               t.acceptance_deadline, t.start_date, t.end_date,
               DATEDIFF(t.acceptance_deadline, CURDATE()) as days_remaining
        FROM task t
        WHERE t.executor = '{job_number}'
          AND t.current_status IN (1, 5, 10)
        ORDER BY t.acceptance_deadline
    """

    conn = get_conn()
    try:
        cursor = conn.cursor()
        # 同时获取员工姓名
        cursor.execute(f"""
            SELECT employee_name FROM hris_ads.hris_employee
            WHERE job_number = '{job_number}' AND deleted = 0
            LIMIT 1
        """)
        name_row = cursor.fetchone()
        employee_name = name_row[0] if name_row else job_number

        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "mode": "my_tasks",
            "has_tasks": False,
            "executor": job_number,
            "employee_name": employee_name,
            "message": f"{employee_name}当前没有进行中的家里事任务",
        }

    tasks = []
    lines = [f"【{employee_name} 的进行中任务】", ""]
    for i, (code, content, status, deadline, start, end, days) in enumerate(rows, 1):
        status_name = STATUS_MAP.get(status, str(status))
        task_name = content.split("\n")[0][:50]
        deadline_str = deadline.strftime("%Y-%m-%d") if isinstance(deadline, (date, datetime)) else str(deadline)
        days_text = f"剩余{days}天" if days >= 0 else f"已逾期{abs(days)}天"

        tasks.append({
            "task_code": code, "task_name": task_name,
            "status": status_name, "deadline": deadline_str,
            "days_remaining": days,
        })
        lines.append(f"{i}. {task_name}")
        lines.append(f"   截止日：{deadline_str}（{days_text}）| 状态：{status_name}")
        lines.append("")

    return {
        "mode": "my_tasks",
        "has_tasks": True,
        "executor": job_number,
        "employee_name": employee_name,
        "message": "\n".join(lines),
        "tasks": tasks,
        "task_count": len(rows),
    }


def query_expiring(days=3, statuses=None):
    """场景五：未来N天快到期的任务"""
    if statuses is None:
        statuses = [5, 10]
    status_str = ",".join(str(s) for s in statuses)

    sql = f"""
        SELECT t.executor, he.employee_name, he.dingding_user_id,
               t.task_content, t.current_status, t.acceptance_deadline,
               DATEDIFF(t.acceptance_deadline, CURDATE()) as days_remaining
        FROM task t
        JOIN hris_ads.hris_employee he ON he.job_number = t.executor
        WHERE he.dept_id = '{PRODUCT_DEPT_ID}'
          AND he.deleted = 0
          AND he.status = 1
          AND t.acceptance_deadline >= CURDATE()
          AND t.acceptance_deadline <= DATE_ADD(CURDATE(), INTERVAL {days} DAY)
          AND t.current_status IN ({status_str})
        ORDER BY t.acceptance_deadline, t.executor
    """

    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "mode": "expiring",
            "has_tasks": False,
            "days": days,
            "message": f"产品组近三日内无即将到期的家里事任务",
            "mentions": [],
        }

    # 按截止日期分组
    by_date = {}
    mentions = []
    mentioned_ids = set()
    for exec_id, name, dingding_uid, content, status, deadline, days_rem in rows:
        status_name = STATUS_MAP.get(status, str(status))
        task_name = content.split("\n")[0][:50]
        deadline_str = deadline.strftime("%Y-%m-%d") if isinstance(deadline, (date, datetime)) else str(deadline)

        if deadline_str not in by_date:
            by_date[deadline_str] = {"days_remaining": days_rem, "persons": {}}

        person_key = (exec_id, name, dingding_uid)
        if person_key not in by_date[deadline_str]["persons"]:
            by_date[deadline_str]["persons"][person_key] = []
            if exec_id not in mentioned_ids:
                mentions.append({"name": name, "dingding_user_id": dingding_uid})
                mentioned_ids.add(exec_id)
        by_date[deadline_str]["persons"][person_key].append({"task": task_name, "status": status_name})

    lines = [f"【产品组近三日要到期任务提醒】", ""]
    for deadline_str in sorted(by_date.keys()):
        info = by_date[deadline_str]
        days_rem = info["days_remaining"]
        lines.append(f"{deadline_str}（{days_rem}天后）：")
        for (exec_id, name, _), tasks in info["persons"].items():
            lines.append(f"  工号：{exec_id}  {name} @{name}")
            for t in tasks:
                lines.append(f"    - {t['task']}（{t['status']}）")
        lines.append("")

    return {
        "mode": "expiring",
        "has_tasks": True,
        "days": days,
        "message": "\n".join(lines),
        "mentions": mentions,
        "task_count": len(rows),
        "person_count": len(mentioned_ids),
    }


def main():
    parser = argparse.ArgumentParser(description="家里事任务查询")
    parser.add_argument("--mode", choices=["reminder", "my-tasks", "expiring"],
                        default="reminder", help="查询模式")
    parser.add_argument("--date", help="目标日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--status", help="状态筛选，逗号分隔，如 5,10")
    parser.add_argument("--executor", help="执行人工号")
    parser.add_argument("--days", type=int, default=3, help="未来N天（expiring模式），默认3天")
    args = parser.parse_args()

    statuses = [int(s) for s in args.status.split(",")] if args.status else None

    if args.mode == "my-tasks":
        if not args.executor:
            print(json.dumps({"error": "my-tasks 模式需要 --executor 参数指定工号"}))
            sys.exit(1)
        result = query_my_tasks(args.executor)
    elif args.mode == "expiring":
        result = query_expiring(args.days, statuses)
    else:
        result = query_daily_reminder(args.date, statuses, args.executor)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
