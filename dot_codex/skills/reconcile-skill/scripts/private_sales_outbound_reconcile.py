#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
销售出库核对工具（FMS vs IOM）

核对流程：
1. 按 出库仓库 + 商品编码 汇总比对数量
2. 仅对汇总有差异的组合，继续下钻到 单号 + 商品编码
3. 支持命令行输入开始/结束时间
4. 输出汇总对比与单据差异 CSV
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少依赖 pymysql，请先安装后再运行。") from exc


SUMMARY_KEY = Tuple[str, str]
DETAIL_KEY = Tuple[str, str]
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
PSI_GROUP_TYPES: List[str] = [
    "142",
    "120",
    "102",
    "141",
    "140",
    "137",
    "135",
    "118",
    "117",
    "113",
    "108",
    "110",
    "148",
    "149",
    "169",
    "170",
    "171",
    "172",
    "106",
]
WHITELIST_WAREHOUSES = {"WH0882", "WH0388", "WH0390", "WH0237", "WH0494"}


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


def to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def chunked(items: Sequence, size: int) -> Iterable[Sequence]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def split_datetime_range(start_time: str, end_time: str, day_batch_size: int) -> List[Tuple[str, str]]:
    """按天切分时间范围，避免单条 SQL 扫描过大"""
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    ranges: List[Tuple[str, str]] = []
    current = start_dt
    while current <= end_dt:
        batch_end = min(
            datetime.combine((current + timedelta(days=day_batch_size - 1)).date(), datetime.max.time()).replace(microsecond=0),
            end_dt,
        )
        ranges.append(
            (
                current.strftime("%Y-%m-%d %H:%M:%S"),
                batch_end.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        current = batch_end + timedelta(seconds=1)
    return ranges


def build_pair_filter(alias_warehouse: str, alias_goods: str, pairs: Sequence[Tuple[str, str]]) -> Tuple[str, List[str]]:
    clauses: List[str] = []
    params: List[str] = []
    for warehouse_code, goods_code in pairs:
        clauses.append(f"({alias_warehouse} = %s AND {alias_goods} = %s)")
        params.extend([warehouse_code, goods_code])
    return " OR ".join(clauses), params


def fetch_left_summary(conn, start_time: str, end_time: str, day_batch_size: int) -> Dict[SUMMARY_KEY, Decimal]:
    placeholders = ", ".join(["%s"] * len(PSI_GROUP_TYPES))
    sql = (
        "SELECT "
        "COALESCE(out_warehouse_code, '') AS warehouse_code, "
        "goods_code AS goods_code, "
        "SUM(actual_num) AS total_num "
        "FROM fms_cost.psi_sales "
        "LEFT JOIN oms_product.warehouse w ON psi_sales.out_warehouse_code = w.warehouse_code "
        "WHERE business_date BETWEEN %s AND %s "
        f"AND psi_group_type IN ({placeholders}) "
        "AND (w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR psi_sales.out_warehouse_code IN ('WH0882','WH0388','WH0390','WH0237','WH0494')) "
        "GROUP BY COALESCE(out_warehouse_code, ''), goods_code"
    )
    result: Dict[SUMMARY_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for range_start, range_end in split_datetime_range(start_time, end_time, day_batch_size):
            cursor.execute(sql, [range_start[:10], range_end[:10]] + PSI_GROUP_TYPES)
            for row in cursor.fetchall():
                key = (str(row["warehouse_code"]), str(row["goods_code"]))
                result[key] = result.get(key, Decimal("0")) + to_decimal(row["total_num"])
    return result


def fetch_right_summary(
    conn,
    start_time: str,
    end_time: str,
    pairs: Sequence[Tuple[str, str]] | None = None,
    batch_size: int = 100,
    day_batch_size: int = 1,
) -> Dict[SUMMARY_KEY, Decimal]:
    base_sql = (
        "SELECT "
        "COALESCE(d.warehouse_code, '') AS warehouse_code, "
        "s.goods_code AS goods_code, "
        "SUM(s.goods_num) AS total_num "
        "FROM erp_iom.sub_delivery_order s "
        "LEFT JOIN erp_iom.delivery_order d ON s.delivery_order_id = d.delivery_order_id "
        "LEFT JOIN oms_product.warehouse w ON d.warehouse_code = w.warehouse_code "
        "WHERE d.warehouse_delivery_time BETWEEN %s AND %s "
        "AND d.order_status = 7 "
        "AND (w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR d.warehouse_code IN ('WH0882','WH0388','WH0390','WH0237','WH0494')) "
    )
    result: Dict[SUMMARY_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        if not pairs:
            sql = base_sql + "GROUP BY COALESCE(d.warehouse_code, ''), s.goods_code"
            for range_start, range_end in split_datetime_range(start_time, end_time, day_batch_size):
                cursor.execute(sql, [range_start, range_end])
                for row in cursor.fetchall():
                    key = (str(row["warehouse_code"]), str(row["goods_code"]))
                    result[key] = result.get(key, Decimal("0")) + to_decimal(row["total_num"])
            return result

        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(d.warehouse_code, '')", "s.goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY COALESCE(d.warehouse_code, ''), s.goods_code"
            for range_start, range_end in split_datetime_range(start_time, end_time, day_batch_size):
                cursor.execute(sql, [range_start, range_end] + pair_params)
                for row in cursor.fetchall():
                    key = (str(row["warehouse_code"]), str(row["goods_code"]))
                    result[key] = result.get(key, Decimal("0")) + to_decimal(row["total_num"])
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


def fetch_left_detail(
    conn,
    start_time: str,
    end_time: str,
    pairs: Sequence[Tuple[str, str]],
    batch_size: int,
    day_batch_size: int,
) -> Dict[DETAIL_KEY, Decimal]:
    placeholders = ", ".join(["%s"] * len(PSI_GROUP_TYPES))
    base_sql = (
        "SELECT "
        "business_code AS business_code, "
        "goods_code AS goods_code, "
        "SUM(actual_num) AS total_num "
        "FROM fms_cost.psi_sales "
        "LEFT JOIN oms_product.warehouse w ON psi_sales.out_warehouse_code = w.warehouse_code "
        "WHERE business_date BETWEEN %s AND %s "
        f"AND psi_group_type IN ({placeholders}) "
        "AND (w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR psi_sales.out_warehouse_code IN ('WH0882','WH0388','WH0390','WH0237','WH0494')) "
    )
    result: Dict[DETAIL_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(out_warehouse_code, '')", "goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY business_code, goods_code"
            for range_start, range_end in split_datetime_range(start_time, end_time, day_batch_size):
                cursor.execute(sql, [range_start[:10], range_end[:10]] + PSI_GROUP_TYPES + pair_params)
                for row in cursor.fetchall():
                    key = (str(row["business_code"]), str(row["goods_code"]))
                    result[key] = result.get(key, Decimal("0")) + to_decimal(row["total_num"])
    return result


def fetch_right_detail(
    conn,
    start_time: str,
    end_time: str,
    pairs: Sequence[Tuple[str, str]],
    batch_size: int,
    day_batch_size: int,
) -> Dict[DETAIL_KEY, Decimal]:
    base_sql = (
        "SELECT "
        "d.order_id AS business_code, "
        "s.goods_code AS goods_code, "
        "SUM(s.goods_num) AS total_num "
        "FROM erp_iom.sub_delivery_order s "
        "LEFT JOIN erp_iom.delivery_order d ON s.delivery_order_id = d.delivery_order_id "
        "LEFT JOIN oms_product.warehouse w ON d.warehouse_code = w.warehouse_code "
        "WHERE d.warehouse_delivery_time BETWEEN %s AND %s "
        "AND d.order_status = 7 "
        "AND (w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR d.warehouse_code IN ('WH0882','WH0388','WH0390','WH0237','WH0494')) "
    )
    result: Dict[DETAIL_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(d.warehouse_code, '')", "s.goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY d.order_id, s.goods_code"
            for range_start, range_end in split_datetime_range(start_time, end_time, day_batch_size):
                cursor.execute(sql, [range_start, range_end] + pair_params)
                for row in cursor.fetchall():
                    key = (str(row["business_code"]), str(row["goods_code"]))
                    result[key] = result.get(key, Decimal("0")) + to_decimal(row["total_num"])
    return result


def fetch_iom_order_meta(conn, business_codes: Sequence[str]) -> Dict[str, Dict[str, str]]:
    if not business_codes:
        return {}
    result: Dict[str, Dict[str, str]] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(business_codes), 200):
            placeholders = ", ".join(["%s"] * len(batch))
            sql = (
                "SELECT "
                "d.order_id, "
                "d.order_status, "
                "d.warehouse_code, "
                "d.warehouse_delivery_time, "
                "COALESCE(w.warehouse_use_type, '') AS warehouse_use_type "
                "FROM erp_iom.delivery_order d "
                "LEFT JOIN oms_product.warehouse w ON d.warehouse_code = w.warehouse_code "
                f"WHERE d.order_id IN ({placeholders})"
            )
            cursor.execute(sql, list(batch))
            for row in cursor.fetchall():
                result[str(row["order_id"])] = {
                    "order_status": str(row["order_status"] if row["order_status"] is not None else ""),
                    "warehouse_code": str(row["warehouse_code"] or ""),
                    "warehouse_delivery_time": str(row["warehouse_delivery_time"] or ""),
                    "warehouse_use_type": str(row["warehouse_use_type"] or ""),
                }
    return result


def describe_failure(
    business_code: str,
    left_value: Decimal,
    right_value: Decimal,
    iom_order_meta: Dict[str, Dict[str, str]],
    start_time: str,
    end_time: str,
) -> str:
    if left_value != 0 and right_value == 0:
        meta = iom_order_meta.get(business_code)
        if not meta:
            return "FMS有，IOM无此单号"

        reasons: List[str] = []
        order_status = meta.get("order_status", "")
        warehouse_code = meta.get("warehouse_code", "")
        warehouse_delivery_time = meta.get("warehouse_delivery_time", "")
        warehouse_use_type = meta.get("warehouse_use_type", "")

        if order_status and order_status != "7":
            reasons.append(f"order_status={order_status} 未命中已完成条件")
        if warehouse_delivery_time and not (start_time <= warehouse_delivery_time <= end_time):
            reasons.append(f"warehouse_delivery_time={warehouse_delivery_time} 未命中当前时间范围")
        if warehouse_use_type == "2" and warehouse_code not in WHITELIST_WAREHOUSES:
            reasons.append(f"warehouse_code={warehouse_code} 命中代发仓过滤")

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
        rows.append(
            {
                "business_code": business_code,
                "goods_code": goods_code,
                "fms_num": str(left_value),
                "iom_num": str(right_value),
                "diff_num": str(diff),
                "message": "单据数量不一致",
                "failure_reason": describe_failure(business_code, left_value, right_value, iom_order_meta, start_time, end_time),
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
    parser = argparse.ArgumentParser(description="销售出库核对工具")
    parser.add_argument("--start-time", required=True, type=parse_datetime, help="开始时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end-time", required=True, type=parse_datetime, help="结束时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument(
        "--summary-output",
        default=os.path.join(DESKTOP_DIR, "sales_outbound_summary.csv"),
        help="汇总对比输出文件",
    )
    parser.add_argument(
        "--detail-output",
        default=os.path.join(DESKTOP_DIR, "sales_outbound_detail.csv"),
        help="单据差异输出文件",
    )
    parser.add_argument("--batch-size", type=int, default=100, help="差异组合分批查询大小")
    parser.add_argument("--day-batch-size", type=int, default=1, help="按多少天一批查询汇总和明细")
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
        left_summary = fetch_left_summary(conn, args.start_time, args.end_time, args.day_batch_size)
        right_summary = fetch_right_summary(conn, args.start_time, args.end_time, day_batch_size=args.day_batch_size)
        summary_rows, diff_pairs = build_summary_rows(left_summary, right_summary)

        detail_rows: List[Dict[str, str]] = []
        if diff_pairs:
            left_detail = fetch_left_detail(conn, args.start_time, args.end_time, diff_pairs, args.batch_size, args.day_batch_size)
            right_detail = fetch_right_detail(conn, args.start_time, args.end_time, diff_pairs, args.batch_size, args.day_batch_size)
            iom_order_meta = fetch_iom_order_meta(conn, sorted({business_code for business_code, _ in set(left_detail.keys()) | set(right_detail.keys())}))
            detail_rows = build_detail_rows(left_detail, right_detail, iom_order_meta, args.start_time, args.end_time)
    finally:
        conn.close()

    write_csv(args.summary_output, summary_rows, ["warehouse_code", "goods_code", "fms_num", "iom_num", "diff_num", "message"])
    write_csv(args.detail_output, detail_rows, ["business_code", "goods_code", "fms_num", "iom_num", "diff_num", "message", "failure_reason"])

    print(
        f"核对完成，时间范围 {args.start_time} 到 {args.end_time}，"
        f"汇总对比 {len(summary_rows)} 行，"
        f"汇总差异组合 {len(diff_pairs)} 个，"
        f"单据差异 {len(detail_rows)} 条"
    )
    print(f"汇总文件: {args.summary_output}")
    print(f"单据差异文件: {args.detail_output}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    main()
