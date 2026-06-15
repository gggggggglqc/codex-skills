#!/usr/bin/env python3
"""Check rule 6 from MySQL.

Rule:
actual cost restoration actual outsourcing total cost
= finance outsourcing processing detail

actual cost restoration side:
  outside_cost from erp_cost.produce_cost_detail
  only keep root rows to avoid repeated roll-up expansion
  filtered by calc_month and status = 20

finance side:
  outsourcing_not_tax_freight_cost from erp_cost.outsourcing_order_detail
  joined to erp_cost.outsourcing_order by outsourcing_order_id
  filtered by order_billing_time
"""

from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pymysql") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check rule 6 in MySQL")
    parser.add_argument("--start-date", default="2026-03-01")
    parser.add_argument("--end-date", default="2026-03-31")
    parser.add_argument("--calc-month", default="2026-03-01")
    parser.add_argument(
        "--env-file",
        default="D:/codex/codex-file-organizer/.env",
        help="Path to .env file",
    )
    parser.add_argument(
        "--cost-table",
        default="erp_cost.produce_cost_detail",
    )
    parser.add_argument(
        "--finance-detail-table",
        default="erp_cost.outsourcing_order_detail",
    )
    parser.add_argument(
        "--finance-header-table",
        default="erp_cost.outsourcing_order",
    )
    parser.add_argument(
        "--cost-field",
        default="outside_cost",
        choices=["outside_cost", "reduce_outside_cost", "total_outside_cost"],
        help="Actual cost restoration field used on produce_cost_detail.",
    )
    parser.add_argument(
        "--cost-parent-id",
        default="root",
        help="Only use produce_cost_detail rows with this parent_id.",
    )
    parser.add_argument(
        "--finance-field",
        default="outsourcing_not_tax_freight_cost",
        choices=[
            "outsourcing_not_tax_freight_cost",
            "outsourcing_tax_freight_cost",
        ],
        help="Finance outsourcing amount field.",
    )
    parser.add_argument(
        "--finance-time-field",
        default="order_billing_time",
        choices=["order_create_time", "order_finish_time", "order_billing_time"],
        help="Header time field used for finance month filtering.",
    )
    parser.add_argument(
        "--finance-order-type",
        type=int,
        default=2,
        help="Only use finance outsourcing orders with this outsourcing_order_type.",
    )
    parser.add_argument(
        "--output",
        default="D:/codex/工厂账务核对/fms-reconciliation/output/rule6_2026_03.csv",
        help="Output CSV path",
    )
    return parser.parse_args()


def load_dotenv(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def connect():
    host = env_required("DB_HOST")
    port = int(os.getenv("DB_PORT", "3306"))
    user = env_required("DB_USER")
    password = env_required("DB_PASSWORD")
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4",
        cursorclass=DictCursor,
        read_timeout=600,
        write_timeout=600,
    )


def to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def fetch_cost_amount_map(
    conn,
    cost_table: str,
    cost_field: str,
    cost_parent_id: str,
    calc_month: str,
) -> Dict[str, Decimal]:
    sql = (
        "SELECT material_code, "
        f"SUM(COALESCE({cost_field}, 0)) AS amount "
        f"FROM {cost_table} "
        "WHERE calc_month = %s "
        "AND status = 20 "
        "AND parent_id = %s "
        "GROUP BY material_code"
    )
    result: Dict[str, Decimal] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [calc_month, cost_parent_id])
        for row in cursor.fetchall():
            result[str(row["material_code"])] = to_decimal(row["amount"])
    return result


def fetch_finance_amount_map(
    conn,
    finance_detail_table: str,
    finance_header_table: str,
    finance_field: str,
    finance_time_field: str,
    finance_order_type: int,
    start_date: str,
    end_date: str,
) -> Dict[str, Decimal]:
    sql = (
        "SELECT d.material_code, "
        f"SUM(COALESCE(d.{finance_field}, 0)) AS amount "
        f"FROM {finance_detail_table} d "
        f"JOIN {finance_header_table} h "
        "ON h.outsourcing_order_id = d.outsourcing_order_id "
        f"WHERE h.{finance_time_field} >= %s "
        f"AND h.{finance_time_field} < DATE_ADD(%s, INTERVAL 1 DAY) "
        "AND h.outsourcing_order_type = %s "
        "GROUP BY d.material_code"
    )
    result: Dict[str, Decimal] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [start_date, end_date, finance_order_type])
        for row in cursor.fetchall():
            result[str(row["material_code"])] = to_decimal(row["amount"])
    return result


def build_rows(
    cost_map: Dict[str, Decimal],
    finance_map: Dict[str, Decimal],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for material_code in sorted(set(cost_map) | set(finance_map)):
        cost_amount = cost_map.get(material_code, Decimal("0"))
        finance_amount = finance_map.get(material_code, Decimal("0"))
        diff = cost_amount - finance_amount
        rows.append(
            {
                "material_code": material_code,
                "actual_restore_outsource_amount": str(cost_amount),
                "finance_outsource_amount": str(finance_amount),
                "diff": str(diff),
                "status": "MATCH" if diff == 0 else "DIFF",
            }
        )
    return rows


def write_csv(path: str, rows: Iterable[Dict[str, str]]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    fieldnames = [
        "material_code",
        "actual_restore_outsource_amount",
        "finance_outsource_amount",
        "diff",
        "status",
    ]
    with path_obj.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row_list)


def main() -> int:
    args = parse_args()
    datetime.strptime(args.start_date, "%Y-%m-%d")
    datetime.strptime(args.end_date, "%Y-%m-%d")
    datetime.strptime(args.calc_month, "%Y-%m-%d")
    load_dotenv(args.env_file)

    conn = connect()
    try:
        cost_map = fetch_cost_amount_map(
            conn,
            args.cost_table,
            args.cost_field,
            args.cost_parent_id,
            args.calc_month,
        )
        finance_map = fetch_finance_amount_map(
            conn,
            args.finance_detail_table,
            args.finance_header_table,
            args.finance_field,
            args.finance_time_field,
            args.finance_order_type,
            args.start_date,
            args.end_date,
        )
    finally:
        conn.close()

    rows = build_rows(cost_map, finance_map)
    diff_rows = [row for row in rows if row["status"] != "MATCH"]
    cost_total = sum(cost_map.values(), Decimal("0"))
    finance_total = sum(finance_map.values(), Decimal("0"))
    total_diff = cost_total - finance_total

    write_csv(args.output, rows)
    print(f"range: {args.start_date} to {args.end_date}")
    print(f"calc_month: {args.calc_month}")
    print(f"cost field: {args.cost_field}")
    print(f"cost parent_id: {args.cost_parent_id}")
    print(f"finance field: {args.finance_field}")
    print(f"finance time field: {args.finance_time_field}")
    print(f"finance order type: {args.finance_order_type}")
    print(f"actual restore total: {cost_total}")
    print(f"finance total: {finance_total}")
    print(f"total diff: {total_diff}")
    print(f"material diff rows: {len(diff_rows)}")
    print(f"output: {args.output}")
    return 0 if not diff_rows and total_diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
