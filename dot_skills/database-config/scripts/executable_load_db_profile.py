#!/usr/bin/env python3
"""Load a local database profile and print a redacted view."""

import argparse
import json
import os
from pathlib import Path


PROFILE_DIR = Path.home() / ".config" / "db-profiles"
REQUIRED_KEYS = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")


def parse_env_file(path: Path) -> dict:
    data = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def load_profile(profile: str) -> dict:
    path = PROFILE_DIR / f"{profile}.env"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    data = parse_env_file(path)
    for key in ("DB_TYPE", "DB_CHARSET", "DB_READONLY"):
        data.setdefault(key, os.environ.get(key, ""))
    for key in REQUIRED_KEYS:
        if os.environ.get(key):
            data[key] = os.environ[key]

    missing = [key for key in REQUIRED_KEYS if not data.get(key)]
    if missing:
        raise ValueError(f"Profile {profile} is missing: {', '.join(missing)}")
    data["DB_PROFILE"] = profile
    return data


def redacted(data: dict) -> dict:
    safe = dict(data)
    if safe.get("DB_PASSWORD"):
        safe["DB_PASSWORD"] = "***"
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=os.environ.get("DB_PROFILE", "erp-mysql"))
    args = parser.parse_args()

    data = load_profile(args.profile)
    print(json.dumps(redacted(data), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
