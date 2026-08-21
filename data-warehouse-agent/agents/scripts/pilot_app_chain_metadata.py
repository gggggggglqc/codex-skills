#!/usr/bin/env python3
"""Read-only metadata check for the delivery V1 -> net-profit V2 -> finance-profit pilot."""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import pymysql


TABLES = (
    "doris_app_report_delivery_v1",
    "doris_app_net_profit_check_report_v2",
    "doris_app_finance_profit_business",
)


def load_profile(name: str) -> dict:
    path = Path.home() / ".config" / "db-profiles" / f"{name}.env"
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def connect(profile: str):
    cfg = load_profile(profile)
    return pymysql.connect(
        host=cfg["DB_HOST"],
        port=int(cfg["DB_PORT"]),
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database="dp_dws",
        charset=cfg.get("DB_CHARSET", "utf8mb4"),
        connect_timeout=10,
        read_timeout=60,
        cursorclass=pymysql.cursors.DictCursor,
    )


def inspect_table(conn, table: str, start_date: date) -> dict:
    with conn.cursor() as cur:
        cur.execute(f"DESCRIBE `{table}`")
        columns = [row["Field"] for row in cur.fetchall()]
        cur.execute(f"SELECT MIN(dt) AS min_dt, MAX(dt) AS max_dt, COUNT(*) AS total_rows FROM `{table}`")
        summary = cur.fetchone()
        cur.execute(
            f"""
            SELECT dt, COUNT(*) AS row_count
            FROM `{table}`
            WHERE dt >= %s
            GROUP BY dt
            ORDER BY dt
            """,
            (start_date,),
        )
        daily = cur.fetchall()
    return {"columns": columns, "summary": summary, "daily_rows": daily}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="doris")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    start_date = date.today() - timedelta(days=args.days - 1)
    conn = connect(args.profile)
    try:
        result = {
            "check_type": "app_chain_metadata",
            "read_only": True,
            "window_start": str(start_date),
            "tables": {table: inspect_table(conn, table, start_date) for table in TABLES},
        }
    finally:
        conn.close()
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
