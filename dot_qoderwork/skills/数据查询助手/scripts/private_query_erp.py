"""
ERP MySQL 查询工具
用法: python query_erp.py <command> [args...]

支持的命令:
  voucher_status   <YYYY-MM>            - 凭证审核状态
  payment_push     <YYYY-MM>            - 出纳付款单推送状态
  receipt_push     <YYYY-MM>            - 出纳收款单推送状态
  expense_summary  <YYYY-MM> [cost_code] - 费用账单汇总(可按cost_code过滤)
  duplicate_check  <YYYY-MM-DD>         - 重复凭证检查
  payment_detail   <YYYY-MM> <order_source> - 付款单明细(按来源)
"""
import sys, json
from datetime import datetime
import pymysql

DB_CONFIG = {
    "host": "rr-2zeh95evp4y3t94fkmo.mysql.rds.aliyuncs.com",
    "port": 3306,
    "user": "oms_query",
    "password": "%zVtq^h$30fQIDav",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

def get_conn(db="fms_bill"):
    cfg = {**DB_CONFIG, "database": db}
    return pymysql.connect(**cfg)

def voucher_status(month: str):
    """凭证审核状态统计"""
    conn = get_conn("fms_bill")
    sql = """
    SELECT voucher_status, COUNT(*) AS cnt,
           SUM(debit_amount) AS total_debit
    FROM voucher
    WHERE DATE_FORMAT(business_date, '%%Y-%%m') = %s
    GROUP BY voucher_status
    ORDER BY voucher_status
    """
    with conn.cursor() as cur:
        cur.execute(sql, (month,))
        rows = cur.fetchall()
    conn.close()

    total = sum(r["cnt"] for r in rows)
    unaudited = sum(r["cnt"] for r in rows if r["voucher_status"] != 2)
    result = {
        "月份": month,
        "凭证总数": total,
        "未审核数": unaudited,
        "明细": rows
    }
    return result

def payment_push(month: str):
    """付款单推送状态"""
    conn = get_conn("fms_bill")
    sql = """
    SELECT order_source, push_status, COUNT(*) AS cnt,
           SUM(payable_amount) AS total_payable,
           SUM(actual_payment_amount) AS total_actual
    FROM payment_order
    WHERE DATE_FORMAT(business_date, '%%Y-%%m') = %s
    GROUP BY order_source, push_status
    ORDER BY order_source, push_status
    """
    with conn.cursor() as cur:
        cur.execute(sql, (month,))
        rows = cur.fetchall()
    conn.close()

    failures = [r for r in rows if r["push_status"] != 1]
    fail_cnt = sum(r["cnt"] for r in failures)
    result = {
        "月份": month,
        "推送失败数": fail_cnt,
        "按来源和状态": rows,
        "失败明细": failures
    }
    return result

def receipt_push(month: str):
    """收款单推送状态"""
    conn = get_conn("fms_bill")
    sql = """
    SELECT order_source, push_status, COUNT(*) AS cnt,
           SUM(receivable_amount) AS total_receivable,
           SUM(actual_receipt_amount) AS total_actual
    FROM receipt_order
    WHERE DATE_FORMAT(business_date, '%%Y-%%m') = %s
    GROUP BY order_source, push_status
    ORDER BY order_source, push_status
    """
    with conn.cursor() as cur:
        cur.execute(sql, (month,))
        rows = cur.fetchall()
    conn.close()

    failures = [r for r in rows if r["push_status"] != 1]
    fail_cnt = sum(r["cnt"] for r in failures)
    result = {
        "月份": month,
        "推送失败数": fail_cnt,
        "按来源和状态": rows,
        "失败明细": failures
    }
    return result

def expense_summary(month: str, cost_code: str = None):
    """费用账单汇总（按科目编码）"""
    conn = get_conn("fms_cost")
    year, mon = month.split("-")
    days_in_month = 31
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            days_in_month = d
            break
        except ValueError:
            continue

    all_rows = []
    for day in range(1, days_in_month + 1):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT cost_code, COUNT(*) AS cnt,
               SUM(income_cost) AS total_income,
               SUM(expend_cost) AS total_expend
        FROM expense_detail
        WHERE trans_dt = %s
        """
        params = [dt]
        if cost_code:
            sql += " AND cost_code = %s"
            params.append(cost_code)
        sql += " GROUP BY cost_code ORDER BY cnt DESC"

        with conn.cursor() as cur:
            cur.execute(sql, params)
            all_rows.extend(cur.fetchall())
    conn.close()

    # Aggregate by cost_code
    agg = {}
    for r in all_rows:
        cc = r["cost_code"] or "(空)"
        if cc not in agg:
            agg[cc] = {"cost_code": cc, "cnt": 0, "total_income": 0, "total_expend": 0}
        agg[cc]["cnt"] += r["cnt"]
        agg[cc]["total_income"] += float(r["total_income"] or 0)
        agg[cc]["total_expend"] += float(r["total_expend"] or 0)

    result_list = sorted(agg.values(), key=lambda x: -x["cnt"])
    total_cnt = sum(x["cnt"] for x in result_list)
    return {"月份": month, "cost_code过滤": cost_code, "总记录数": total_cnt, "科目汇总": result_list}

def duplicate_check(dt: str):
    """重复凭证检查（单日）"""
    conn = get_conn("fms_bill")
    sql = """
    SELECT voucher_no, COUNT(*) AS cnt
    FROM voucher
    WHERE DATE(business_date) = %s
    GROUP BY voucher_no
    HAVING cnt > 1
    ORDER BY cnt DESC
    LIMIT 50
    """
    with conn.cursor() as cur:
        cur.execute(sql, (dt,))
        rows = cur.fetchall()
    conn.close()
    return {"日期": dt, "重复凭证数": len(rows), "明细": rows}

def payment_detail(month: str, order_source: str):
    """付款单明细（按来源，找差异单）"""
    conn = get_conn("fms_bill")
    sql = """
    SELECT id, order_no, business_date, payable_amount, actual_payment_amount,
           (actual_payment_amount - payable_amount) AS diff,
           status, push_status
    FROM payment_order
    WHERE DATE_FORMAT(business_date, '%%Y-%%m') = %s
      AND order_source = %s
      AND ABS(actual_payment_amount - payable_amount) > 0.01
    ORDER BY ABS(actual_payment_amount - payable_amount) DESC
    LIMIT 50
    """
    with conn.cursor() as cur:
        cur.execute(sql, (month, int(order_source)))
        rows = cur.fetchall()
    conn.close()
    return {"月份": month, "来源": order_source, "差异单据数": len(rows), "明细": rows}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    try:
        if cmd == "voucher_status" and len(sys.argv) >= 3:
            print(json.dumps(voucher_status(sys.argv[2]), ensure_ascii=False, indent=2, default=str))
        elif cmd == "payment_push" and len(sys.argv) >= 3:
            print(json.dumps(payment_push(sys.argv[2]), ensure_ascii=False, indent=2, default=str))
        elif cmd == "receipt_push" and len(sys.argv) >= 3:
            print(json.dumps(receipt_push(sys.argv[2]), ensure_ascii=False, indent=2, default=str))
        elif cmd == "expense_summary" and len(sys.argv) >= 3:
            cc = sys.argv[3] if len(sys.argv) >= 4 else None
            print(json.dumps(expense_summary(sys.argv[2], cc), ensure_ascii=False, indent=2, default=str))
        elif cmd == "duplicate_check" and len(sys.argv) >= 3:
            print(json.dumps(duplicate_check(sys.argv[2]), ensure_ascii=False, indent=2, default=str))
        elif cmd == "payment_detail" and len(sys.argv) >= 4:
            print(json.dumps(payment_detail(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2, default=str))
        else:
            print(f"未知命令或参数不足: {cmd}")
            print(__doc__)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)
