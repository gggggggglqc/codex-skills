"""
Sales business log (psi_sales) vs Voucher detail income reconciliation v2
Based on the reconciliation rules:
  Left (psi_sales): income_fee - refund_amount = net_income
  Right (voucher, resource=8, account_set=3): 6001% + 2221.01.01% = book_income
  Verify: net_income - book_income = 0

Usage: python reconcile_sales_income_v2.py <YYYY-MM> [options]
"""
import sys, json, os
from datetime import datetime
from decimal import Decimal
import pymysql
from pathlib import Path



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

def make_db_config(profile_name, database=None, read_timeout=120):
    data = load_db_profile(profile_name)
    return {
        "host": os.environ.get("DB_HOST", data["DB_HOST"]),
        "port": int(os.environ.get("DB_PORT", data["DB_PORT"])),
        "user": os.environ.get("DB_USER", data["DB_USER"]),
        "password": os.environ.get("DB_PASSWORD", data["DB_PASSWORD"]),
        "database": database or os.environ.get("DB_NAME", data.get("DB_NAME", "")),
        "charset": os.environ.get("DB_CHARSET", data.get("DB_CHARSET", "utf8mb4")),
        "cursorclass": pymysql.cursors.DictCursor,
        "connect_timeout": 30,
        "read_timeout": read_timeout,
    }

DORIS_CONFIG = make_db_config(os.environ.get("DORIS_PROFILE", "doris"), database="dp_ods", read_timeout=300)
MYSQL_CONFIG = make_db_config(os.environ.get("MYSQL_PROFILE", "erp-mysql"), database="fms_bill", read_timeout=300)
PSI_VOUCHER_RESOURCE = 8
PSI_ACCOUNT_SET = 3  # group accounting

# 9 business groups from PsiGroupTypeEnum (only these are included in reconciliation)
PSI_GROUP_TYPES = (
    101,  # SALE_PRICE_DIFFERENCES_ORDER  - 差价交易订单
    105,  # SALE_REISSUE_POSTAGE          - 补邮费/差价
    107,  # SALE_GENERAL_TRANSACTION_COMPLETE - 一般交易·完成
    114,  # AFTER_SALE_RETURN_REFUND      - 售后退货退款
    115,  # AFTER_SALE_REFUND             - 售后已收货仅退款
    125,  # AFTER_SALE_NO_RECEIVE_REFUND  - 售后未收货仅退款
    147,  # DISTRIBUTION_SALE             - 分销销售
    148,  # OFFLINE_SALES                 - 线下零售
    165,  # DISTRIBUTO_REFUND_ORDER       - 分销退货
)
PSI_GROUP_TYPE_IN = ", ".join(str(g) for g in PSI_GROUP_TYPES)


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


def fetch_psi_sales(month):
    """Fetch psi_sales data from MySQL fms_cost.psi_sales, filtered by business_date"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    conn.select_db("fms_cost")
    daily = {}
    total_income_fee = Decimal(0)
    total_refund = Decimal(0)
    total_cnt = 0

    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = f"""
        SELECT COUNT(*) AS cnt,
               SUM(income_fee) AS total_income_fee,
               SUM(income_fee_no_tax) AS total_income_fee_no_tax,
               SUM(refund_amount) AS total_refund,
               SUM(pay_amount) AS total_pay,
               SUM(pay_no_tax_amount) AS total_pay_no_tax
        FROM psi_sales
        WHERE business_date = %s
          AND psi_group_type IN ({PSI_GROUP_TYPE_IN})
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt,))
            r = cur.fetchone()
            cnt = r["cnt"] or 0
            inc = Decimal(r["total_income_fee"] or 0)
            inc_no_tax = Decimal(r["total_income_fee_no_tax"] or 0)
            refund = Decimal(r["total_refund"] or 0)
            pay = Decimal(r["total_pay"] or 0)
            pay_no_tax = Decimal(r["total_pay_no_tax"] or 0)

            net_income = inc - refund
            daily[dt] = {
                "cnt": cnt,
                "income_fee": float(inc),
                "income_fee_no_tax": float(inc_no_tax),
                "refund_amount": float(refund),
                "pay_amount": float(pay),
                "net_income": float(net_income),
            }
            total_income_fee += inc
            total_refund += refund
            total_cnt += cnt

    conn.close()
    return {
        "total_income_fee": float(total_income_fee),
        "total_refund": float(total_refund),
        "net_income": float(total_income_fee - total_refund),
        "total_cnt": total_cnt,
        "daily": daily,
    }


