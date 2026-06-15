#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地钉钉机器人测试服务。

目标：
1. 接收本地 HTTP 请求，模拟钉钉群里 @机器人后的文本消息
2. 解析核对指令
3. 调用 skill 内统一入口脚本执行核对
4. 返回结果摘要
5. 可选地把结果摘要转发到钉钉群机器人 webhook
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import hmac
import base64
import hashlib
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


SERVICE_DIR = Path(__file__).resolve().parent
SKILL_DIR = SERVICE_DIR.parent
SCRIPT_DIR = SKILL_DIR / "scripts"
RUN_SCRIPT = SCRIPT_DIR / "run_reconcile.py"
PYTHON_EXE = Path(r"C:\Users\lqc\AppData\Local\Python\bin\python.exe")
DESKTOP_DIR = Path.home() / "Desktop"
DEFAULT_TIMEOUT_SECONDS = 3600


TYPE_ALIASES = {
    "采购": "purchase",
    "采购入库": "purchase",
    "purchase": "purchase",
    "其他入库": "other_in",
    "other_in": "other_in",
    "其他出库": "other_out",
    "other_out": "other_out",
    "退货应收入库": "return_income",
    "退货应收": "return_income",
    "return_income": "return_income",
    "无单退货入库": "no_order_return",
    "无单退货": "no_order_return",
    "no_order_return": "no_order_return",
    "销售出库": "sales_outbound",
    "销售": "sales_outbound",
    "sales_outbound": "sales_outbound",
}


SUMMARY_PATTERNS = {
    "summary_rows": re.compile(r"汇总对比\s+(\d+)\s+行"),
    "diff_pairs": re.compile(r"汇总差异组合\s+(\d+)\s+个"),
    "detail_rows": re.compile(r"单据差异\s+(\d+)\s+条"),
    "summary_output": re.compile(r"汇总文件:\s*(.+)"),
    "detail_output": re.compile(r"单据差异文件:\s*(.+)"),
}


TYPE_LABELS = {
    "purchase": "采购入库",
    "other_in": "其他入库",
    "other_out": "其他出库",
    "return_income": "退货应收入库",
    "no_order_return": "无单退货入库",
    "sales_outbound": "销售出库",
}


app = FastAPI(title="DingTalk Reconcile Service", version="1.0.0")


class LocalRunRequest(BaseModel):
    command: str = Field(..., description="例如：销售出库 2026-03-01 2026-03-31")
    send_to_dingtalk: bool = Field(False, description="是否把结果摘要发到钉钉群机器人 webhook")


class DingTalkMessageRequest(BaseModel):
    payload: Dict[str, Any] = Field(..., description="钉钉回调原始 JSON")
    send_to_dingtalk: bool = Field(False, description="是否回发到钉钉群机器人 webhook")


@dataclass
class ParsedCommand:
    reconcile_type: str
    start_time: str
    end_time: str
    day_batch_size: Optional[int] = None


