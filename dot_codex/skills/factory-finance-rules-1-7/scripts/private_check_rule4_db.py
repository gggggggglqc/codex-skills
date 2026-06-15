#!/usr/bin/env python3
"""Check rule 4 from MySQL.

Rule:
finished inbound unit cost * quantity = cost restoration production total amount

finished inbound amount:
  cost_price * (actual_num + defective_actual_num)
  from finish inbound detail, filtered by finish header billing_time by default

cost restoration amount:
  actual_produce_amount from erp_cost.produce_cost
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
    parser = argparse.ArgumentParser(description="Check rule 4 in MySQL")
    parser.add_argument("--start-date", default="2026-03-01")
    parser.add_argument("--end-date", default="2026-03-31")
    parser.add_argument("--calc-month", default="2026-03-01")
    parser.add_argument(
        "--env-file",
        default="D:/codex/codex-file-organizer/.env",
        help="Path to .env file",
    )
    parser.add_argument(
        "--finish-table",
        default="erp_iom.finish_job_stock_order_detail",
    )
    parser.add_argument(
        "--finish-header-table",
        default="erp_iom.finish_job_stock_order",
    )
    parser.add_argument(
        "--cost-table",
        default="erp_cost.produce_cost",
    )
    parser.add_argument(
        "--finish-time-field",
        default="billing_time",
        choices=["create_time", "finish_time", "billing_time"],
        help="Header time field used for finished inbound month filtering.",
    )
    parser.add_argument(
        "--output",
        default="D:/codex/工厂账务核对/fms-reconciliation/output/rule4_2026_03.csv",
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


def fetch_finish_amount_map(
    conn,
    finish_table: str,
    finish_header_table: str,
    finish_time_field: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Decimal]:
    sql = (
        "SELECT d.material_code, "
        "SUM(COALESCE(d.cost_price, 0) * (COALESCE(d.actual_num, 0) + COALESCE(d.defective_actual_num, 0))) AS amount "
        f"FROM {finish_table} d "
        f"JOIN {finish_header_table} h ON h.stock_order_id = d.stock_order_id "
        f"WHERE h.{finish_time_field} >= %s AND h.{finish_time_field} < DATE_ADD(%s, INTERVAL 1 DAY) "
        "GROUP BY d.material_code"
    )
    result: Dict[str, Decimal] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [start_date, end_date])
        for row in cursor.fetchall():
            result[str(row["material_code"])] = to_decimal(row["amount"])
    return result


def fetch_cost_amount_map(
    conn,
    cost_table: str,
    calc_month: str,
) -> Dict[str, Decimal]:
    sql = (
        "SELECT material_code, SUM(COALESCE(actual_produce_amount, 0)) AS amount "
        f"FROM {cost_table} "
        "WHERE calc_month = %s "
        "GROUP BY material_code"
    )
    result: Dict[str, Decimal] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [calc_month])
        for row in cursor.fetchall():
            result[str(row["material_code"])] = to_decimal(row["amount"])
    return result


def build_rows(
    finish_map: Dict[str, Decimal],
    cost_map: Dict[str, Decimal],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for material_code in sorted(set(finish_map) | set(cost_map)):
        finish_amount = finish_map.get(material_code, Decimal("0"))
        cost_amount = cost_map.get(material_code, Decimal("0"))
        diff = finish_amount - cost_amount
        rows.append(
            {
                "material_code": material_code,
                "finish_amount": str(finish_amount),
                "cost_amount": str(cost_amount),
                "diff": str(diff),
                "status": "MATCH" if diff == 0 else "DIFF",
            }
        )
    return rows


def write_csv(path: str, rows: Iterable[Dict[str, str]]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    fieldnames = ["material_code", "finish_amount", "cost_amount", "diff", "status"]
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
        finish_map = fetch_finish_amount_map(
            conn,
            args.finish_table,
            args.finish_header_table,
            args.finish_time_field,
            args.start_date,
            args.end_date,
        )
        cost_map = fetch_cost_amount_map(
            conn,
            args.cost_table,
            args.calc_month,
        )
    finally:
        conn.close()

    rows = build_rows(finish_map, cost_map)
    diff_rows = [row for row in rows if row["status"] != "MATCH"]
    finish_total = sum(finish_map.values(), Decimal("0"))
    cost_total = sum(cost_map.values(), Decimal("0"))
    total_diff = finish_total - cost_total

    write_csv(args.output, rows)
    print(f"range: {args.start_date} to {args.end_date}")
    print(f"calc_month: {args.calc_month}")
    print(f"finish time field: {args.finish_time_field}")
    print(f"finish total: {finish_total}")
    print(f"cost total: {cost_total}")
    print(f"total diff: {total_diff}")
    print(f"material diff rows: {len(diff_rows)}")
    print(f"output: {args.output}")
    return 0 if not diff_rows and total_diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
