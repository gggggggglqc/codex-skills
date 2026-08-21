#!/usr/bin/env python3
"""Read-only daily reconciliation: delivery V1 aggregates versus net-profit V2 EP rows."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

import pymysql

ABSOLUTE_TOLERANCE = Decimal("0.01")
RELATIVE_TOLERANCE = Decimal("0.0001")


def is_within_tolerance(difference, expected_amount):
    """Allow either one cent or 0.01% of the expected amount."""
    return abs(difference) <= max(ABSOLUTE_TOLERANCE, abs(expected_amount) * RELATIVE_TOLERANCE)


def build_rules():
    return [
        {"rule_id": "REC-REV-001", "v1_field": "sales_amount", "v1_sql_expression": "CASE WHEN sales_model = '3' THEN estimate_brand_quotation ELSE sales_amount END", "expense_code": "EP001", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6},
        {"rule_id": "REC-REV-002", "v1_field": "no_tax_payment", "expense_code": "EP028", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6},
        {"rule_id": "REC-COST-001", "v1_field": "no_tax_product_cost", "expense_code": "EP003", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6},
        {"rule_id": "REC-TAX-001", "v1_field": "output_tax_amount", "expense_code": "EP029", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6},
        {"rule_id": "REC-TAX-003", "v1_field": "input_tax_amount", "expense_code": "EP030", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6},
        {"rule_id": "REC-TAX-002", "v1_field": "input_tax_amount_rebate", "expense_code": "EP039", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6, "v2_sign": -1},
        {"rule_id": "REC-COST-002", "v1_field": "rebate_amount", "expense_code": "EP038", "country_type": 1, "v1_cbs_platform": 0, "v1_exclude_business_group": 6, "v2_sign": -1},
    ]


def load_profile(name):
    path = Path.home() / ".config" / "db-profiles" / f"{name}.env"
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def connect(profile):
    config = load_profile(profile)
    return pymysql.connect(
        host=config["DB_HOST"],
        port=int(config["DB_PORT"]),
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database="dp_dws",
        charset=config.get("DB_CHARSET", "utf8mb4"),
        connect_timeout=10,
        read_timeout=120,
        cursorclass=pymysql.cursors.DictCursor,
    )


def scalar(cursor, sql, params):
    cursor.execute(sql, params)
    return Decimal(cursor.fetchone()["amount"] or 0)


def reconcile_day(conn, dt):
    results = []
    with conn.cursor() as cursor:
        for rule in build_rules():
            v1_amount = scalar(
                cursor,
                f"SELECT SUM({rule.get('v1_sql_expression', '`' + rule['v1_field'] + '`')}) AS amount "
                "FROM `doris_app_report_delivery_v1` "
                "WHERE dt = %s AND cbs_platform = %s "
                "AND COALESCE(business_group, -1) <> %s",
                (dt, rule["v1_cbs_platform"], rule["v1_exclude_business_group"]),
            )
            v2_sql = (
                "SELECT SUM(expense_amount) AS amount "
                "FROM `doris_app_net_profit_check_report_v2` "
                "WHERE dt = %s AND flag = 1 AND expense_code = %s"
            )
            params = [dt, rule["expense_code"]]
            if rule["country_type"] is not None:
                v2_sql += " AND country_type = %s"
                params.append(rule["country_type"])
            v2_amount = scalar(cursor, v2_sql, params)
            expected_v2_amount = v1_amount * Decimal(str(rule.get("v2_sign", 1)))
            difference = expected_v2_amount - v2_amount
            results.append(
                {
                    **rule,
                    "v1_amount": str(v1_amount),
                    "expected_v2_amount": str(expected_v2_amount),
                    "v2_amount": str(v2_amount),
                    "difference": str(difference),
                    "status": "pass" if is_within_tolerance(difference, expected_v2_amount) else "failed",
                }
            )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="business date in YYYY-MM-DD")
    parser.add_argument("--profile", default="doris")
    args = parser.parse_args()
    conn = connect(args.profile)
    try:
        rules = reconcile_day(conn, args.date)
    finally:
        conn.close()
    print(json.dumps({"date": args.date, "read_only": True, "rules": rules}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
