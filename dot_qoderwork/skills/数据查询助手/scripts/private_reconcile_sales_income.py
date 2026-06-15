"""
Sales business log (psi_sales) vs Voucher detail income reconciliation
Usage: python reconcile_sales_income.py <YYYY-MM> [subject_prefix]

subject_prefix: optional, default '6001' (main business income)
  6001 = main business income
  6051 = other business income
  6    = all income (6001+6051+6301+6711)
"""
import sys, json
from datetime import datetime
from decimal import Decimal
import pymysql

# --- Database connections ---
DORIS_CONFIG = {
    "host": "cmccnet.jiabs.com",
    "port": 19130,
    "user": "db_devops",
    "password": "mVk3ydQVwN",
    "database": "dp_ods",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 30,
    "read_timeout": 300,
}

MYSQL_CONFIG = {
    "host": "rr-2zeh95evp4y3t94fkmo.mysql.rds.aliyuncs.com",
    "port": 3306,
    "user": "oms_query",
    "password": "%zVtq^h$30fQIDav",
    "database": "fms_bill",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 30,
    "read_timeout": 300,
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def get_days(month):
    """Get list of (year, mon, day) tuples for a given month"""
    year, mon = month.split("-")
    for d in range(31, 0, -1):
        try:
            datetime(int(year), int(mon), d)
            return [(year, mon, day) for day in range(1, d + 1)]
        except ValueError:
            continue
    return []


def fetch_psi_sales(month):
    """Fetch psi_sales income_fee by day from Doris"""
    conn = pymysql.connect(**DORIS_CONFIG)
    daily = {}
    total_income_fee = Decimal(0)
    total_income_fee_no_tax = Decimal(0)
    total_cnt = 0

    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT COUNT(*) AS cnt,
               SUM(income_fee) AS total_income_fee,
               SUM(income_fee_no_tax) AS total_income_fee_no_tax,
               SUM(pay_amount) AS total_pay,
               SUM(refund_amount) AS total_refund
        FROM doris_ods_fms_cost_psi_sales
        WHERE dt = %s
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt,))
            r = cur.fetchone()
            cnt = r["cnt"] or 0
            inc = Decimal(r["total_income_fee"] or 0)
            inc_no_tax = Decimal(r["total_income_fee_no_tax"] or 0)
            pay = Decimal(r["total_pay"] or 0)
            refund = Decimal(r["total_refund"] or 0)

            daily[dt] = {
                "cnt": cnt,
                "income_fee": float(inc),
                "income_fee_no_tax": float(inc_no_tax),
                "pay_amount": float(pay),
                "refund_amount": float(refund),
            }
            total_income_fee += inc
            total_income_fee_no_tax += inc_no_tax
            total_cnt += cnt

    conn.close()
    return {
        "total_income_fee": float(total_income_fee),
        "total_income_fee_no_tax": float(total_income_fee_no_tax),
        "total_cnt": total_cnt,
        "daily": daily,
    }


