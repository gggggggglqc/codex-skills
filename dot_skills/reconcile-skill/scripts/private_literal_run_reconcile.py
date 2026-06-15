#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""统一入口：按类型转发到具体核对脚本。"""

import argparse
import os
import subprocess
import sys


SCRIPT_MAP = {
    "no_order_return": "no_order_return_reconcile.py",
    "sales_outbound": "sales_outbound_reconcile.py",
    "purchase": "purchase_in_stock_reconcile.py",
    "other_in": "other_in_stock_reconcile.py",
    "other_out": "other_out_stock_reconcile.py",
    "return_income": "return_income_reconcile.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="统一核对入口")
    parser.add_argument("reconcile_type", choices=sorted(SCRIPT_MAP.keys()), help="核对类型")
    parser.add_argument("--start-time", required=True, help="开始时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end-time", required=True, help="结束时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--summary-output", help="汇总输出文件")
    parser.add_argument("--detail-output", help="明细输出文件")
    parser.add_argument("--batch-size", type=int, help="分批查询大小")
    parser.add_argument("--day-batch-size", type=int, help="按多少天一批查询")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_script = os.path.join(script_dir, SCRIPT_MAP[args.reconcile_type])

    cmd = [
        sys.executable,
        target_script,
        "--start-time",
        args.start_time,
        "--end-time",
        args.end_time,
    ]
    if args.summary_output:
        cmd.extend(["--summary-output", args.summary_output])
    if args.detail_output:
        cmd.extend(["--detail-output", args.detail_output])
    if args.batch_size is not None:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if args.day_batch_size is not None:
        cmd.extend(["--day-batch-size", str(args.day_batch_size)])

    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
