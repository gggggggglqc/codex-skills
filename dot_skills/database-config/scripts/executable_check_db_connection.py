#!/usr/bin/env python3
"""Run a read-only database connection smoke test for a local profile."""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from load_db_profile import load_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="erp-mysql")
    args = parser.parse_args()

    try:
        import pymysql
    except ImportError:
        print(json.dumps({"ok": False, "error": "pymysql is not installed"}, ensure_ascii=False))
        return 1

    data = load_profile(args.profile)
    conn = pymysql.connect(
        host=data["DB_HOST"],
        port=int(data["DB_PORT"]),
        user=data["DB_USER"],
        password=data["DB_PASSWORD"],
        database=data["DB_NAME"],
        charset=data.get("DB_CHARSET") or "utf8mb4",
        connect_timeout=10,
        read_timeout=30,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
    finally:
        conn.close()

    print(json.dumps({"ok": row.get("ok") == 1, "profile": args.profile}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