def fetch_voucher_income(month, subject_prefix="6001"):
    """Fetch voucher income detail from MySQL, day by day"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    daily = {}
    by_subject = {}
    total_credit = Decimal(0)
    total_cnt = 0

    # Build subject filter
    if subject_prefix == "6":
        subj_filter = "AND (vd.subject_code LIKE '6001%%' OR vd.subject_code LIKE '6051%%' OR vd.subject_code LIKE '6301%%')"
    else:
        subj_filter = f"AND vd.subject_code LIKE '{subject_prefix}%%'"

    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = f"""
        SELECT vd.subject_code,
               COUNT(*) AS cnt,
               SUM(vd.credit_amount) AS total_credit,
               SUM(vd.debit_amount) AS total_debit,
               SUM(vd.credit_standard_currency_amount) AS total_credit_std,
               SUM(vd.debit_standard_currency_amount) AS total_debit_std
        FROM voucher_detail vd
        JOIN voucher v ON vd.voucher_id = v.voucher_id
        WHERE v.business_date = %s
          {subj_filter}
        GROUP BY vd.subject_code
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt,))
            day_credit = Decimal(0)
            day_cnt = 0
            for r in cur.fetchall():
                sc = r["subject_code"]
                cnt = r["cnt"]
                credit = Decimal(r["total_credit"] or 0)
                debit = Decimal(r["total_debit"] or 0)

                if sc not in by_subject:
                    by_subject[sc] = {"cnt": 0, "credit": Decimal(0), "debit": Decimal(0)}
                by_subject[sc]["cnt"] += cnt
                by_subject[sc]["credit"] += credit
                by_subject[sc]["debit"] += debit

                day_credit += credit
                day_cnt += cnt

            daily[dt] = {
                "cnt": day_cnt,
                "credit": float(day_credit),
                "abs_credit": float(abs(day_credit)),
            }
            total_credit += day_credit
            total_cnt += day_cnt

    conn.close()

    # Convert by_subject to serializable
    subjects_list = []
    for sc, data in sorted(by_subject.items(), key=lambda x: -abs(float(x[1]["credit"]))):
        subjects_list.append({
            "subject_code": sc,
            "cnt": data["cnt"],
            "credit": float(data["credit"]),
            "debit": float(data["debit"]),
            "abs_credit": float(abs(data["credit"])),
        })

    return {
        "total_credit": float(total_credit),
        "abs_total_credit": float(abs(total_credit)),
        "total_cnt": total_cnt,
        "daily": daily,
        "by_subject": subjects_list,
    }


def reconcile(month, subject_prefix="6001"):
    """Main reconciliation: psi_sales income_fee vs voucher credit_amount"""
    print(f"Fetching psi_sales data for {month}...")
    psi = fetch_psi_sales(month)

    print(f"Fetching voucher income data for {month} (subject prefix: {subject_prefix})...")
    voucher = fetch_voucher_income(month, subject_prefix)

    # Monthly comparison
    psi_income = psi["total_income_fee"]
    voucher_credit_abs = voucher["abs_total_credit"]
    diff = psi_income - voucher_credit_abs
    diff_pct = (diff / voucher_credit_abs * 100) if voucher_credit_abs != 0 else 0

    result = {
        "month": month,
        "subject_prefix": subject_prefix,
        "monthly_summary": {
            "psi_sales_income_fee": psi_income,
            "psi_sales_cnt": psi["total_cnt"],
            "voucher_abs_credit": voucher_credit_abs,
            "voucher_cnt": voucher["total_cnt"],
            "diff": round(diff, 2),
            "diff_pct": round(diff_pct, 2),
            "status": "MATCH" if abs(diff_pct) < 0.1 else ("WARN" if abs(diff_pct) < 1 else "MISMATCH"),
        },
        "by_subject": voucher["by_subject"],
        "daily_comparison": [],
    }

    # Daily comparison
    all_dates = sorted(set(list(psi["daily"].keys()) + list(voucher["daily"].keys())))
    max_daily_diff = 0
    max_daily_diff_date = ""
    for dt in all_dates:
        p = psi["daily"].get(dt, {"income_fee": 0, "cnt": 0})
        v = voucher["daily"].get(dt, {"abs_credit": 0, "cnt": 0, "credit": 0})
        d_diff = p["income_fee"] - v["abs_credit"]
        d_pct = (d_diff / v["abs_credit"] * 100) if v["abs_credit"] != 0 else 0

        if abs(d_diff) > abs(max_daily_diff):
            max_daily_diff = d_diff
            max_daily_diff_date = dt

        result["daily_comparison"].append({
            "date": dt,
            "psi_income_fee": p["income_fee"],
            "voucher_abs_credit": v["abs_credit"],
            "diff": round(d_diff, 2),
            "diff_pct": round(d_pct, 2),
        })

    result["max_daily_diff"] = {
        "date": max_daily_diff_date,
        "diff": round(max_daily_diff, 2),
    }

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    month = sys.argv[1]
    subj = sys.argv[2] if len(sys.argv) >= 3 else "6001"

    try:
        result = reconcile(month, subj)
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DecimalEncoder))
    except Exception as e:
        import traceback
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2))
        sys.exit(1)
