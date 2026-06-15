#!/usr/bin/env python3
"""Check rule 1 from MySQL.

Rule:
finished inbound quantity = adjusted report quantity

finished inbound quantity:
  actual_num + defective_actual_num (finish detail)

adjusted report quantity:
  default uses linked finish detail quantity, grouped by report detail
  (report_work_order_detail_id -> finish detail)
"""

from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pymysql") from exc


DATE_CANDIDATES = [
    "business_date",
    "biz_date",
    "stock_date",
    "order_date",
    "finish_date",
    "report_date",
    "work_date",
    "audit_time",
    "approve_time",
    "create_time",
    "created_at",
    "updated_at",
]

RULE1_FINISH_COLUMNS = {"material_code", "actual_num", "defective_actual_num"}
RULE1_REPORT_COLUMNS = {"material_code", "report_work_num"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check rule 1 in MySQL")
    parser.add_argument("--start-date", default="2026-03-01")
    parser.add_argument("--end-date", default="2026-03-31")
    parser.add_argument(
        "--env-file",
        default="D:/codex/codex-file-organizer/.env",
        help="Path to .env file",
    )
    parser.add_argument("--database", default=None, help="Optional database override")
    parser.add_argument("--finish-table", default="finish_job_stock_order")
    parser.add_argument("--report-table", default="report_work_order")
    parser.add_argument("--finish-date-column", default=None)
    parser.add_argument("--report-date-column", default=None)
    parser.add_argument(
        "--finish-product-type",
        default="1",
        help="Only use finish detail rows with this product_type. Default 1 means main product only.",
    )
    parser.add_argument(
        "--report-quantity-mode",
        default="adjusted_from_finish",
        choices=["adjusted_from_finish", "report_work_num"],
        help="How to calculate report quantity.",
    )
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument(
        "--output",
        default="D:/codex/工厂账务核对/fms-reconciliation/output/rule1_2026_03.csv",
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


def connect(database_override: str | None):
    host = env_required("DB_HOST")
    port = int(os.getenv("DB_PORT", "3306"))
    user = env_required("DB_USER")
    password = env_required("DB_PASSWORD")
    database = database_override or os.getenv("DB_NAME", "").strip() or None
    kwargs = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "read_timeout": 600,
        "write_timeout": 600,
    }
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def split_table_name(name: str) -> tuple[str | None, str]:
    if "." in name:
        schema, table = name.split(".", 1)
        return schema, table
    return None, name


def resolve_table_name(conn, table_name: str) -> str:
    schema, table = split_table_name(table_name)
    if schema:
        return table_name
    sql = (
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_NAME = %s "
        "AND TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys') "
        "ORDER BY TABLE_SCHEMA"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, [table])
        rows = cursor.fetchall()
    if not rows:
        raise ValueError(f"Table not found: {table_name}")
    if len(rows) > 1:
        matches = ", ".join(f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}" for row in rows)
        raise ValueError(f"Table name {table_name} matched multiple schemas: {matches}")
    row = rows[0]
    return f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}"


def fetch_columns(conn, table_name: str) -> List[str]:
    schema, table = split_table_name(table_name)
    sql = (
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
        "ORDER BY ORDINAL_POSITION"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, [schema, table])
        return [str(row["COLUMN_NAME"]) for row in cursor.fetchall()]


def find_related_tables(conn, table_name: str) -> List[str]:
    schema, table = split_table_name(table_name)
    pattern = f"%{table}%"
    sql = (
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME LIKE %s "
        "ORDER BY TABLE_NAME"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, [schema, pattern])
        return [f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}" for row in cursor.fetchall()]


def choose_date_column(columns: Sequence[str]) -> str | None:
    column_set = {column.lower(): column for column in columns}
    for candidate in DATE_CANDIDATES:
        if candidate.lower() in column_set:
            return column_set[candidate.lower()]
    return None


def to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def run_summary_query(
    conn,
    table_name: str,
    date_column: str,
    quantity_sql: str,
    extra_where_sql: str,
    extra_params: Sequence[str],
    start_date: str,
    end_date: str,
) -> Dict[str, Decimal]:
    sql = (
        f"SELECT material_code, {quantity_sql} AS qty "
        f"FROM {table_name} "
        f"WHERE {date_column} >= %s AND {date_column} < DATE_ADD(%s, INTERVAL 1 DAY) "
        f"{extra_where_sql} "
        "GROUP BY material_code"
    )
    result: Dict[str, Decimal] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [start_date, end_date, *extra_params])
        for row in cursor.fetchall():
            result[str(row["material_code"])] = to_decimal(row["qty"])
    return result


