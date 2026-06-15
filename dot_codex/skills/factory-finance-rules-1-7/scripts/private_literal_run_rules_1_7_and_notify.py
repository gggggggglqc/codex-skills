#!/usr/bin/env python3
"""Run rule 1-7 checks, generate a summary, then notify a robot."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = Path.home() / "Desktop"


@dataclass
class RuleSpec:
    rule_no: int
    name: str
    script_name: str
    output_name: str
    extra_args: List[str] = field(default_factory=list)


RULE_SPECS = [
    RuleSpec(
        1,
        "完工入库单数量 = 报工入库数量",
        "check_rule1_db.py",
        "规则1-完工入库单数量等于报工入库数量-{period}.csv",
        [
            "--finish-table",
            "erp_iom.finish_job_stock_order_detail",
            "--report-table",
            "mes_aps.report_work_order_detail",
            "--finish-date-column",
            "create_time",
            "--report-date-column",
            "create_time",
        ],
    ),
    RuleSpec(2, "完工入库单数量 = 实际成本还原的完工入库数量", "check_rule2_db.py", "规则2-完工入库单数量等于实际成本还原的完工入库数量-{period}.csv"),
    RuleSpec(3, "完工入库单数量 = 生产成本管理的生产入库数量", "check_rule3_db.py", "规则3-完工入库单数量等于生产成本管理的生产入库数量-{period}.csv"),
    RuleSpec(4, "完工入库单成本单价*数量 = 实际成本还原的生产成本总金额", "check_rule4_db.py", "规则4-完工入库单成本单价乘数量等于实际成本还原的生产成本总金额-{period}.csv"),
    RuleSpec(5, "完工入库单成本单价*数量 = 生产成本管理的实际生产入库总金额", "check_rule5_db.py", "规则5-完工入库单成本单价乘数量等于生产成本管理的实际生产入库总金额-{period}.csv"),
    RuleSpec(6, "实际成本还原的实际委外加工总费用 = 财务-委外加工明细金额", "check_rule6_db.py", "规则6-实际成本还原的实际委外加工总费用等于财务委外加工明细金额-{period}.csv"),
    RuleSpec(7, "领料出库单数量 = 生产收发-倒冲领料单数量", "check_rule7_db.py", "规则7-领料出库单数量等于生产收发倒冲领料单数量-{period}.csv"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rule 1-7 checks and notify robot")
    parser.add_argument("--start-date", default="2026-03-01")
    parser.add_argument("--end-date", default="2026-03-31")
    parser.add_argument("--calc-month", default="2026-03-01")
    parser.add_argument(
        "--env-file",
        default="D:/codex/codex-file-organizer/.env",
        help="Path to .env file",
    )
    parser.add_argument(
        "--title",
        default="工厂账务核对 1-7 结果",
        help="Robot message title",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for rule CSV files and summary. Defaults to Desktop.",
    )
    return parser.parse_args()


def extract_period(start_date: str) -> str:
    year, month, _ = start_date.split("-")
    return f"{year}_{month}"


def parse_stdout(stdout: str) -> Dict[str, str]:
    info: Dict[str, str] = {}
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        info[key.strip().lower()] = value.strip()
    return info


def build_command(spec: RuleSpec, args: argparse.Namespace, output_path: Path) -> List[str]:
    command = [
        sys.executable,
        str(SCRIPT_DIR / spec.script_name),
        "--start-date",
        args.start_date,
        "--end-date",
        args.end_date,
        "--env-file",
        args.env_file,
        "--output",
        str(output_path),
    ]
    if spec.rule_no in {2, 3, 4, 5, 6}:
        command.extend(["--calc-month", args.calc_month])
    command.extend(spec.extra_args)
    return command


def first_present(info: Dict[str, str], keys: List[str]) -> str:
    for key in keys:
        value = info.get(key.lower(), "")
        if value:
            return value
    return ""


def write_summary(summary_path: Path, title: str, lines: List[str]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(f"# {title}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    period = extract_period(args.start_date)
    output_dir = Path(args.output_dir)
    summary_lines = [
        f"- 时间范围: {args.start_date} 到 {args.end_date}",
        f"- 成本月份: {args.calc_month}",
        f"- 输出目录: {output_dir}",
        "",
    ]

    for spec in RULE_SPECS:
        output_path = output_dir / spec.output_name.format(period=period)
        command = build_command(spec, args, output_path)
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if completed.returncode not in (0, 1):
            raise SystemExit(
                f"Rule {spec.rule_no} failed to execute.\n"
                f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
            )

        info = parse_stdout(completed.stdout)
        status = "一致" if completed.returncode == 0 else "差异"
        total_diff = first_present(info, ["total diff"])
        diff_rows = first_present(info, ["material diff rows", "detail diff rows"])
        summary_lines.extend(
            [
                f"## 规则 {spec.rule_no}：{spec.name}",
                f"- 执行状态: {status}",
                f"- 结果文件: {output_path}",
                f"- 汇总差异: {total_diff}",
                f"- 差异行数: {diff_rows}",
                "",
            ]
        )

    summary_path = output_dir / f"规则1到7汇总结果-{period}.md"
    write_summary(summary_path, args.title, summary_lines)

    notify_command = [
        sys.executable,
        str(SCRIPT_DIR / "send_robot_message.py"),
        "--title",
        args.title,
        "--content-file",
        str(summary_path),
        "--env-file",
        args.env_file,
    ]
    completed = subprocess.run(notify_command, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if completed.returncode != 0:
        raise SystemExit(
            "Rules 1-7 outputs were generated, but robot notification failed.\n"
            f"summary: {summary_path}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )

    print(f"summary: {summary_path}")
    print(completed.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
