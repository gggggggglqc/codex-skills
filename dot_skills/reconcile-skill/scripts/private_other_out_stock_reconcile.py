#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
其他出库日志 vs IMC 出库数据核对工具

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
from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少依赖 pymysql，请先安装后再运行。") from exc


PSI_GROUP_TYPES: List[str] = [
    "301",
    "302",
    "303",
    "304",
    "309",
    "310",
    "311",
    "312",
    "326",
    "332",
    "334",
    "335",
    "336",
    "339",
    "701",
    "702",
    "703",
    "704",
    "705",
    "706",
    "707",
    "708",
    "709",
    "710",
    "724",
    "726",
    "727",
    "728",
    "729",
    "730",
    "732",
    "733",
    "739",
    "742",
    "743",
    "744",
]
ORDER_TYPES: List[str] = ["1", "3", "4", "12", "14", "15", "16", "18"]
SUMMARY_KEY = Tuple[str, str]
DETAIL_KEY = Tuple[str, str]
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")


def parse_datetime(value: str) -> str:
    """校验时间参数格式"""
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"非法时间格式: {value}，请使用 YYYY-MM-DD HH:MM:SS") from exc
    return value


def env_required(name: str) -> str:
    """读取必需环境变量"""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"缺少环境变量: {name}")
    return value


def load_dotenv(path: str) -> None:
    """从 .env 文件读取环境变量"""
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
    """按固定顺序尝试加载 .env，兼容 skill 目录和项目目录"""
    candidate_paths = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.path.dirname(script_dir), ".env"),
        r"D:\codex\codex-file-organizer\.env",
    ]
    for path in candidate_paths:
        load_dotenv(path)


def to_decimal(value) -> Decimal:
    """统一转 Decimal，避免精度问题"""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def chunked(items: Sequence, size: int) -> Iterable[Sequence]:
    """按固定大小切分列表"""
    for index in range(0, len(items), size):
        yield items[index:index + size]


def build_pair_filter(alias_warehouse: str, alias_goods: str, pairs: Sequence[Tuple[str, str]]) -> Tuple[str, List[str]]:
    """构造 仓库+商品编码 过滤条件"""
    clauses: List[str] = []
    params: List[str] = []
    for warehouse_code, goods_code in pairs:
        clauses.append(f"({alias_warehouse} = %s AND {alias_goods} = %s)")
        params.extend([warehouse_code, goods_code])
    return " OR ".join(clauses), params


