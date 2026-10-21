#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
退货应收入库单核对工具（FMS vs IOM）

核对流程：
1. 按 入库仓库 + 商品编码 汇总比对数量
2. 仅对汇总有差异的组合，继续下钻到 单号 + 商品编码
3. 支持命令行输入开始/结束时间
4. 输出汇总对比与单据差异 CSV
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence, Tuple

from fms_source_reconcile import close_fms_dataset, get_fms_dataset, run_reconciliation

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少依赖 pymysql，请先安装后再运行。") from exc


PSI_GROUP_TYPES: List[str] = [
    "131",
    "132",
    "133",
    "146",
    "152",
    "153",
    "154",
    "155",
    "167",
    "176",
    "177",
    "181",
    "182",
    "183",
    "184",
    "185",
    "186",
    "187",
    "188",
]
FACTORY_PSI_GROUP_TYPES: List[str] = [
    "422",
    "423",
    "424",
    "425",
    "436",
    "450",
    "451",
    "452",
    "453",
    "454",
    "455",
    "456",
    "457",
]
ORDER_STATUSES: List[str] = ["40", "50", "60", "70"]
SUMMARY_KEY = Tuple[str, str]
DETAIL_KEY = Tuple[str, str]
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")


def parse_datetime(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"非法时间格式: {value}，请使用 YYYY-MM-DD HH:MM:SS") from exc
    return value


def env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"缺少环境变量: {name}")
    return value


def load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as file_obj:
        for raw_line in file_obj:
            line = raw_line.strip().lstrip("\ufeff")
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


def load_known_dotenvs(script_dir: str) -> None:
    candidate_paths = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.path.dirname(script_dir), ".env"),
        r"D:\codex\codex-file-organizer\.env",
    ]
    for path in candidate_paths:
        load_dotenv(path)

    load_dotenv(os.path.join(os.path.expanduser("~"), ".config", "db-profiles", "erp-mysql.env"))


def to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def chunked(items: Sequence, size: int) -> Iterable[Sequence]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def build_pair_filter(alias_warehouse: str, alias_goods: str, pairs: Sequence[Tuple[str, str]]) -> Tuple[str, List[str]]:
    clauses: List[str] = []
    params: List[str] = []
    for warehouse_code, goods_code in pairs:
        clauses.append(f"({alias_warehouse} = %s AND {alias_goods} = %s)")
        params.extend([warehouse_code, goods_code])
    return " OR ".join(clauses), params




def fetch_left_summary(conn, start_time: str, end_time: str) -> Dict[SUMMARY_KEY, Decimal]:
    return get_fms_dataset(conn, sys.modules[__name__], "return_income", start_time, end_time).summary()

