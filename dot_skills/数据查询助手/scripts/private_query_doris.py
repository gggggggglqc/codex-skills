"""
Doris 数仓查询工具
用法: python query_doris.py <command> [args...]

支持的命令:
  cost_summary     <YYYY-MM> [cost_code]    - 科目费用分摊汇总(可按cost_code过滤)
  ep_summary       <YYYY-MM> [expense_code]  - EP费用编码汇总(净利V2)
  cost_daily       <YYYY-MM> <cost_code>     - 科目费用逐日明细
  ep_daily         <YYYY-MM> [expense_code]  - EP费用逐日汇总
  cost_failure     <YYYY-MM>                 - 分摊失败记录统计
"""
import sys, json
from datetime import datetime
from decimal import Decimal
import pymysql

DB_CONFIG = {
    "host": "cmccnet.jiabs.com",
    "port": 19130,
    "user": "db_devops",
    "password": "mVk3ydQVwN",
    "database": "dp_dws",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 30,
    "read_timeout": 120,
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def cost_summary(month: str, cost_code: str = None):
    """科目费用分摊汇总（finance_cost_sbjct）- 逐日查询避免超时"""
    conn = get_conn()
    year, mon = month.split("-")
    days_in_month = 31
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            days_in_month = d
            break
        except ValueError:
            continue

    agg = {}
    for day in range(1, days_in_month + 1):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT cost_code, COUNT(*) AS cnt,
               SUM(share) AS total_share,
               SUM(no_tax_amount) AS total_no_tax
        FROM doris_dws_finance_cost_sbjct
        WHERE dt = %s
        """
        params = [dt]
        if cost_code:
            sql += " AND cost_code = %s"
            params.append(cost_code)
        sql += " GROUP BY cost_code"

        with conn.cursor() as cur:
            cur.execute(sql, params)
            for r in cur.fetchall():
                cc = r["cost_code"] or "(空)"
                if cc not in agg:
                    agg[cc] = {"cost_code": cc, "cnt": 0, "total_share": Decimal(0), "total_no_tax": Decimal(0)}
                agg[cc]["cnt"] += r["cnt"]
                agg[cc]["total_share"] += Decimal(r["total_share"] or 0)
                agg[cc]["total_no_tax"] += Decimal(r["total_no_tax"] or 0)
    conn.close()

    result_list = sorted(agg.values(), key=lambda x: -x["cnt"])
    return {"月份": month, "cost_code过滤": cost_code, "科目汇总": result_list}

def ep_summary(month: str, expense_code: str = None):
    """EP费用编码汇总（net_profit_check_report_v2）- 逐日查询"""
    conn = get_conn()
    year, mon = month.split("-")
    days_in_month = 31
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            days_in_month = d
            break
        except ValueError:
            continue

    agg = {}
    for day in range(1, days_in_month + 1):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT expense_code, COUNT(*) AS cnt,
               SUM(expense_amount) AS total_amount
        FROM doris_app_net_profit_check_report_v2
        WHERE dt = %s
        """
        params = [dt]
        if expense_code:
            sql += " AND expense_code = %s"
            params.append(expense_code)
        sql += " GROUP BY expense_code"

        with conn.cursor() as cur:
            cur.execute(sql, params)
            for r in cur.fetchall():
                ec = r["expense_code"] or "(空)"
                if ec not in agg:
                    agg[ec] = {"expense_code": ec, "cnt": 0, "total_amount": Decimal(0)}
                agg[ec]["cnt"] += r["cnt"]
                agg[ec]["total_amount"] += Decimal(r["total_amount"] or 0)
    conn.close()

    result_list = sorted(agg.values(), key=lambda x: -x["cnt"])
    return {"月份": month, "expense_code过滤": expense_code, "EP汇总": result_list}

def cost_daily(month: str, cost_code: str):
    """科目费用逐日明细"""
    conn = get_conn()
    year, mon = month.split("-")
    days_in_month = 31
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            days_in_month = d
            break
        except ValueError:
            continue

    daily = []
    for day in range(1, days_in_month + 1):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT COUNT(*) AS cnt,
               SUM(share) AS total_share,
               SUM(no_tax_amount) AS total_no_tax
        FROM doris_dws_finance_cost_sbjct
        WHERE dt = %s AND cost_code = %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt, cost_code))
            r = cur.fetchone()
            daily.append({
                "日期": dt,
                "记录数": r["cnt"],
                "分摊金额": float(r["total_share"] or 0),
                "不含税金额": float(r["total_no_tax"] or 0),
            })
    conn.close()
    return {"月份": month, "cost_code": cost_code, "逐日明细": daily}

def ep_daily(month: str, expense_code: str = None):
    """EP费用逐日汇总"""
    conn = get_conn()
    year, mon = month.split("-")
    days_in_month = 31
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            days_in_month = d
            break
        except ValueError:
            continue

    daily = []
    for day in range(1, days_in_month + 1):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT COUNT(*) AS cnt,
               SUM(expense_amount) AS total_amount
        FROM doris_app_net_profit_check_report_v2
        WHERE dt = %s
        """
        params = [dt]
        if expense_code:
            sql += " AND expense_code = %s"
            params.append(expense_code)

        with conn.cursor() as cur:
            cur.execute(sql, params)
            r = cur.fetchone()
            daily.append({
                "日期": dt,
                "记录数": r["cnt"],
                "金额合计": float(r["total_amount"] or 0),
            })
    conn.close()
    return {"月份": month, "expense_code过滤": expense_code, "逐日明细": daily}

def cost_failure(month: str):
    """分摊失败记录统计"""
    conn = get_conn()
    year, mon = month.split("-")
    days_in_month = 31
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            days_in_month = d
            break
        except ValueError:
            continue

    total = 0
    agg = {}
    for day in range(1, days_in_month + 1):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT cost_code, COUNT(*) AS cnt
        FROM doris_dws_finance_cost_sbjct_failure
        WHERE dt = %s
        GROUP BY cost_code
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt,))
            for r in cur.fetchall():
                cc = r["cost_code"] or "(空)"
                agg[cc] = agg.get(cc, 0) + r["cnt"]
                total += r["cnt"]
    conn.close()

    result_list = [{"cost_code": k, "cnt": v} for k, v in sorted(agg.items(), key=lambda x: -x[1])]
    return {"月份": month, "失败总数": total, "按科目": result_list}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    try:
        if cmd == "cost_summary" and len(sys.argv) >= 3:
            cc = sys.argv[3] if len(sys.argv) >= 4 else None
            print(json.dumps(cost_summary(sys.argv[2], cc), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        elif cmd == "ep_summary" and len(sys.argv) >= 3:
            ec = sys.argv[3] if len(sys.argv) >= 4 else None
            print(json.dumps(ep_summary(sys.argv[2], ec), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        elif cmd == "cost_daily" and len(sys.argv) >= 4:
            print(json.dumps(cost_daily(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        elif cmd == "ep_daily" and len(sys.argv) >= 3:
            ec = sys.argv[3] if len(sys.argv) >= 4 else None
            print(json.dumps(ep_daily(sys.argv[2], ec), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        elif cmd == "cost_failure" and len(sys.argv) >= 3:
            print(json.dumps(cost_failure(sys.argv[2]), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        else:
            print(f"未知命令或参数不足: {cmd}")
            print(__doc__)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)