def fetch_left_summary(conn, start_time: str, end_time: str) -> Dict[SUMMARY_KEY, Decimal]:
    """查询 FMS 左侧汇总（原其他出入库 + 工厂其他出入库）"""
    placeholders = ", ".join(["%s"] * len(PSI_GROUP_TYPES))
    sql_legacy = (
        "SELECT "
        "COALESCE(bb.out_stock_warehouse_code, '') AS warehouse_code, "
        "aa.sku_code AS goods_code, "
        "SUM(aa.num) AS total_num "
        "FROM fms_cost.psi_other_stock_record_detail aa "
        "LEFT JOIN fms_cost.psi_other_stock_record bb ON aa.stock_id = bb.id "
        "WHERE bb.business_date BETWEEN %s AND %s "
        f"AND bb.psi_group_type IN ({placeholders}) "
        "GROUP BY COALESCE(bb.out_stock_warehouse_code, ''), aa.sku_code"
    )
    sql_factory = (
        "SELECT "
        "COALESCE(bb.out_stock_warehouse_code, '') AS warehouse_code, "
        "aa.code AS goods_code, "
        "SUM(aa.num) AS total_num "
        "FROM fms_cost.psi_factory_other_stock_record_detail aa "
        "LEFT JOIN fms_cost.psi_factory_other_stock_record bb ON aa.stock_id = bb.id "
        "WHERE bb.business_date BETWEEN %s AND %s "
        f"AND bb.psi_group_type IN ({placeholders}) "
        "GROUP BY COALESCE(bb.out_stock_warehouse_code, ''), aa.code"
    )
    params: List[str] = [start_time, end_time] + PSI_GROUP_TYPES
    result: Dict[SUMMARY_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for sql in (sql_legacy, sql_factory):
            cursor.execute(sql, params)
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
) -> Dict[SUMMARY_KEY, Decimal]:
    """查询 WMS 出库汇总，可选按差异组合过滤"""
    order_placeholders = ", ".join(["%s"] * len(ORDER_TYPES))
    base_sql = (
        "SELECT "
        "COALESCE(bb.warehouse_code, '') AS warehouse_code, "
        "aa.goods_code AS goods_code, "
        "SUM(CASE "
        "WHEN bb.order_type = '18' THEN "
        "(aa.arrive_num + aa.arrive_defective_num - aa.actual_num - aa.defective_actual_num) "
        "ELSE (aa.actual_num + aa.defective_actual_num) "
        "END) AS total_num "
        "FROM erp_iom.stock_order_detail aa "
        "LEFT JOIN erp_iom.stock_order bb ON aa.stock_order_code = bb.stock_order_code "
        "LEFT JOIN erp_iom.allocation cc ON bb.source_order_id = cc.allocation_order_id "
        "LEFT JOIN oms_product.warehouse w ON bb.warehouse_code = w.warehouse_code "
        "WHERE bb.order_type IN ({order_types}) "
        "AND bb.billing_time BETWEEN %s AND %s "
        "AND bb.in_out_type = '2' "
        "AND (cc.allot_type IS NULL OR cc.allot_type <> 1) "
        "AND (w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR bb.warehouse_code IN ('WH0882','WH0388','WH0390','WH0237','WH0494')) "
        "AND NOT (bb.order_type = '1' AND bb.reason = '13') "
    ).format(order_types=order_placeholders)

    result: Dict[SUMMARY_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        if not pairs:
            sql = base_sql + "GROUP BY COALESCE(bb.warehouse_code, ''), aa.goods_code"
            cursor.execute(sql, ORDER_TYPES + [start_time, end_time])
            for row in cursor.fetchall():
                key = (str(row["warehouse_code"]), str(row["goods_code"]))
                result[key] = to_decimal(row["total_num"])
            return result

        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(bb.warehouse_code, '')", "aa.goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY COALESCE(bb.warehouse_code, ''), aa.goods_code"
            params: List[str] = ORDER_TYPES + [start_time, end_time] + pair_params
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                key = (str(row["warehouse_code"]), str(row["goods_code"]))
                result[key] = to_decimal(row["total_num"])
    return result


def build_summary_rows(
    left_summary: Dict[SUMMARY_KEY, Decimal],
    right_summary: Dict[SUMMARY_KEY, Decimal],
) -> Tuple[List[Dict[str, str]], List[Tuple[str, str]]]:
    """构造汇总对比结果，并返回有差异的键"""
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
                "fms_cost_num": str(left_value),
                "erp_iom_num": str(right_value),
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
) -> Dict[DETAIL_KEY, Decimal]:
    """查询 FMS 左侧差异明细（原其他出入库 + 工厂其他出入库）"""
    placeholders = ", ".join(["%s"] * len(PSI_GROUP_TYPES))
    base_sql_legacy = (
        "SELECT "
        "bb.business_code AS business_code, "
        "aa.sku_code AS goods_code, "
        "SUM(aa.num) AS total_num "
        "FROM fms_cost.psi_other_stock_record_detail aa "
        "LEFT JOIN fms_cost.psi_other_stock_record bb ON aa.stock_id = bb.id "
        "WHERE bb.business_date BETWEEN %s AND %s "
        f"AND bb.psi_group_type IN ({placeholders}) "
    )
    base_sql_factory = (
        "SELECT "
        "bb.business_code AS business_code, "
        "aa.code AS goods_code, "
        "SUM(aa.num) AS total_num "
        "FROM fms_cost.psi_factory_other_stock_record_detail aa "
        "LEFT JOIN fms_cost.psi_factory_other_stock_record bb ON aa.stock_id = bb.id "
        "WHERE bb.business_date BETWEEN %s AND %s "
        f"AND bb.psi_group_type IN ({placeholders}) "
    )
    result: Dict[DETAIL_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(pairs), batch_size):
            pair_filter_legacy, pair_params_legacy = build_pair_filter(
                "COALESCE(bb.out_stock_warehouse_code, '')", "aa.sku_code", batch
            )
            sql_legacy = base_sql_legacy + f"AND ({pair_filter_legacy}) GROUP BY bb.business_code, aa.sku_code"
            params_legacy: List[str] = [start_time, end_time] + PSI_GROUP_TYPES + pair_params_legacy
            cursor.execute(sql_legacy, params_legacy)
            for row in cursor.fetchall():
                key = (str(row["business_code"]), str(row["goods_code"]))
                result[key] = result.get(key, Decimal("0")) + to_decimal(row["total_num"])

            pair_filter_factory, pair_params_factory = build_pair_filter(
                "COALESCE(bb.out_stock_warehouse_code, '')", "aa.code", batch
            )
            sql_factory = base_sql_factory + f"AND ({pair_filter_factory}) GROUP BY bb.business_code, aa.code"
            params_factory: List[str] = [start_time, end_time] + PSI_GROUP_TYPES + pair_params_factory
            cursor.execute(sql_factory, params_factory)
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
) -> Dict[DETAIL_KEY, Decimal]:
    """查询右侧差异组合下的单据明细"""
    order_placeholders = ", ".join(["%s"] * len(ORDER_TYPES))
    base_sql = (
        "SELECT "
        "aa.stock_order_code AS business_code, "
        "aa.goods_code AS goods_code, "
        "SUM(CASE "
        "WHEN bb.order_type = '18' THEN "
        "(aa.arrive_num + aa.arrive_defective_num - aa.actual_num - aa.defective_actual_num) "
        "ELSE (aa.actual_num + aa.defective_actual_num) "
        "END) AS total_num "
        "FROM erp_iom.stock_order_detail aa "
        "LEFT JOIN erp_iom.stock_order bb ON aa.stock_order_code = bb.stock_order_code "
        "LEFT JOIN erp_iom.allocation cc ON bb.source_order_id = cc.allocation_order_id "
        "LEFT JOIN oms_product.warehouse w ON bb.warehouse_code = w.warehouse_code "
        "WHERE bb.order_type IN ({order_types}) "
        "AND bb.billing_time BETWEEN %s AND %s "
        "AND bb.in_out_type = '2' "
        "AND (cc.allot_type IS NULL OR cc.allot_type <> 1) "
        "AND (w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR bb.warehouse_code IN ('WH0882','WH0388','WH0390','WH0237','WH0494')) "
        "AND NOT (bb.order_type = '1' AND bb.reason = '13') "
    ).format(order_types=order_placeholders)

    result: Dict[DETAIL_KEY, Decimal] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(pairs), batch_size):
            pair_filter, pair_params = build_pair_filter("COALESCE(bb.warehouse_code, '')", "aa.goods_code", batch)
            sql = base_sql + f"AND ({pair_filter}) GROUP BY aa.stock_order_code, aa.goods_code"
            params: List[str] = ORDER_TYPES + [start_time, end_time] + pair_params
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                key = (str(row["business_code"]), str(row["goods_code"]))
                result[key] = to_decimal(row["total_num"])
    return result


