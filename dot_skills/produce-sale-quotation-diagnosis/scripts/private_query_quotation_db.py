#!/usr/bin/env python3
"""Read-only database helper for ERP Cost quotation diagnosis."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query ERP Cost quotation data in read-only mode.")
    parser.add_argument("--offer-price-id")
    parser.add_argument("--standard-cost-id")
    parser.add_argument("--material-code")
    parser.add_argument("--factory-code")
    parser.add_argument("--reassembly-quotation-id")
    parser.add_argument("--schema", default="erp_cost")
    parser.add_argument("--env-file", default="D:/codex/codex-file-organizer/.env")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--custom-sql", help="Optional single SELECT statement. Use %%s placeholders.")
    parser.add_argument("--param", action="append", default=[], help="Parameter for --custom-sql; repeatable.")
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
    try:
        import pymysql
        from pymysql.cursors import DictCursor
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Missing dependency: pymysql. Install/use a Python environment with pymysql for DB queries.") from exc

    return pymysql.connect(
        host=env_required("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=env_required("DB_USER"),
        password=env_required("DB_PASSWORD"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        read_timeout=600,
        write_timeout=600,
    )


def quote_schema(schema: str) -> str:
    if not schema.replace("_", "").isalnum():
        raise ValueError(f"Unsafe schema name: {schema}")
    return f"`{schema}`"


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ")
    return str(value)


def fetch(conn, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(sql, list(params))
        return list(cursor.fetchall())


def select_by_offer_price_id(schema: str, offer_price_id: str) -> List[Tuple[str, str, Sequence[Any]]]:
    s = quote_schema(schema)
    tables = [
        "offer_price_order",
        "offer_price_order_formula",
        "offer_price_order_injection",
        "offer_price_order_outsource",
        "offer_price_reassembly_quotation",
    ]
    return [
        (table, f"SELECT * FROM {s}.`{table}` WHERE offer_price_id = %s", [offer_price_id])
        for table in tables
    ]


def standard_cost_queries(schema: str, standard_cost_id: Optional[str], material_code: Optional[str], factory_code: Optional[str]) -> List[Tuple[str, str, Sequence[Any]]]:
    s = quote_schema(schema)
    queries: List[Tuple[str, str, Sequence[Any]]] = []
    if standard_cost_id:
        queries.extend(
            [
                (
                    "produce_standard_cost",
                    f"SELECT * FROM {s}.`produce_standard_cost` WHERE standard_cost_id = %s",
                    [standard_cost_id],
                ),
                (
                    "produce_standard_cost_detail",
                    f"SELECT * FROM {s}.`produce_standard_cost_detail` WHERE standard_cost_id = %s ORDER BY level, parent_detail_id, detail_id",
                    [standard_cost_id],
                ),
                (
                    "produce_standard_cost_info_mapping",
                    f"""
                    SELECT *
                    FROM {s}.`produce_standard_cost_info_mapping`
                    WHERE cost_detail_id = %s
                       OR cost_detail_id IN (
                           SELECT detail_id FROM {s}.`produce_standard_cost_detail` WHERE standard_cost_id = %s
                       )
                    """,
                    [standard_cost_id, standard_cost_id],
                ),
            ]
        )
    if material_code:
        sql = f"SELECT * FROM {s}.`produce_standard_cost` WHERE material_code = %s"
        params: List[Any] = [material_code]
        if factory_code:
            sql += " AND factory_code = %s"
            params.append(factory_code)
        sql += " ORDER BY calc_time DESC LIMIT 20"
        queries.append(("produce_standard_cost_by_material", sql, params))
    return queries


def context_queries(schema: str, material_code: Optional[str], factory_code: Optional[str], reassembly_quotation_id: Optional[str]) -> List[Tuple[str, str, Sequence[Any]]]:
    s = quote_schema(schema)
    queries: List[Tuple[str, str, Sequence[Any]]] = []
    if factory_code:
        queries.append(("basic_offer_price", f"SELECT * FROM {s}.`basic_offer_price` WHERE factory_code = %s ORDER BY update_time DESC LIMIT 20", [factory_code]))
    if material_code or factory_code:
        where = []
        params: List[Any] = []
        if factory_code:
            where.append("factory_code = %s")
            params.append(factory_code)
        if material_code:
            where.append("(material_code = %s OR goods_code = %s)")
            params.extend([material_code, material_code])
        queries.append(("operation_fee_quotation", f"SELECT * FROM {s}.`operation_fee_quotation` WHERE {' AND '.join(where)} ORDER BY update_time DESC LIMIT 20", params))
    if material_code:
        queries.extend(
            [
                ("mould_material_detail", f"SELECT * FROM {s}.`mould_material_detail` WHERE material_code = %s ORDER BY update_time DESC LIMIT 50", [material_code]),
                ("reassembly_quotation", f"SELECT * FROM {s}.`reassembly_quotation` WHERE material_code = %s ORDER BY update_time DESC LIMIT 20", [material_code]),
                ("outsourcing_quotation", f"SELECT * FROM {s}.`outsourcing_quotation` WHERE material_code = %s ORDER BY update_time DESC LIMIT 20", [material_code]),
            ]
        )
    if reassembly_quotation_id:
        queries.extend(
            [
                ("reassembly_quotation_process_detail", f"SELECT * FROM {s}.`reassembly_quotation_process_detail` WHERE reassembly_quotation_id = %s ORDER BY process_code", [reassembly_quotation_id]),
                ("reassembly_quotation_related_equipment", f"SELECT * FROM {s}.`reassembly_quotation_related_equipment` WHERE reassembly_quotation_id = %s ORDER BY process_code, equipment_code", [reassembly_quotation_id]),
            ]
        )
    return queries


def validate_custom_sql(sql: str) -> None:
    stripped = sql.strip().lower()
    if not stripped.startswith("select"):
        raise ValueError("--custom-sql only allows SELECT statements")
    if ";" in stripped[:-1]:
        raise ValueError("--custom-sql only allows a single statement")
    blocked = [" update ", " delete ", " insert ", " replace ", " drop ", " alter ", " truncate ", " create "]
    padded = f" {stripped} "
    if any(token in padded for token in blocked):
        raise ValueError("--custom-sql contains a blocked keyword")


def run_queries(conn, queries: Iterable[Tuple[str, str, Sequence[Any]]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name, sql, params in queries:
        try:
            result[name] = fetch(conn, sql, params)
        except Exception as exc:
            result[name] = {"error": str(exc), "sql": " ".join(sql.split()), "params": list(params)}
    return result


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)
    with connect() as conn:
        if args.custom_sql:
            validate_custom_sql(args.custom_sql)
            result = {"custom_sql": fetch(conn, args.custom_sql, args.param)}
        else:
            queries: List[Tuple[str, str, Sequence[Any]]] = []
            if args.offer_price_id:
                queries.extend(select_by_offer_price_id(args.schema, args.offer_price_id))
            queries.extend(standard_cost_queries(args.schema, args.standard_cost_id, args.material_code, args.factory_code))
            queries.extend(context_queries(args.schema, args.material_code, args.factory_code, args.reassembly_quotation_id))
            result = run_queries(conn, queries)

    text = json.dumps(result, ensure_ascii=False, indent=2, default=json_default)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(output)
    else:
        print(text)


if __name__ == "__main__":
    main()