def fetch_voucher_income(month):
    """Fetch voucher income from MySQL, filtered by voucher_resource=8 (PSI_SALES_RECORD)"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    daily = {}
    by_subject = {}
    total_income_credit = Decimal(0)
    total_income_debit = Decimal(0)
    total_tax_credit = Decimal(0)
    total_tax_debit = Decimal(0)
    total_cost_debit = Decimal(0)
    total_inventory_credit = Decimal(0)
    total_cnt = 0

    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = """
        SELECT vd.subject_code,
               COUNT(*) AS cnt,
               SUM(vd.credit_amount) AS total_credit,
               SUM(vd.debit_amount) AS total_debit
        FROM voucher_detail vd
        JOIN voucher v ON vd.voucher_id = v.voucher_id
        WHERE v.business_date = %s
          AND v.voucher_resource = %s
          AND v.account_set = %s
        GROUP BY vd.subject_code
        """
        with conn.cursor() as cur:
            cur.execute(sql, (dt, PSI_VOUCHER_RESOURCE, PSI_ACCOUNT_SET))
            day_income_credit = Decimal(0)
            day_income_debit = Decimal(0)
            day_tax_credit = Decimal(0)
            day_tax_debit = Decimal(0)
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

                if sc.startswith("6001"):
                    day_income_credit += credit
                    day_income_debit += debit
                    total_income_credit += credit
                    total_income_debit += debit
                elif sc.startswith("2221.01.01"):
                    day_tax_credit += credit
                    day_tax_debit += debit
                    total_tax_credit += credit
                    total_tax_debit += debit
                elif sc.startswith("6401"):
                    total_cost_debit += debit
                elif sc.startswith("1405"):
                    total_inventory_credit += credit

                day_cnt += cnt

            # book_income = income + tax (both credit side)
            day_book_income = day_income_credit + day_tax_credit
            daily[dt] = {
                "cnt": day_cnt,
                "income_credit": float(day_income_credit),
                "income_debit": float(day_income_debit),
                "tax_credit": float(day_tax_credit),
                "tax_debit": float(day_tax_debit),
                "book_income": float(day_book_income),
            }
            total_cnt += day_cnt

    conn.close()

    subjects_list = []
    for sc, data in sorted(by_subject.items(), key=lambda x: -abs(float(x[1]["credit"]))):
        subjects_list.append({
            "subject_code": sc,
            "cnt": data["cnt"],
            "credit": float(data["credit"]),
            "debit": float(data["debit"]),
        })

    total_book_income = total_income_credit + total_tax_credit
    return {
        "total_income_credit": float(total_income_credit),
        "total_income_debit": float(total_income_debit),
        "total_tax_credit": float(total_tax_credit),
        "total_tax_debit": float(total_tax_debit),
        "total_cost_debit": float(total_cost_debit),
        "total_inventory_credit": float(total_inventory_credit),
        "total_book_income": float(total_book_income),
        "total_cnt": total_cnt,
        "daily": daily,
        "by_subject": subjects_list,
    }


def reconcile(month):
    """Main reconciliation"""
    print(f"Fetching psi_sales for {month}...")
    psi = fetch_psi_sales(month)

    print(f"Fetching voucher (resource={PSI_VOUCHER_RESOURCE}) for {month}...")
    voucher = fetch_voucher_income(month)

    # Monthly summary
    psi_net_income = psi["net_income"]
    voucher_book_income = voucher["total_book_income"]
    diff = psi_net_income - voucher_book_income
    diff_pct = (diff / voucher_book_income * 100) if voucher_book_income != 0 else 0

    result = {
        "month": month,
        "voucher_resource": PSI_VOUCHER_RESOURCE,
        "psi_group_types": list(PSI_GROUP_TYPES),
        "monthly_summary": {
            "psi_sales_income_fee": psi["total_income_fee"],
            "psi_sales_refund": psi["total_refund"],
            "psi_net_income": psi_net_income,
            "psi_cnt": psi["total_cnt"],
            "voucher_income_credit": voucher["total_income_credit"],
            "voucher_income_debit": voucher["total_income_debit"],
            "voucher_tax_credit": voucher["total_tax_credit"],
            "voucher_tax_debit": voucher["total_tax_debit"],
            "voucher_book_income": voucher_book_income,
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
        p = psi["daily"].get(dt, {"net_income": 0, "income_fee": 0, "refund_amount": 0, "cnt": 0})
        v = voucher["daily"].get(dt, {"book_income": 0, "income_credit": 0, "tax_credit": 0, "cnt": 0})
        d_diff = p["net_income"] - v["book_income"]
        d_pct = (d_diff / v["book_income"] * 100) if v["book_income"] != 0 else (0 if p["net_income"] == 0 else 999)

        if abs(d_diff) > abs(max_daily_diff):
            max_daily_diff = d_diff
            max_daily_diff_date = dt

        result["daily_comparison"].append({
            "date": dt,
            "psi_net_income": p["net_income"],
            "psi_income_fee": p["income_fee"],
            "psi_refund": p["refund_amount"],
            "voucher_book_income": v["book_income"],
            "voucher_income_credit": v["income_credit"],
            "voucher_tax_credit": v["tax_credit"],
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
    try:
        result = reconcile(month)
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DecimalEncoder))
    except Exception as e:
        import traceback
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2))
        sys.exit(1)