def fetch_iom_order_meta(conn, business_codes: Sequence[str]) -> Dict[str, Dict[str, str]]:
    """查询 IOM 单据主信息，用于补充失败原因"""
    if not business_codes:
        return {}

    result: Dict[str, Dict[str, str]] = {}
    with conn.cursor() as cursor:
        for batch in chunked(list(business_codes), 200):
            placeholders = ", ".join(["%s"] * len(batch))
            sql = (
                "SELECT "
                "bb.stock_order_code, "
                "bb.in_out_type, "
                "bb.order_type, "
                "bb.reason, "
                "bb.warehouse_code, "
                "bb.billing_time, "
                "COALESCE(cc.allot_type, '') AS allot_type, "
                "COALESCE(w.warehouse_use_type, '') AS warehouse_use_type "
                "FROM erp_iom.stock_order bb "
                "LEFT JOIN erp_iom.allocation cc ON bb.source_order_id = cc.allocation_order_id "
                "LEFT JOIN oms_product.warehouse w ON bb.warehouse_code = w.warehouse_code "
                f"WHERE bb.stock_order_code IN ({placeholders})"
            )
            cursor.execute(sql, list(batch))
            for row in cursor.fetchall():
                result[str(row["stock_order_code"])] = {
                    "in_out_type": str(row["in_out_type"] if row["in_out_type"] is not None else ""),
                    "order_type": str(row["order_type"] if row["order_type"] is not None else ""),
                    "reason": str(row["reason"] if row["reason"] is not None else ""),
                    "warehouse_code": str(row["warehouse_code"] or ""),
                    "billing_time": str(row["billing_time"] or ""),
                    "allot_type": str(row["allot_type"] or ""),
                    "warehouse_use_type": str(row["warehouse_use_type"] or ""),
                }
    return result