def fetch_right_summary(conn, start_time: str, end_time: str, pairs: Sequence[Tuple[str, str]] | None = None, batch_size: int = 100) -> Dict[SUMMARY_KEY, Decimal]:
    status_placeholders = ", ".join(["%s"] * len(ORDER_STATUSES))
    base_sql = (
        "SELECT "
        "COALESCE(b.warehouse_code, '') AS warehouse_code, "
        "a.goods_code AS goods_code, "
        "SUM(a.arrive_num + a.arrive_imperfect_num) AS total_num "
        "FROM erp_iom.return_order_detail a "
        "LEFT JOIN erp_iom.return_order b ON a.return_order_id = b.return_order_id "
        "WHERE b.arrive_time BETWEEN %s AND %s "
        f"AND b.order_status IN ({status_placeholders}) "
    )

    result: Dict[SUMMARY_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        if not pairs:
            sql = base_sql + "GROUP BY COALESCE(b.warehouse_code, ''), a.goods_code"
            cursor.execute(sql, [start_time, end_time] + ORDER_STATUSES)
            for row in cursor.fetchall():
                key = (str(row["warehouse_code"]), str(row["goods_code"]))
                result[key] = to_decimal(row["total_num"])
            return result

        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(b.warehouse_code, '')", "a.goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY COALESCE(b.warehouse_code, ''), a.goods_code"
            params: List[str] = [start_time, end_time] + ORDER_STATUSES + pair_params
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                key = (str(row["warehouse_code"]), str(row["goods_code"]))
                result[key] = to_decimal(row["total_num"])
    return result


def build_summary_rows(left_summary: Dict[SUMMARY_KEY, Decimal], right_summary: Dict[SUMMARY_KEY, Decimal]) -> Tuple[List[Dict[str, str]], List[Tuple[str, str]]]:
    rows: List[Dict[str, str]] = []
    diff_pairs: List[Tuple[str, str]] = []
    all_keys = sorted(set(left_summary.keys()) | set(right_summary.keys()))
    for warehouse_code, goods_code in all_keys:
        left_value = left_summary.get((warehouse_code, goods_code), Decimal("0"))
        right_value = right_summary.get((warehouse_code, goods_code), Decimal("0"))
        diff = left_value - right_value
        rows.append(
            {
                "warehouse_code": warehouse_code,
                "goods_code": goods_code,
                "fms_num": str(left_value),
                "iom_num": str(right_value),
                "diff_num": str(diff),
                "message": "一致" if diff == 0 else "数量不一致",
            }
        )
        if diff != 0:
            diff_pairs.append((warehouse_code, goods_code))
    return rows, diff_pairs


def fetch_left_detail(conn, start_time: str, end_time: str, pairs: Sequence[Tuple[str, str]], batch_size: int) -> Dict[DETAIL_KEY, Decimal]:
    return get_fms_dataset(conn, sys.modules[__name__], "return_income", start_time, end_time).detail(pairs)

def fetch_right_detail(conn, start_time: str, end_time: str, pairs: Sequence[Tuple[str, str]], batch_size: int) -> Dict[DETAIL_KEY, Decimal]:
    status_placeholders = ", ".join(["%s"] * len(ORDER_STATUSES))
    base_sql = (
        "SELECT "
        "a.return_order_id AS business_code, "
        "a.goods_code AS goods_code, "
        "SUM(a.arrive_num + a.arrive_imperfect_num) AS total_num "
        "FROM erp_iom.return_order_detail a "
        "LEFT JOIN erp_iom.return_order b ON a.return_order_id = b.return_order_id "
        "WHERE b.arrive_time BETWEEN %s AND %s "
        f"AND b.order_status IN ({status_placeholders}) "
    )

    result: Dict[DETAIL_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(b.warehouse_code, '')", "a.goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY a.return_order_id, a.goods_code"
            params: List[str] = [start_time, end_time] + ORDER_STATUSES + pair_params
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                key = (str(row["business_code"]), str(row["goods_code"]))
                result[key] = to_decimal(row["total_num"])
    return result


def fetch_iom_order_meta(conn, business_codes: Sequence[str]) -> Dict[str, Dict[str, str]]:
    """查询 IOM 退货单主表信息，用于补充失败原因"""
    if not business_codes:
        return {}

    result: Dict[str, Dict[str, str]] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(business_codes), 200):
            placeholders = ", ".join(["%s"] * len(batch))
            sql = (
                "SELECT "
                "return_order_id, "
                "warehouse_code, "
                "order_status, "
                "arrive_time "
                "FROM erp_iom.return_order "
                f"WHERE return_order_id IN ({placeholders})"
            )
            cursor.execute(sql, list(batch))
            for row in cursor.fetchall():
                result[str(row["return_order_id"])] = {
                    "warehouse_code": str(row["warehouse_code"] or ""),
                    "order_status": str(row["order_status"] if row["order_status"] is not None else ""),
                    "arrive_time": str(row["arrive_time"] or ""),
                }
    return result


def describe_return_income_failure(
    business_code: str,
    left_value: Decimal,
    right_value: Decimal,
    iom_order_meta: Dict[str, Dict[str, str]],
    start_time: str,
    end_time: str,
) -> str:
    """生成退货应收入库单的业务化失败原因"""
    if left_value != 0 and right_value == 0:
        meta = iom_order_meta.get(business_code)
        if not meta:
            return "FMS有，IOM无此单号"

        reasons: List[str] = []
        status = meta.get("order_status", "")
        arrive_time = meta.get("arrive_time", "")
        if status and status not in ORDER_STATUSES:
            reasons.append(f"order_status={status} 未命中 IOM 状态条件")
        if arrive_time.startswith("1970-01-01"):
            reasons.append(f"arrive_time={arrive_time} 仍为默认值")
        elif arrive_time and not (start_time <= arrive_time <= end_time):
            reasons.append(f"arrive_time={arrive_time} 未命中当前时间范围")
        if reasons:
            return "；".join(reasons)
        return "FMS有，IOM无"

    if left_value == 0 and right_value != 0:
        return "IOM有，FMS无"

    return "FMS与IOM数量不一致"


def build_detail_rows(
    left_detail: Dict[DETAIL_KEY, Decimal],
    right_detail: Dict[DETAIL_KEY, Decimal],
    iom_order_meta: Dict[str, Dict[str, str]],
    start_time: str,
    end_time: str,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    all_keys = sorted(set(left_detail.keys()) | set(right_detail.keys()))
    for business_code, goods_code in all_keys:
        left_value = left_detail.get((business_code, goods_code), Decimal("0"))
        right_value = right_detail.get((business_code, goods_code), Decimal("0"))
        diff = left_value - right_value
        if diff == 0:
            continue
        failure_reason = describe_return_income_failure(
            business_code=business_code,
            left_value=left_value,
            right_value=right_value,
            iom_order_meta=iom_order_meta,
            start_time=start_time,
            end_time=end_time,
        )
        rows.append(
            {
                "business_code": business_code,
                "goods_code": goods_code,
                "fms_num": str(left_value),
                "iom_num": str(right_value),
                "diff_num": str(diff),
                "message": "单据数量不一致",
                "failure_reason": failure_reason,
            }
        )
    return rows


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="退货应收入库单核对工具")
    parser.add_argument("--start-time", required=True, type=parse_datetime, help="开始时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end-time", required=True, type=parse_datetime, help="结束时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument(
        "--summary-output",
        default=os.path.join(DESKTOP_DIR, "return_income_summary.csv"),
        help="汇总对比输出文件",
    )
    parser.add_argument(
        "--detail-output",
        default=os.path.join(DESKTOP_DIR, "return_income_detail.csv"),
        help="单据差异输出文件",
    )
    parser.add_argument("--source-audit-output", help="跨来源重复与冲突明细文件")
    parser.add_argument("--batch-size", type=int, default=100, help="差异组合分批查询大小")
    return parser.parse_args()


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    load_known_dotenvs(script_dir)
    args = parse_args()

    host = env_required("DB_HOST")
    port = int(os.getenv("DB_PORT", "3306"))
    user = env_required("DB_USER")
    password = env_required("DB_PASSWORD")
    database = os.getenv("DB_NAME", "").strip()

    conn_kwargs = {
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
        conn_kwargs["database"] = database

    conn = pymysql.connect(**conn_kwargs)
    try:
        run_reconciliation(sys.modules[__name__], conn, args, "return_income")
    finally:
        close_fms_dataset(conn)
        conn.close()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    main()
