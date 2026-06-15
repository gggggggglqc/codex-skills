#!/usr/bin/env python3
"""Check rule 7 from MySQL.

Rule:
material issue outbound quantity
= production issue/receipt backflush take-material quantity

IOM side:
  erp_iom.take_material_stock_order_detail.actual_num
  joined to erp_iom.take_material_stock_order by stock_order_id
  filtered by billing_time by default

MES side:
  mes_aps.take_material_order_detail.base_unit_apply_num
  joined to mes_aps.take_material_order by take_material_order_id
  filtered by take_time by default

Important:
  compare in base unit.
  mes base_unit_apply_num matches iom actual_num;
  mes pro_unit_real_num is production-unit quantity and may differ.
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
    parser = argparse.ArgumentParser(description="Check rule 7 in MySQL")
    parser.add_argument("--start-date", default="2026-03-01")
    parser.add_argument("--end-date", default="2026-03-31")
    parser.add_argument(
        "--env-file",
        default="D:/codex/codex-file-organizer/.env",
        help="Path to .env file",
    )
    parser.add_argument(
        "--iom-detail-table",
        default="erp_iom.take_material_stock_order_detail",
    )
    parser.add_argument(
        "--iom-header-table",
        default="erp_iom.take_material_stock_order",
    )
    parser.add_argument(
        "--mes-detail-table",
        default="mes_aps.take_material_order_detail",
    )
    parser.add_argument(
        "--mes-header-table",
        default="mes_aps.take_material_order",
    )
    parser.add_argument(
        "--iom-time-field",
        default="billing_time",
        choices=["create_time", "finish_time", "billing_time"],
        help="Header time field used for IOM month filtering.",
    )
    parser.add_argument(
        "--mes-time-field",
        default="take_time",
        choices=["take_time", "create_time", "update_time"],
        help="Header time field used for MES month filtering.",
    )
    parser.add_argument(
        "--iom-qty-field",
        default="actual_num",
        choices=["actual_num", "required_num"],
        help="IOM quantity field.",
    )
    parser.add_argument(
        "--mes-qty-field",
        default="base_unit_apply_num",
        choices=["base_unit_apply_num", "pro_unit_apply_num", "pro_unit_real_num"],
        help="MES quantity field.",
    )
    parser.add_argument(
        "--output",
        default="D:/codex/工厂账务核对/fms-reconciliation/output/rule7_2026_03.csv",
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


def fetch_iom_map(
    conn,
    iom_detail_table: str,
    iom_header_table: str,
    iom_time_field: str,
    iom_qty_field: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Dict[str, str]]:
    sql = (
        "SELECT d.material_order_detail_id, d.stock_order_id, d.material_code, d.base_unit_code, "
        f"COALESCE(d.{iom_qty_field}, 0) AS qty "
        f"FROM {iom_detail_table} d "
        f"JOIN {iom_header_table} h ON h.stock_order_id = d.stock_order_id "
        f"WHERE h.{iom_time_field} >= %s "
        f"AND h.{iom_time_field} < DATE_ADD(%s, INTERVAL 1 DAY)"
    )
    result: Dict[str, Dict[str, str]] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [start_date, end_date])
        for row in cursor.fetchall():
            detail_id = str(row["material_order_detail_id"])
            result[detail_id] = {
                "stock_order_id": str(row["stock_order_id"]),
                "material_code": str(row["material_code"]),
                "base_unit_code": str(row["base_unit_code"] or ""),
                "qty": str(to_decimal(row["qty"])),
            }
    return result


def fetch_mes_map(
    conn,
    mes_detail_table: str,
    mes_header_table: str,
    mes_time_field: str,
    mes_qty_field: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Dict[str, str]]:
    sql = (
        "SELECT d.detail_id, d.take_material_order_id, d.material_code, "
        "d.base_unit_code, d.produce_unit_code, "
        f"COALESCE(d.{mes_qty_field}, 0) AS qty "
        f"FROM {mes_detail_table} d "
        f"JOIN {mes_header_table} h ON h.take_material_order_id = d.take_material_order_id "
        f"WHERE h.{mes_time_field} >= %s "
        f"AND h.{mes_time_field} < DATE_ADD(%s, INTERVAL 1 DAY)"
    )
    result: Dict[str, Dict[str, str]] = {}
    with conn.cursor() as cursor:
        cursor.execute(sql, [start_date, end_date])
        for row in cursor.fetchall():
            detail_id = str(row["detail_id"])
            result[detail_id] = {
                "take_material_order_id": str(row["take_material_order_id"]),
                "material_code": str(row["material_code"]),
                "base_unit_code": str(row["base_unit_code"] or ""),
                "produce_unit_code": str(row["produce_unit_code"] or ""),
                "qty": str(to_decimal(row["qty"])),
            }
    return result


def build_rows(
    iom_map: Dict[str, Dict[str, str]],
    mes_map: Dict[str, Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for detail_id in sorted(set(iom_map) | set(mes_map)):
        iom_row = iom_map.get(detail_id, {})
        mes_row = mes_map.get(detail_id, {})
        iom_qty = Decimal(iom_row.get("qty", "0"))
        mes_qty = Decimal(mes_row.get("qty", "0"))
        diff = iom_qty - mes_qty
        rows.append(
            {
                "detail_id": detail_id,
                "stock_order_id": iom_row.get("stock_order_id", ""),
                "take_material_order_id": mes_row.get("take_material_order_id", ""),
                "material_code": iom_row.get("material_code", mes_row.get("material_code", "")),
                "iom_base_unit_code": iom_row.get("base_unit_code", ""),
                "mes_base_unit_code": mes_row.get("base_unit_code", ""),
                "mes_produce_unit_code": mes_row.get("produce_unit_code", ""),
                "iom_qty": str(iom_qty),
                "mes_qty": str(mes_qty),
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
        "detail_id",
        "stock_order_id",
        "take_material_order_id",
        "material_code",
        "iom_base_unit_code",
        "mes_base_unit_code",
        "mes_produce_unit_code",
        "iom_qty",
        "mes_qty",
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
    load_dotenv(args.env_file)

    conn = connect()
    try:
        iom_map = fetch_iom_map(
            conn,
            args.iom_detail_table,
            args.iom_header_table,
            args.iom_time_field,
            args.iom_qty_field,
            args.start_date,
            args.end_date,
        )
        mes_map = fetch_mes_map(
            conn,
            args.mes_detail_table,
            args.mes_header_table,
            args.mes_time_field,
            args.mes_qty_field,
            args.start_date,
            args.end_date,
        )
    finally:
        conn.close()

    rows = build_rows(iom_map, mes_map)
    diff_rows = [row for row in rows if row["status"] != "MATCH"]
    iom_total = sum((Decimal(row["qty"]) for row in iom_map.values()), Decimal("0"))
    mes_total = sum((Decimal(row["qty"]) for row in mes_map.values()), Decimal("0"))
    total_diff = iom_total - mes_total

    write_csv(args.output, rows)
    print(f"range: {args.start_date} to {args.end_date}")
    print(f"iom time field: {args.iom_time_field}")
    print(f"mes time field: {args.mes_time_field}")
    print(f"iom qty field: {args.iom_qty_field}")
    print(f"mes qty field: {args.mes_qty_field}")
    print(f"iom detail rows: {len(iom_map)}")
    print(f"mes detail rows: {len(mes_map)}")
    print(f"iom total: {iom_total}")
    print(f"mes total: {mes_total}")
    print(f"total diff: {total_diff}")
    print(f"detail diff rows: {len(diff_rows)}")
    print(f"output: {args.output}")
    return 0 if not diff_rows and total_diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