def parse_date_token(value: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    raise ValueError(f"日期格式不正确：{value}，请使用 YYYY-MM-DD")


def normalize_text(text: str) -> str:
    text = text.replace("|", " ").replace("，", " ").replace(",", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_command(text: str) -> ParsedCommand:
    normalized = normalize_text(text)
    if not normalized:
        raise ValueError("指令为空，请输入例如：销售出库 2026-03-01 2026-03-31")

    parts = normalized.split(" ")
    if len(parts) < 3:
        raise ValueError("指令不完整，请输入：类型 开始日期 结束日期，例如：销售出库 2026-03-01 2026-03-31")

    type_token = parts[0]
    reconcile_type = TYPE_ALIASES.get(type_token)
    if not reconcile_type:
        raise ValueError(f"不支持的核对类型：{type_token}")

    start_date = parse_date_token(parts[1])
    end_date = parse_date_token(parts[2])
    day_batch_size = None

    if len(parts) >= 4:
        extra = parts[3].lower()
        if extra.startswith("day_batch_size="):
            day_batch_size = int(extra.split("=", 1)[1])
        elif extra.startswith("batch="):
            day_batch_size = int(extra.split("=", 1)[1])
        else:
            raise ValueError("第四个参数只支持 day_batch_size=N，例如：销售出库 2026-03-01 2026-03-31 day_batch_size=1")

    return ParsedCommand(
        reconcile_type=reconcile_type,
        start_time=f"{start_date} 00:00:00",
        end_time=f"{end_date} 23:59:59",
        day_batch_size=day_batch_size,
    )


def build_output_paths(reconcile_type: str, start_time: str, end_time: str) -> tuple[str, str]:
    start_date = start_time[:10].replace("-", "_")
    end_date = end_time[:10].replace("-", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{reconcile_type}_{start_date}_{end_date}_{timestamp}"
    summary_output = str(DESKTOP_DIR / f"{base}_summary.csv")
    detail_output = str(DESKTOP_DIR / f"{base}_detail.csv")
    return summary_output, detail_output


def parse_run_output(stdout: str, fallback_summary: str, fallback_detail: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "raw_output": stdout,
        "summary_rows": None,
        "diff_pairs": None,
        "detail_rows": None,
        "summary_output": fallback_summary,
        "detail_output": fallback_detail,
    }
    for key, pattern in SUMMARY_PATTERNS.items():
        match = pattern.search(stdout)
        if not match:
            continue
        value = match.group(1).strip()
        if key in {"summary_rows", "diff_pairs", "detail_rows"}:
            result[key] = int(value)
        else:
            result[key] = value
    return result


def run_reconcile(command: ParsedCommand) -> Dict[str, Any]:
    if not RUN_SCRIPT.exists():
        raise RuntimeError(f"未找到统一入口脚本：{RUN_SCRIPT}")
    if not PYTHON_EXE.exists():
        raise RuntimeError(f"未找到 Python 解释器：{PYTHON_EXE}")

    summary_output, detail_output = build_output_paths(command.reconcile_type, command.start_time, command.end_time)
    cmd = [
        str(PYTHON_EXE),
        str(RUN_SCRIPT),
        command.reconcile_type,
        "--start-time",
        command.start_time,
        "--end-time",
        command.end_time,
        "--summary-output",
        summary_output,
        "--detail-output",
        detail_output,
    ]
    if command.day_batch_size is not None:
        cmd.extend(["--day-batch-size", str(command.day_batch_size)])
    elif command.reconcile_type == "sales_outbound":
        # 销售出库默认按天跑，避免整月全量 SQL 太慢。
        cmd.extend(["--day-batch-size", "1"])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    completed = subprocess.run(
        cmd,
        cwd=str(SKILL_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=DEFAULT_TIMEOUT_SECONDS,
        env=env,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "脚本执行失败")

    parsed = parse_run_output(completed.stdout, summary_output, detail_output)
    parsed["reconcile_type"] = command.reconcile_type
    parsed["type_label"] = TYPE_LABELS.get(command.reconcile_type, command.reconcile_type)
    parsed["start_time"] = command.start_time
    parsed["end_time"] = command.end_time
    return parsed


def build_reply_text(result: Dict[str, Any]) -> str:
    return (
        f"{result['type_label']} 核对完成\n"
        f"时间范围：{result['start_time']} ~ {result['end_time']}\n"
        f"汇总对比：{result['summary_rows']} 行\n"
        f"差异组合：{result['diff_pairs']} 个\n"
        f"单据差异：{result['detail_rows']} 条\n"
        f"汇总文件：{result['summary_output']}\n"
        f"明细文件：{result['detail_output']}"
    )


def extract_text_from_payload(payload: Dict[str, Any]) -> str:
    candidates = [
        payload.get("text", {}).get("content") if isinstance(payload.get("text"), dict) else None,
        payload.get("content"),
        payload.get("msg", {}).get("text", {}).get("content") if isinstance(payload.get("msg"), dict) else None,
        payload.get("msg", {}).get("content") if isinstance(payload.get("msg"), dict) else None,
    ]
    for item in candidates:
        if isinstance(item, str) and item.strip():
            return item.strip()
    raise ValueError("未从请求体中提取到文本内容")


def maybe_send_to_dingtalk(text: str) -> None:
    webhook = os.getenv("DINGTALK_WEBHOOK", "").strip()
    secret = os.getenv("DINGTALK_SECRET", "").strip()
    keyword = os.getenv("DINGTALK_KEYWORD", "").strip()
    if not webhook:
        raise RuntimeError("未配置 DINGTALK_WEBHOOK，暂时无法回发到钉钉群")

    final_text = text
    if keyword and keyword not in final_text:
        final_text = f"{keyword}\n{final_text}"

    final_webhook = webhook
    if secret:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        separator = "&" if "?" in webhook else "?"
        final_webhook = f"{webhook}{separator}timestamp={timestamp}&sign={sign}"

    response = requests.post(
        final_webhook,
        json={
            "msgtype": "text",
            "text": {"content": final_text},
        },
        timeout=30,
    )
    response.raise_for_status()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/local/run")
def local_run(request: LocalRunRequest) -> Dict[str, Any]:
    try:
        parsed = parse_command(request.command)
        result = run_reconcile(parsed)
        reply_text = build_reply_text(result)
        if request.send_to_dingtalk:
            maybe_send_to_dingtalk(reply_text)
        return {
            "success": True,
            "request_command": request.command,
            "result": result,
            "reply_text": reply_text,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/dingtalk/message")
def dingtalk_message(request: DingTalkMessageRequest) -> Dict[str, Any]:
    try:
        text = extract_text_from_payload(request.payload)
        parsed = parse_command(text)
        result = run_reconcile(parsed)
        reply_text = build_reply_text(result)
        if request.send_to_dingtalk:
            maybe_send_to_dingtalk(reply_text)
        return {
            "success": True,
            "received_text": text,
            "result": result,
            "reply_text": reply_text,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dingtalk_reconcile_service:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
