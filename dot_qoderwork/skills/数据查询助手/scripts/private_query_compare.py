"""
跨库比对工具 (ERP MySQL vs Doris 数仓)
用法: python query_compare.py <command> [args...]

支持的命令:
  full_compare  <YYYY-MM>         - 全量按cost_code比对(MySQL费用账单 vs Doris科目分摊)
  code_diff     <YYYY-MM> <code>  - 单科目逐日差异比对
"""
import sys, json
from datetime import datetime
from decimal import Decimal
import pymysql

MYSQL_CONFIG = {
    "host": "rr-2zeh95evp4y3t94fkmo.mysql.rds.aliyuncs.com",
    "port": 3306,
    "user": "oms_query",
    "password": "%zVtq^h$30fQIDav",
    "database": "fms_cost",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

DORIS_CONFIG = {
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

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def get_days(month):
    year, mon = month.split("-")
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            return [(year, mon, day) for day in range(1, d + 1)]
        except ValueError:
            continue
    return []

def fetch_mysql(month):
    """从 MySQL expense_detail 按月逐日汇总"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    agg = {}
    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT cost_code, COUNT(*) AS cnt,
               SUM(income_cost) AS total_income,
               SUM(expend_cost) AS total_expend,
               SUM(no_tax_amount) AS total_no_tax
        FROM expense_detail
        WHERE trans_dt = %s
        GROUP BY cost_code
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt,))
            for r in cur.fetchall():
                cc = r["cost_code"] or "(空)"
                if cc not in agg:
                    agg[cc] = {"cnt": 0, "income": Decimal(0), "expend": Decimal(0), "no_tax": Decimal(0)}
                agg[cc]["cnt"] += r["cnt"]
                agg[cc]["income"] += Decimal(r["total_income"] or 0)
                agg[cc]["expend"] += Decimal(r["total_expend"] or 0)
                agg[cc]["no_tax"] += Decimal(r["total_no_tax"] or 0)
    conn.close()
    return agg

def fetch_doris(month):
    """从 Doris finance_cost_sbjct 按月逐日汇总"""
    conn = pymysql.connect(**DORIS_CONFIG)
    agg = {}
    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT cost_code, COUNT(*) AS cnt,
               SUM(share) AS total_share,
               SUM(no_tax_amount) AS total_no_tax
        FROM doris_dws_finance_cost_sbjct
        WHERE dt = %s
        GROUP BY cost_code
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt,))
            for r in cur.fetchall():
                cc = r["cost_code"] or "(空)"
                if cc not in agg:
                    agg[cc] = {"cnt": 0, "share": Decimal(0), "no_tax": Decimal(0)}
                agg[cc]["cnt"] += r["cnt"]
                agg[cc]["share"] += Decimal(r["total_share"] or 0)
                agg[cc]["no_tax"] += Decimal(r["total_no_tax"] or 0)
    conn.close()
    return agg

def full_compare(month: str):
    """全量比对"""
    mysql_data = fetch_mysql(month)
    doris_data = fetch_doris(month)

    all_codes = sorted(set(list(mysql_data.keys()) + list(doris_data.keys())))
    results = []
    for cc in all_codes:
        m = mysql_data.get(cc, {"cnt": 0, "income": Decimal(0), "expend": Decimal(0), "no_tax": Decimal(0)})
        d = doris_data.get(cc, {"cnt": 0, "share": Decimal(0), "no_tax": Decimal(0)})

        mysql_amount = m["income"] - m["expend"]
        doris_amount = d["share"]
        diff = mysql_amount - doris_amount
        pct = float(diff / doris_amount * 100) if doris_amount != 0 else (0 if mysql_amount == 0 else 999)

        results.append({
            "cost_code": cc,
            "mysql_cnt": m["cnt"],
            "doris_cnt": d["cnt"],
            "mysql_amount": float(mysql_amount),
            "doris_amount": float(doris_amount),
            "diff": float(diff),
            "diff_pct": round(pct, 2),
        })

    results.sort(key=lambda x: -abs(x["diff"]))
    significant = [r for r in results if abs(r["diff"]) > 100]

    return {
        "月份": month,
        "MySQL科目数": len(mysql_data),
        "Doris科目数": len(doris_data),
        "显著差异(>100元)": significant,
        "全部比对": results,
    }

def code_diff(month: str, cost_code: str):
    """单科目逐日差异"""
    conn_mysql = pymysql.connect(**MYSQL_CONFIG)
    conn_doris = pymysql.connect(**DORIS_CONFIG)

    daily = []
    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"

        with conn_mysql.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS cnt, SUM(income_cost) AS inc, SUM(expend_cost) AS exp
                FROM expense_detail WHERE trans_dt = %s AND cost_code = %s
            """, (dt, cost_code))
            m = cur.fetchone()

        with conn_doris.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS cnt, SUM(share) AS share
                FROM doris_dws_finance_cost_sbjct WHERE dt = %s AND cost_code = %s
            """, (dt, cost_code))
            d = cur.fetchone()

        m_amt = float((m["inc"] or 0) - (m["exp"] or 0))
        d_amt = float(d["share"] or 0)
        daily.append({"日期": dt, "mysql_cnt": m["cnt"], "doris_cnt": d["cnt"],
                       "mysql_amount": m_amt, "doris_amount": d_amt, "diff": round(m_amt - d_amt, 2)})

    conn_mysql.close()
    conn_doris.close()
    return {"月份": month, "cost_code": cost_code, "逐日比对": daily}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    try:
        if cmd == "full_compare" and len(sys.argv) >= 3:
            print(json.dumps(full_compare(sys.argv[2]), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        elif cmd == "code_diff" and len(sys.argv) >= 4:
            print(json.dumps(code_diff(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2, cls=DecimalEncoder))
        else:
            print(f"未知命令或参数不足: {cmd}")
            print(__doc__)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)