def describe_other_out_failure(
    business_code: str,
    left_value: Decimal,
    right_value: Decimal,
    iom_order_meta: Dict[str, Dict[str, str]],
    start_time: str,
    end_time: str,
) -> str:
    """生成其他出库核对的业务化失败原因"""
    if left_value != 0 and right_value == 0:
        meta = iom_order_meta.get(business_code)
        if not meta:
            return "FMS有，IOM无此单号"

        reasons: List[str] = []
        billing_time = meta.get("billing_time", "")
        warehouse_code = meta.get("warehouse_code", "")
        warehouse_use_type = meta.get("warehouse_use_type", "")
        allot_type = meta.get("allot_type", "")
        in_out_type = meta.get("in_out_type", "")
        order_type = meta.get("order_type", "")
        reason = meta.get("reason", "")

        if billing_time and not (start_time <= billing_time <= end_time):
            reasons.append(f"billing_time={billing_time} 未命中当前时间范围")
        if allot_type == "1":
            reasons.append("命中仓内调拨过滤")
        if warehouse_use_type == "2" and warehouse_code not in {"WH0882", "WH0388", "WH0390", "WH0237", "WH0494"}:
            reasons.append(f"warehouse_code={warehouse_code} 命中代发仓过滤")
        if order_type == "1" and reason == "13":
            reasons.append("order_type=1 且 reason=13 被其他出库排除规则过滤")
        if not (in_out_type == "2" and order_type in ORDER_TYPES):
            reasons.append(f"in_out_type={in_out_type}, order_type={order_type} 未命中其他出库核对范围")

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
    """构造单据差异结果"""
    rows: List[Dict[str, str]] = []
    all_keys = sorted(set(left_detail.keys()) | set(right_detail.keys()))
    for business_code, goods_code in all_keys:
        left_value = left_detail.get((business_code, goods_code), Decimal("0"))
        right_value = right_detail.get((business_code, goods_code), Decimal("0"))
        diff = left_value - right_value
        if diff == 0:
            continue
        failure_reason = describe_other_out_failure(
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
                "fms_cost_num": str(left_value),
                "erp_iom_num": str(right_value),
                "diff_num": str(diff),
                "message": "单据数量不一致",
                "failure_reason": failure_reason,
            }
        )
    return rows


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """写 CSV 文件"""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="其他出库 vs IMC 核对工具")
    parser.add_argument("--start-time", required=True, type=parse_datetime, help="开始时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--end-time", required=True, type=parse_datetime, help="结束时间，格式 YYYY-MM-DD HH:MM:SS")
    parser.add_argument(
        "--summary-output",
        default=os.path.join(DESKTOP_DIR, "summary_compare.csv"),
        help="汇总对比输出文件",
    )
    parser.add_argument(
        "--detail-output",
        default=os.path.join(DESKTOP_DIR, "detail_diff.csv"),
        help="单据差异输出文件",
    )
    parser.add_argument("--batch-size", type=int, default=100, help="差异组合分批查询大小")
    return parser.parse_args()


def main() -> None:
    """主入口"""
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
        left_summary = fetch_left_summary(conn, args.start_time, args.end_time)
        right_summary = fetch_right_summary(conn, args.start_time, args.end_time)
        summary_rows, diff_pairs = build_summary_rows(left_summary, right_summary)

        detail_rows: List[Dict[str, str]] = []
        if diff_pairs:
            left_detail = fetch_left_detail(conn, args.start_time, args.end_time, diff_pairs, args.batch_size)
            right_detail = fetch_right_detail(conn, args.start_time, args.end_time, diff_pairs, args.batch_size)
            iom_order_meta = fetch_iom_order_meta(conn, sorted({business_code for business_code, _ in set(left_detail.keys()) | set(right_detail.keys())}))
            detail_rows = build_detail_rows(left_detail, right_detail, iom_order_meta, args.start_time, args.end_time)
    finally:
        conn.close()

    write_csv(
        args.summary_output,
        summary_rows,
        ["warehouse_code", "goods_code", "fms_cost_num", "erp_iom_num", "diff_num", "message"],
    )
    write_csv(
        args.detail_output,
        detail_rows,
        ["business_code", "goods_code", "fms_cost_num", "erp_iom_num", "diff_num", "message", "failure_reason"],
    )

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














