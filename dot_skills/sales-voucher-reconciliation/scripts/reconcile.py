"""
Sales business log (psi_sales) vs Voucher detail income reconciliation
=====================================================================
Left  (psi_sales):   income_fee - refund_amount = net_income
Right (voucher):     6001% credit + 2221.01.01% credit = book_income
Verify: net_income - book_income ≈ 0

Usage:
    python reconcile.py <YYYY-MM> [--shop SHOP_CODE]

Examples:
    python reconcile.py 2026-04
    python reconcile.py 2026-04 --shop SH028
"""
import sys, json, os, argparse
from datetime import datetime
from decimal import Decimal
import pymysql
from pathlib import Path


# ---------------------------------------------------------------------------
# Database profile loader
# ---------------------------------------------------------------------------
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


def make_mysql_conn(database=None, read_timeout=300):
    profile = os.environ.get("MYSQL_PROFILE", "erp-mysql")
    cfg = load_db_profile(profile)
    return pymysql.connect(
        host=os.environ.get("DB_HOST", cfg["DB_HOST"]),
        port=int(os.environ.get("DB_PORT", cfg["DB_PORT"])),
        user=os.environ.get("DB_USER", cfg["DB_USER"]),
        password=os.environ.get("DB_PASSWORD", cfg["DB_PASSWORD"]),
        database=database or cfg.get("DB_NAME", ""),
        charset=os.environ.get("DB_CHARSET", cfg.get("DB_CHARSET", "utf8mb4")),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
        read_timeout=read_timeout,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PSI_VOUCHER_RESOURCE = 8   # PSI_SALES_RECORD
PSI_ACCOUNT_SET = 3        # group accounting

PSI_GROUP_TYPES = (
    101,  # 差价交易订单
    105,  # 补邮费/差价
    107,  # 一般交易·完成
    114,  # 售后退货退款
    115,  # 售后已收货仅退款
    125,  # 售后未收货仅退款
    147,  # 分销销售
    148,  # 线下零售
    165,  # 分销退货
)
PSI_GROUP_TYPE_IN = ", ".join(str(g) for g in PSI_GROUP_TYPES)

GROUP_NAMES = {
    101: "差价交易订单",
    105: "补邮费/差价",
    107: "一般交易·完成",
    114: "售后退货退款",
    115: "售后已收货仅退款",
    125: "售后未收货仅退款",
    147: "分销销售",
    148: "线下零售",
    165: "分销退货",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Fetch psi_sales
# ---------------------------------------------------------------------------
def fetch_psi_sales(month, shop_code=None):
    conn = make_mysql_conn(database="fms_cost")
    daily = {}
    by_group = {}
    total_income_fee = Decimal(0)
    total_refund = Decimal(0)
    total_cnt = 0

    shop_filter = ""
    params_extra = []
    if shop_code:
        shop_filter = "AND shop_code = %s"
        params_extra = [shop_code]

    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql = f"""
        SELECT COUNT(*) AS cnt,
               SUM(income_fee) AS total_income_fee,
               SUM(refund_amount) AS total_refund
        FROM psi_sales
        WHERE business_date = %s
          AND psi_group_type IN ({PSI_GROUP_TYPE_IN})
          {shop_filter}
        """
        with conn.cursor() as cur:
            cur.execute(sql, [dt] + params_extra)
            r = cur.fetchone()
            cnt = r["cnt"] or 0
            inc = Decimal(r["total_income_fee"] or 0)
            refund = Decimal(r["total_refund"] or 0)
            net_income = inc - refund
            daily[dt] = {
                "cnt": cnt,
                "income_fee": float(inc),
                "refund_amount": float(refund),
                "net_income": float(net_income),
            }
            total_income_fee += inc
            total_refund += refund
            total_cnt += cnt

    # Group breakdown — aggregate day-by-day to avoid full-month GROUP BY timeout
    for year, mon, day in get_days(month):
        dt = f"{year}-{mon}-{day:02d}"
        sql_group = f"""
        SELECT psi_group_type,
               COUNT(*) AS cnt,
               SUM(income_fee) AS total_income_fee,
               SUM(refund_amount) AS total_refund
        FROM psi_sales
        WHERE business_date = %s
          AND psi_group_type IN ({PSI_GROUP_TYPE_IN})
          {shop_filter}
        GROUP BY psi_group_type
        """
        with conn.cursor() as cur:
            cur.execute(sql_group, [dt] + params_extra)
            for r in cur.fetchall():
                gt = r["psi_group_type"]
                gt_key = str(gt)
                if gt_key not in by_group:
                    by_group[gt_key] = {
                        "name": GROUP_NAMES.get(gt, "?"),
                        "cnt": 0,
                        "income_fee": Decimal(0),
                        "refund_amount": Decimal(0),
                        "net_income": Decimal(0),
                    }
                inc = Decimal(r["total_income_fee"] or 0)
                refund = Decimal(r["total_refund"] or 0)
                by_group[gt_key]["cnt"] += r["cnt"]
                by_group[gt_key]["income_fee"] += inc
                by_group[gt_key]["refund_amount"] += refund
                by_group[gt_key]["net_income"] += inc - refund

    # Convert Decimal to float for JSON serialization
    for gt_key in by_group:
        for k in ("income_fee", "refund_amount", "net_income"):
            by_group[gt_key][k] = float(by_group[gt_key][k])

    conn.close()
    return {
        "total_income_fee": float(total_income_fee),
        "total_refund": float(total_refund),
        "net_income": float(total_income_fee - total_refund),
        "total_cnt": total_cnt,
        "daily": daily,
        "by_group": by_group,
    }


# ---------------------------------------------------------------------------
# Fetch voucher income
# ---------------------------------------------------------------------------
def fetch_voucher_income(month, shop_code=None):
    conn = make_mysql_conn(database="fms_bill")
    daily = {}
    by_subject = {}
    total_income_credit = Decimal(0)
    total_income_debit = Decimal(0)
    total_tax_credit = Decimal(0)
    total_tax_debit = Decimal(0)
    total_cnt = 0

    # Note: voucher_detail doesn't have shop_code directly;
    # shop filtering for voucher side is not straightforward.
    # We fetch all vouchers for the month and note this limitation.

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

                day_cnt += cnt

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
        "total_book_income": float(total_book_income),
        "total_cnt": total_cnt,
        "daily": daily,
        "by_subject": subjects_list,
    }


# ---------------------------------------------------------------------------
# Main reconciliation
# ---------------------------------------------------------------------------
def reconcile(month, shop_code=None):
    label = f"{month}"
    if shop_code:
        label += f" (shop={shop_code})"

    print(f"Fetching psi_sales for {label}...", file=sys.stderr)
    psi = fetch_psi_sales(month, shop_code=shop_code)

    print(f"Fetching voucher (resource={PSI_VOUCHER_RESOURCE}) for {month}...", file=sys.stderr)
    if shop_code:
        print(f"Note: voucher side does not filter by shop_code; showing all shops.", file=sys.stderr)
    voucher = fetch_voucher_income(month, shop_code=shop_code)

    # Monthly summary
    psi_net_income = psi["net_income"]
    voucher_book_income = voucher["total_book_income"]
    diff = psi_net_income - voucher_book_income
    diff_pct = (diff / voucher_book_income * 100) if voucher_book_income != 0 else 0

    result = {
        "month": month,
        "shop_code": shop_code,
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
        "psi_by_group": psi["by_group"],
        "by_subject": voucher["by_subject"],
        "daily_comparison": [],
    }

    # Daily comparison
    all_dates = sorted(set(list(psi["daily"].keys()) + list(voucher["daily"].keys())))
    max_daily_diff = 0
    max_daily_diff_date = ""
    no_voucher_days = []

    for dt in all_dates:
        p = psi["daily"].get(dt, {"net_income": 0, "income_fee": 0, "refund_amount": 0, "cnt": 0})
        v = voucher["daily"].get(dt, {"book_income": 0, "income_credit": 0, "tax_credit": 0, "cnt": 0})
        d_diff = p["net_income"] - v["book_income"]
        d_pct = (d_diff / v["book_income"] * 100) if v["book_income"] != 0 else (0 if p["net_income"] == 0 else 999)

        if abs(d_diff) > abs(max_daily_diff):
            max_daily_diff = d_diff
            max_daily_diff_date = dt

        if v["cnt"] == 0 and p["cnt"] > 0:
            no_voucher_days.append(dt)

        result["daily_comparison"].append({
            "date": dt,
            "psi_net_income": p["net_income"],
            "psi_income_fee": p["income_fee"],
            "psi_refund": p["refund_amount"],
            "psi_cnt": p["cnt"],
            "voucher_book_income": v["book_income"],
            "voucher_income_credit": v["income_credit"],
            "voucher_tax_credit": v["tax_credit"],
            "voucher_cnt": v["cnt"],
            "diff": round(d_diff, 2),
            "diff_pct": round(d_pct, 2),
        })

    result["max_daily_diff"] = {
        "date": max_daily_diff_date,
        "diff": round(max_daily_diff, 2),
    }
    result["no_voucher_days"] = no_voucher_days
    result["no_voucher_days_count"] = len(no_voucher_days)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sales vs Voucher reconciliation")
    parser.add_argument("month", help="Month in YYYY-MM format")
    parser.add_argument("--shop", default=None, help="Filter by shop_code (e.g. SH028)")
    args = parser.parse_args()

    try:
        result = reconcile(args.month, shop_code=args.shop)
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DecimalEncoder))
    except Exception as e:
        import traceback
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}, ensure_ascii=False, indent=2))
        sys.exit(1)
