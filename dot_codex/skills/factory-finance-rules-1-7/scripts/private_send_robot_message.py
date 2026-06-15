#!/usr/bin/env python3
"""Send reconciliation result to a configured robot."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Dict
from urllib import request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send reconciliation message to robot")
    parser.add_argument("--title", required=True, help="Message title")
    parser.add_argument("--content-file", required=True, help="Path to markdown/text content file")
    parser.add_argument(
        "--env-file",
        default="D:/codex/codex-file-organizer/.env",
        help="Path to .env file",
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


def env_optional(name: str) -> str:
    return os.getenv(name, "").strip()


def post_json(url: str, payload: Dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        if resp.status >= 400:
            raise RuntimeError(f"Robot webhook failed: HTTP {resp.status} {body}")


def build_dingtalk_signed_webhook(webhook: str, secret: str) -> str:
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    hmac_code = hmac.new(secret.encode("utf-8"), string_to_sign, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def send_by_webhook(robot_type: str, webhook: str, title: str, content: str, secret: str) -> None:
    robot_type = robot_type.lower()
    if robot_type == "wecom":
        payload = {"msgtype": "markdown", "markdown": {"content": f"## {title}\n{content}"}}
        post_json(webhook, payload)
        return
    if robot_type == "dingtalk":
        if secret:
            webhook = build_dingtalk_signed_webhook(webhook, secret)
        payload = {"msgtype": "markdown", "markdown": {"title": title, "text": f"## {title}\n{content}"}}
        post_json(webhook, payload)
        return
    if robot_type == "feishu":
        payload = {"msg_type": "text", "content": {"text": f"{title}\n{content}"}}
        post_json(webhook, payload)
        return
    raise ValueError(f"Unsupported RECONCILE_NOTIFY_TYPE: {robot_type}")


def send_by_command(command_template: str, title: str, content_file: str) -> None:
    command = command_template.format(title=title, content_file=content_file)
    completed = subprocess.run(command, shell=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Robot command failed with exit code {completed.returncode}")


def main() -> int:
    args = parse_args()
    load_dotenv(args.env_file)

    content = Path(args.content_file).read_text(encoding="utf-8")
    command_template = env_optional("RECONCILE_NOTIFY_COMMAND")
    webhook = env_optional("RECONCILE_NOTIFY_WEBHOOK")
    robot_type = env_optional("RECONCILE_NOTIFY_TYPE") or "wecom"
    secret = env_optional("RECONCILE_NOTIFY_SECRET")
    keyword = env_optional("RECONCILE_NOTIFY_KEYWORD")
    if keyword:
        content = f"{keyword}\n{content}"

    if command_template:
        send_by_command(command_template, args.title, args.content_file)
        print("Robot message sent by command")
        return 0

    if webhook:
        send_by_webhook(robot_type, webhook, args.title, content, secret)
        print("Robot message sent by webhook")
        return 0

    raise SystemExit(
        "Missing robot configuration. Set RECONCILE_NOTIFY_COMMAND "
        "or RECONCILE_NOTIFY_WEBHOOK in the env file."
    )


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    raise SystemExit(main())
