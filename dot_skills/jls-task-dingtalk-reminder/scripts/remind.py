#!/usr/bin/env python3
"""
家里事任务查询与提醒格式化脚本

用法:
  python3 remind.py              # 查询今日结束日期任务
  python3 remind.py --date 2026-06-16   # 指定日期查询
  python3 remind.py --dept 393819645    # 指定部门（默认产品组）
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pymysql
except ImportError:
    print(json.dumps({"error": "pymysql not installed. Run: pip install pymysql"}))
    sys.exit(1)


def load_db_profile(profile_name):
    path = Path.home() / ".config" / "db-profiles" / f"{profile_name}.env"
    if not path.exists():
        raise FileNotFoundError(f"Database profile not found: {path}")
    data = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip("\"").strip("'")
    return data


def make_db_config(profile_name):
    data = load_db_profile(profile_name)
    return {
        "host": os.environ.get("DB_HOST", data["DB_HOST"]),
        "port": int(os.environ.get("DB_PORT", data["DB_PORT"])),
        "user": os.environ.get("DB_USER", data["DB_USER"]),
        "password": os.environ.get("DB_PASSWORD", data["DB_PASSWORD"]),
        "database": os.environ.get("DB_NAME", data.get("DB_NAME", "jls_core")),
        "charset": os.environ.get("DB_CHARSET", data.get("DB_CHARSET", "utf8mb4")),
    }


DB_CONFIG = make_db_config(os.environ.get("DB_PROFILE", "wms-mysql"))

PRODUCT_DEPT_ID = "393819645"

STATUS_MAP = {
    5: "进行中",
    10: "逾期进行中",
}


def query_tasks(target_date=None, dept_id=None):
    if target_date is None:
        date_expr = "CURDATE()"
        date_label = "今日"
    else:
        date_expr = f"'{target_date}'"
        date_label = target_date

    dept = dept_id or PRODUCT_DEPT_ID

    sql = f"""
        SELECT t.executor, he.employee_name, he.dingding_user_id,
               t.task_content, t.current_status
        FROM task t
        JOIN hris_ads.hris_employee he ON he.job_number = t.executor
        WHERE he.dept_id = '{dept}'
          AND he.deleted = 0
          AND he.status = 1
          AND DATE(t.end_date) = DATE({date_expr})
          AND t.current_status IN (5, 10)
        ORDER BY t.executor
    """

    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "has_tasks": False,
            "date": date_label,
            "message": f"{date_label}产品组无结束日期在进行中/逾期进行中的家里事任务",
            "mentions": [],
        }

    result_by_person = {}
    mentions = []
    for executor, name, dingding_uid, content, status in rows:
        status_name = STATUS_MAP.get(status, str(status))
        task_name = content.split("\n")[0][:50]
        key = (executor, name, dingding_uid)
        if key not in result_by_person:
            result_by_person[key] = []
            mentions.append({"name": name, "dingding_user_id": dingding_uid})
        result_by_person[key].append({"task": task_name, "status": status_name})

    lines = [f"【家里事提醒】{date_label}结束日期任务：", ""]
    for (exec_id, name, dingding_uid), tasks in result_by_person.items():
        lines.append(f"工号：{exec_id}  姓名：{name} <@{dingding_uid}>")
        for t in tasks:
            lines.append(f"  - {t['task']}（{t['status']}）")
        lines.append("")

    return {
        "has_tasks": True,
        "date": date_label,
        "message": "\n".join(lines),
        "mentions": mentions,
        "task_count": len(rows),
        "person_count": len(result_by_person),
    }


def main():
    parser = argparse.ArgumentParser(description="家里事任务提醒查询")
    parser.add_argument("--date", help="目标日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--dept", help="部门 dept_id，默认产品组 393819645")
    args = parser.parse_args()

    result = query_tasks(args.date, args.dept)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
