#!/usr/bin/env python3
"""Reconcile T+1 subject costs across FMS, warehouse middle tables, and downstream allocation."""

import argparse
import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, getcontext
from pathlib import Path
import sys

import pymysql

getcontext().prec = 28


def load_profile(profile):
    path = Path.home() / ".config" / "db-profiles" / f"{profile}.env"
    data = {}
    for line in path.read_text().splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"').strip("'")
    return data


def connect(profile, database=None):
    cfg = load_profile(profile)
    return pymysql.connect(
        host=cfg["DB_HOST"],
        port=int(cfg["DB_PORT"]),
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=database or cfg.get("DB_NAME"),
        charset=cfg.get("DB_CHARSET", "utf8mb4"),
        cursorclass=pymysql.cursors.DictCursor,
        read_timeout=300,
        write_timeout=300,
    )


def decimal_value(value):
    return Decimal(str(value or 0))


def month_range(month):
    year, month_num = [int(part) for part in month.split("-", 1)]
    start = date(year, month_num, 1)
    _, days = calendar.monthrange(year, month_num)
    end = start + timedelta(days=days)
    return start, end


def table_exists(connection, table_schema, table_name):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            LIMIT 1
            """,
            (table_schema, table_name),
        )
        return cur.fetchone() is not None


def iter_days(start, end):
    current = start
    while current < end:
        yield current, current + timedelta(days=1)
        current += timedelta(days=1)


def chunks(values, size):
    values = list(values)
    for idx in range(0, len(values), size):
        yield values[idx : idx + size]


def get_rate(rate_rows, biz_date, currency_code):
    currency_code = currency_code or "CNY"
    if currency_code == "CNY":
        return Decimal("1")
    for row in rate_rows:
        start = str(row["effective_date"].date())
        end = str(row["expiring_date"].date())
        if row["source_currency_code"] == currency_code and start <= biz_date <= end:
            return decimal_value(row["direct_exchange_rate"])
    raise RuntimeError(f"Missing FMS exchange rate for {biz_date} {currency_code}->CNY")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", required=True, help="Business month, e.g. 2026-05")
    parser.add_argument("--department-id", help="Optional department/structure id, e.g. 507. Omit to reconcile all departments.")
    parser.add_argument("--subject", action="append", required=True, help="Subject code; repeat for multiple subjects")
    parser.add_argument("--shop-chunk-size", type=int, default=40)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def fetch_metadata(mysql, subjects, department_id, start_s, end_s):
    with mysql.cursor() as cur:
        shops = None
        if department_id:
            cur.execute(
                "SELECT shop_code, name FROM oms_business.shop WHERE structure_id = %s",
                (department_id,),
            )
            shops = {row["shop_code"]: row["name"] for row in cur.fetchall()}
            if not shops:
                raise RuntimeError(f"No shops found for department/structure id {department_id}")

        placeholders = ",".join(["%s"] * len(subjects))
        cur.execute(
            f"""
            SELECT cgs.subject_code, cgs.cost_code, ci.cost_name, cgs.is_gather
            FROM fms_support.cost_gather_strategy cgs
            LEFT JOIN fms_cost.cost_item ci ON ci.cost_code = cgs.cost_code
            WHERE cgs.subject_code IN ({placeholders})
            """,
            subjects,
        )
        mapping_rows = cur.fetchall()
        active = [row for row in mapping_rows if str(row.get("is_gather", "1")) != "0"]
        mapping_source = active or mapping_rows
        code_to_subject = {row["cost_code"]: row["subject_code"] for row in mapping_source}
        subject_costs = defaultdict(list)
        for row in mapping_source:
            subject_costs[row["subject_code"]].append(row["cost_code"])

        cur.execute(
            """
            SELECT source_currency_code, target_currency_code, direct_exchange_rate, effective_date, expiring_date
            FROM fms_support.exchange_rate_system
            WHERE target_currency_code = 'CNY'
              AND effective_date < %s
              AND expiring_date >= %s
            """,
            (end_s, start_s),
        )
        rates = cur.fetchall()

        subject_names = {subject: "" for subject in subjects}

    return shops, code_to_subject, subject_costs, rates, subject_names


def add_expense_rows(rows, target, label, currency_detail, detail_label, code_to_subject, rates):
    for row in rows:
        subject = code_to_subject[row["cost_code"]]
        biz_date = str(row["trans_dt"])
        currency = row["currency_code"] or "CNY"
        original_amount = decimal_value(row["amount"])
        converted = original_amount * get_rate(rates, biz_date, currency)
        target[(subject, label)] += converted
        currency_detail[(subject, detail_label, currency)] += original_amount


def query_fms_expenses(mysql, start, end, shops, cost_codes, code_to_subject, rates, chunk_size, verbose):
    result = defaultdict(Decimal)
    currency_detail = defaultdict(Decimal)
    shop_chunks = list(chunks(shops.keys(), chunk_size)) if shops is not None else [None]
    ed_codes = cost_codes
    if not ed_codes:
        return result, currency_detail
    expense_tables = [("fms_cost.expense_detail", "expense_detail", "FMS expense original")]
    history_table = f"his_expense_detail_{start.year}"
    if table_exists(mysql, "fms_cost", history_table):
        expense_tables.append((f"fms_cost.{history_table}", "expense_detail", "FMS expense original"))
    expense_tables.append(("fms_cost.expense_detail_cb", "expense_detail_cb_cny", "FMS CB original"))
    with mysql.cursor() as cur:
        for day_start, day_end in iter_days(start, end):
            day_start_s = str(day_start)
            day_end_s = str(day_end)
            for table_name, label, detail_label in expense_tables:
                for shop_chunk in shop_chunks:
                    shop_filter = ""
                    shop_params = []
                    if shop_chunk is not None:
                        shop_placeholders = ",".join(["%s"] * len(shop_chunk))
                        shop_filter = f"AND shop_code IN ({shop_placeholders})"
                        shop_params = list(shop_chunk)
                    code_placeholders = ",".join(["%s"] * len(ed_codes))
                    cur.execute(
                        f"""
                        SELECT trans_dt, cost_code, COALESCE(currency_code, 'CNY') AS currency_code,
                               SUM(income_cost - expend_cost) AS amount
                        FROM {table_name}
                        WHERE trans_dt >= %s AND trans_dt < %s
                          AND is_deleted = 0
                          {shop_filter}
                          AND cost_code IN ({code_placeholders})
                        GROUP BY trans_dt, cost_code, COALESCE(currency_code, 'CNY')
                        """,
                        [day_start_s, day_end_s] + shop_params + ed_codes,
                    )
                    add_expense_rows(cur.fetchall(), result, label, currency_detail, detail_label, code_to_subject, rates)
            if verbose and day_start.day in (1, 10, 20, 31):
                print(f"FMS day done {day_start_s}", file=sys.stderr, flush=True)
    return result, currency_detail


def query_mid_expenses(doris, start, end, shops, cost_codes, code_to_subject, rates, chunk_size, verbose):
    result = defaultdict(Decimal)
    currency_detail = defaultdict(Decimal)
    shop_chunks = list(chunks(shops.keys(), chunk_size)) if shops is not None else [None]
    if not cost_codes:
        return result, currency_detail
    with doris.cursor() as cur:
        for day_start, day_end in iter_days(start, end):
            day_start_s = str(day_start)
            day_end_s = str(day_end)
            for table_name, label, detail_label in [
                ("dp_ods.doris_ods_upload_expense_detail", "ods_expense_detail", "ODS expense original"),
                ("dp_ods.doris_ods_fms_cost_expense_detail_cb", "ods_expense_detail_cb_cny", "ODS CB original"),
            ]:
                for shop_chunk in shop_chunks:
                    shop_filter = ""
                    shop_params = []
                    if shop_chunk is not None:
                        shop_placeholders = ",".join(["%s"] * len(shop_chunk))
                        shop_filter = f"AND shop_code IN ({shop_placeholders})"
                        shop_params = list(shop_chunk)
                    code_placeholders = ",".join(["%s"] * len(cost_codes))
                    cur.execute(
                        f"""
                        SELECT trans_dt, cost_code, COALESCE(currency_code, 'CNY') AS currency_code,
                               SUM(income_cost - expend_cost) AS amount
                        FROM {table_name}
                        WHERE trans_dt >= %s AND trans_dt < %s
                          AND is_deleted = 0
                          {shop_filter}
                          AND cost_code IN ({code_placeholders})
                        GROUP BY trans_dt, cost_code, COALESCE(currency_code, 'CNY')
                        """,
                        [day_start_s, day_end_s] + shop_params + cost_codes,
                    )
                    add_expense_rows(cur.fetchall(), result, label, currency_detail, detail_label, code_to_subject, rates)
            if verbose and day_start.day in (1, 10, 20, 31):
                print(f"Doris day done {day_start_s}", file=sys.stderr, flush=True)
    return result, currency_detail


def main():
    args = parse_args()
    start, end = month_range(args.month)
    start_s = str(start)
    end_s = str(end)
    subjects = args.subject

    mysql = connect("erp-mysql", "fms_bill")
    try:
        shops, code_to_subject, subject_costs, rates, subject_names = fetch_metadata(
            mysql, subjects, args.department_id, start_s, end_s
        )
        all_cost_codes = sorted(code_to_subject)
        fms_expenses, fms_currency = query_fms_expenses(
            mysql, start, end, shops, all_cost_codes, code_to_subject, rates, args.shop_chunk_size, args.verbose
        )
        fms_vouchers = defaultdict(Decimal)
        with mysql.cursor() as cur:
            placeholders = ",".join(["%s"] * len(subjects))
            dept_filter = ""
            dept_params = []
            if args.department_id:
                dept_filter = "AND FIND_IN_SET(%s, vd.accounting_dimension) > 0"
                dept_params = [f"2_&_{args.department_id}"]
            cur.execute(
                f"""
                SELECT vd.subject_code,
                       SUM(vd.debit_standard_currency_amount - vd.credit_standard_currency_amount) AS amount
                FROM fms_bill.voucher_detail vd
                JOIN fms_bill.voucher v ON vd.voucher_id = v.voucher_id
                WHERE v.business_date >= %s AND v.business_date < %s
                  AND v.account_set = 4
                  AND vd.subject_code IN ({placeholders})
                  {dept_filter}
                GROUP BY vd.subject_code
                """,
                [start_s, end_s] + subjects + dept_params,
            )
            for row in cur.fetchall():
                fms_vouchers[row["subject_code"]] += -decimal_value(row["amount"])
    finally:
        mysql.close()

    doris = connect("doris", "dp_dws")
    try:
        mid_expenses, mid_currency = query_mid_expenses(
            doris, start, end, shops, all_cost_codes, code_to_subject, rates, args.shop_chunk_size, args.verbose
        )
        mid_vouchers = defaultdict(Decimal)
        down_success = defaultdict(Decimal)
        down_failure = defaultdict(Decimal)
        with doris.cursor() as cur:
            placeholders = ",".join(["%s"] * len(subjects))
            dept_filter = ""
            dept_params = []
            if args.department_id:
                dept_filter = "AND department_code = %s"
                dept_params = [args.department_id]
            cur.execute(
                f"""
                SELECT subject_code, SUM(result_amount) AS amount
                FROM dp_dws.doris_dws_voucher_subject_mid
                WHERE business_date >= %s AND business_date < %s
                  {dept_filter}
                  AND subject_code IN ({placeholders})
                GROUP BY subject_code
                """,
                [start_s, end_s] + dept_params + subjects,
            )
            for row in cur.fetchall():
                mid_vouchers[row["subject_code"]] += -decimal_value(row["amount"])

            dept_filter = ""
            dept_params = []
            if args.department_id:
                dept_filter = "AND department_id = %s"
                dept_params = [args.department_id]
            cur.execute(
                f"""
                SELECT subject_code, SUM(share) AS amount
                FROM dp_dws.doris_dws_finance_cost_sbjct
                WHERE dt >= %s AND dt < %s
                  {dept_filter}
                  AND subject_code IN ({placeholders})
                GROUP BY subject_code
                """,
                [start_s, end_s] + dept_params + subjects,
            )
            for row in cur.fetchall():
                down_success[row["subject_code"]] += decimal_value(row["amount"])

            cur.execute(
                f"""
                SELECT subject_code, SUM(result_amount) AS amount
                FROM dp_dws.doris_dws_finance_cost_sbjct_failure
                WHERE dt >= %s AND dt < %s
                  {dept_filter}
                  AND subject_code IN ({placeholders})
                GROUP BY subject_code
                """,
                [start_s, end_s] + dept_params + subjects,
            )
            for row in cur.fetchall():
                down_failure[row["subject_code"]] += decimal_value(row["amount"])
    finally:
        doris.close()

    print(f"RECON_MONTH|{args.month}|DEPARTMENT_ID|{args.department_id or 'ALL'}")
    print(
        "SUBJECT|SUBJECT_NAME|COST_CODES|FMS_EXPENSE|FMS_CB_CNY|FMS_VOUCHER|FMS_TOTAL|"
        "MID_EXPENSE|MID_CB_CNY|MID_VOUCHER|MID_TOTAL|DOWN_SUCCESS|DOWN_FAILURE|"
        "DOWN_TOTAL|FMS_MINUS_MID|MID_MINUS_DOWN"
    )
    for subject in subjects:
        fms_expense = fms_expenses[(subject, "expense_detail")]
        fms_cb = fms_expenses[(subject, "expense_detail_cb_cny")]
        fms_voucher = fms_vouchers[subject]
        fms_total = fms_expense + fms_cb + fms_voucher
        mid_expense = mid_expenses[(subject, "ods_expense_detail")]
        mid_cb = mid_expenses[(subject, "ods_expense_detail_cb_cny")]
        mid_voucher = mid_vouchers[subject]
        mid_total = mid_expense + mid_cb + mid_voucher
        downstream_total = down_success[subject] + down_failure[subject]
        print(
            "|".join(
                [
                    subject,
                    subject_names.get(subject, ""),
                    ",".join(subject_costs.get(subject, [])),
                    str(fms_expense),
                    str(fms_cb),
                    str(fms_voucher),
                    str(fms_total),
                    str(mid_expense),
                    str(mid_cb),
                    str(mid_voucher),
                    str(mid_total),
                    str(down_success[subject]),
                    str(down_failure[subject]),
                    str(downstream_total),
                    str(fms_total - mid_total),
                    str(mid_total - downstream_total),
                ]
            )
        )

    print("CURRENCY_DETAIL")
    for detail in (fms_currency, mid_currency):
        for key in sorted(detail):
            if detail[key] != 0:
                print("|".join([key[0], key[1], key[2], str(detail[key])]))


if __name__ == "__main__":
    main()