def run_adjusted_report_summary_query(
    conn,
    report_table: str,
    report_date_column: str,
    finish_table: str,
    finish_product_type: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Decimal]:
    sql = (
        "SELECT r.material_code, "
        "SUM(COALESCE(f.finish_qty, 0)) AS qty "
        f"FROM {report_table} r "
        "LEFT JOIN ("
        "  SELECT report_work_order_detail_id, "
        "         SUM(COALESCE(actual_num, 0) + COALESCE(defective_actual_num, 0)) AS finish_qty "
        f"  FROM {finish_table} "
        "  WHERE product_type = %s "
        "  GROUP BY report_work_order_detail_id"
        ") f ON f.report_work_order_detail_id = r.detail_id "
        f"WHERE r.{report_date_column} >= %s AND r.{report_date_column} < DATE_ADD(%s, INTERVAL 1 DAY) "
        "GROUP BY r.material_code"
    )
    result: Dict[str, Decimal] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [finish_product_type, start_date, end_date])
        for row in cursor.fetchall():
            result[str(row["material_code"])] = to_decimal(row["qty"])
    return result


def build_rows(left_map: Dict[str, Decimal], right_map: Dict[str, Decimal]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for material_code in sorted(set(left_map) | set(right_map)):
        left_qty = left_map.get(material_code, Decimal("0"))
        right_qty = right_map.get(material_code, Decimal("0"))
        diff = left_qty - right_qty
        rows.append(
            {
                "material_code": material_code,
                "finish_qty": str(left_qty),
                "report_qty": str(right_qty),
                "diff": str(diff),
                "status": "MATCH" if diff == 0 else "DIFF",
            }
        )
    return rows


def write_csv(path: str, rows: Iterable[Dict[str, str]]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    fieldnames = ["material_code", "finish_qty", "report_qty", "diff", "status"]
    with path_obj.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row_list)


def main() -> int:
    args = parse_args()
    datetime.strptime(args.start_date, "%Y-%m-%d")
    datetime.strptime(args.end_date, "%Y-%m-%d")
    load_dotenv(args.env_file)

    conn = connect(args.database)
    try:
        finish_table = resolve_table_name(conn, args.finish_table)
        report_table = resolve_table_name(conn, args.report_table)
        finish_columns = fetch_columns(conn, finish_table)
        report_columns = fetch_columns(conn, report_table)
        finish_date_column = args.finish_date_column or choose_date_column(finish_columns)
        report_date_column = args.report_date_column or choose_date_column(report_columns)

        print(f"finish table: {finish_table}")
        print(f"report table: {report_table}")
        print(f"finish columns: {', '.join(finish_columns)}")
        print(f"report columns: {', '.join(report_columns)}")
        print(f"finish date column: {finish_date_column or 'NOT_FOUND'}")
        print(f"report date column: {report_date_column or 'NOT_FOUND'}")
        print(f"report quantity mode: {args.report_quantity_mode}")

        if not RULE1_FINISH_COLUMNS.issubset(set(finish_columns)):
            finish_related = find_related_tables(conn, finish_table)
            print("finish related tables:")
            for name in finish_related:
                related_columns = fetch_columns(conn, name)
                print(f"  {name}: {', '.join(related_columns)}")

        if not RULE1_REPORT_COLUMNS.issubset(set(report_columns)):
            report_related = find_related_tables(conn, report_table)
            print("report related tables:")
            for name in report_related:
                related_columns = fetch_columns(conn, name)
                print(f"  {name}: {', '.join(related_columns)}")

        if args.inspect_only:
            return 0

        if not finish_date_column or not report_date_column:
            raise ValueError(
                "Could not detect date columns automatically. "
                "Pass --finish-date-column and --report-date-column."
            )

        finish_map = run_summary_query(
            conn,
            finish_table,
            finish_date_column,
            "SUM(COALESCE(actual_num, 0) + COALESCE(defective_actual_num, 0))",
            "AND product_type = %s",
            [args.finish_product_type],
            args.start_date,
            args.end_date,
        )

        if args.report_quantity_mode == "adjusted_from_finish":
            report_map = run_adjusted_report_summary_query(
                conn,
                report_table,
                report_date_column,
                finish_table,
                args.finish_product_type,
                args.start_date,
                args.end_date,
            )
        else:
            report_map = run_summary_query(
                conn,
                report_table,
                report_date_column,
                "SUM(COALESCE(report_work_num, 0))",
                "",
                [],
                args.start_date,
                args.end_date,
            )
    finally:
        conn.close()

    rows = build_rows(finish_map, report_map)
    diff_rows = [row for row in rows if row["status"] != "MATCH"]
    finish_total = sum(finish_map.values(), Decimal("0"))
    report_total = sum(report_map.values(), Decimal("0"))
    total_diff = finish_total - report_total

    write_csv(args.output, rows)
    print(f"range: {args.start_date} to {args.end_date}")
    print(f"finish total: {finish_total}")
    print(f"report total: {report_total}")
    print(f"finish product type: {args.finish_product_type}")
    print(f"total diff: {total_diff}")
    print(f"material diff rows: {len(diff_rows)}")
    print(f"output: {args.output}")
    return 0 if not diff_rows and total_diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
