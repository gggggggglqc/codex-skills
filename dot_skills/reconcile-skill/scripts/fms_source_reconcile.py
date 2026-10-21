#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""六类核对共用的 FMS 跨来源处理；汇总和明细读取同一次取数快照。"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import groupby
from pathlib import Path

from pymysql.cursors import SSDictCursor


ZERO = Decimal("0")
WHITELIST = ("WH0882", "WH0388", "WH0390", "WH0237", "WH0494", "WH0979")
SOURCE_TABLES = {
    "purchase": ("psi_purchase_record", "psi_factory_purchase_record"),
    "other_in": ("psi_other_stock_record", "psi_factory_other_stock_record"),
    "other_out": ("psi_other_stock_record", "psi_factory_other_stock_record"),
    "no_order_return": ("psi_sales", "psi_factory_sales"),
    "return_income": ("psi_sales", "psi_factory_sales"),
    "sales_outbound": ("psi_sales", "psi_factory_sales"),
}


def _text(value):
    # 编码保留大小写与前导零，不对单号做前缀猜测或转换。
    return "" if value is None else str(value)


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


class FmsDataset:
    """SQLite 只负责存储和排序；数量始终使用 Decimal，避免浮点误差。"""

    def __init__(self, kind):
        self.kind = kind
        self.temp_dir = tempfile.TemporaryDirectory(prefix="reconcile-fms-")
        self.db = sqlite3.connect(os.path.join(self.temp_dir.name, "sources.sqlite"))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE candidates (
                source TEXT, order_code TEXT, goods_code TEXT, direction TEXT,
                warehouse_code TEXT, unit_code TEXT, quantity TEXT,
                business_date TEXT, psi_group_type TEXT, ownership TEXT
            );
            CREATE TABLE effective (
                order_code TEXT, goods_code TEXT, direction TEXT,
                warehouse_code TEXT, unit_code TEXT, quantity TEXT
            );
            CREATE TABLE audits (
                order_code TEXT, goods_code TEXT, direction TEXT, decision TEXT,
                retained_source TEXT, failure_reason TEXT, common_records TEXT,
                factory_records TEXT, affected_pairs TEXT, blocking INTEGER
            );
        """)
        self.resolved = False

    def close(self):
        self.db.close()
        self.temp_dir.cleanup()

    def add(self, source, rows):
        self.db.executemany(
            "INSERT INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ((source, _text(r.get("order_code")), _text(r.get("goods_code")),
              _text(r.get("direction")), _text(r.get("warehouse_code")),
              _text(r.get("unit_code")),
              "" if r.get("total_num") is None else str(_decimal(r["total_num"])),
              _text(r.get("business_date")), _text(r.get("psi_group_type")),
              _text(r.get("ownership")) or "unknown") for r in rows),
        )

    @staticmethod
    def _distribution(records):
        values = defaultdict(lambda: ZERO)
        for r in records:
            values[(r["warehouse_code"], r["unit_code"])] += _decimal(r["quantity"])
        return dict(values)

    def resolve(self):
        if self.resolved:
            return
        self.db.execute("CREATE INDEX candidate_key ON candidates(order_code, goods_code, direction)")
        cursor = self.db.execute("SELECT * FROM candidates ORDER BY order_code, goods_code, direction")
        for key, group in groupby(cursor, lambda r: (r["order_code"], r["goods_code"], r["direction"])):
            records = [dict(r) for r in group]
            common = [r for r in records if r["source"] == "common"]
            factory = [r for r in records if r["source"] == "factory"]
            known_factory = any(r["ownership"] == "factory" for r in records)
            known_ordinary = any(r["ownership"] == "ordinary" for r in records)
            decision, reason, selected, blocking = "", "", [], False
            if not key[0] or not key[1] or not key[2]:
                decision, reason, blocking = "标识缺失", "单号、商品或出入库方向缺失，无法确认同一业务", True
            elif any(r["quantity"] == "" for r in records):
                decision, reason, blocking = "数量缺失", "来源数量为空，不能作为零数量处理", True
            elif any(r["warehouse_code"] == "" for r in records):
                decision, reason, blocking = "仓库缺失", "来源仓库编码为空，无法确认仓库下的数量", True
            elif known_factory and not factory:
                decision, reason, blocking = "产销来源缺失", "已命中产销归属，但当前时间和分组范围内缺少有效产销记录", True
            elif common and factory:
                a, b = self._distribution(common), self._distribution(factory)
                if a != b:
                    parts = []
                    if {w for w, u in a} != {w for w, u in b}:
                        parts.append("仓库不同")
                    if {u for w, u in a} != {u for w, u in b}:
                        parts.append("单位不同或无法对应")
                    if sum(a.values(), ZERO) != sum(b.values(), ZERO):
                        parts.append("数量不同")
                    decision, reason, blocking = "来源冲突", "；".join(parts) or "仓库或单位下的数量分布不同", True
                elif known_factory and known_ordinary:
                    decision, reason, blocking = "归属冲突", "相同业务命中了普通和产销两种组织归属", True
                else:
                    selected = factory if known_factory else common
                    decision = "跨来源重复"
                    if known_factory:
                        reason = "已确认属于产销，只计产销数量一次"
                    elif known_ordinary:
                        reason = "已确认属于普通业务，只计普通来源数量一次"
                    else:
                        reason = "同一业务数量和仓库单位分布相同，只计一次；归属待确认"
                    if {r["business_date"] for r in common} != {r["business_date"] for r in factory}:
                        reason += "；来源业务日期不同，保留两边日期供排查"
            else:
                selected = factory or common

            if selected:
                for (warehouse, unit), quantity in self._distribution(selected).items():
                    self.db.execute("INSERT INTO effective VALUES (?, ?, ?, ?, ?, ?)", (*key, warehouse, unit, str(quantity)))
            if decision:
                pairs = sorted({(r["warehouse_code"], r["goods_code"]) for r in records})
                self.db.execute(
                    "INSERT INTO audits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (*key, decision, selected[0]["source"] if selected else "", reason,
                     json.dumps(common, ensure_ascii=False), json.dumps(factory, ensure_ascii=False),
                     json.dumps(pairs, ensure_ascii=False), int(blocking)),
                )
        self.db.execute("CREATE INDEX effective_pair ON effective(warehouse_code, goods_code)")
        self.db.commit()
        self.resolved = True

    def summary(self):
        self.resolve()
        result = {}
        for r in self.db.execute("SELECT warehouse_code, goods_code, quantity FROM effective"):
            key = (r["warehouse_code"], r["goods_code"])
            result[key] = result.get(key, ZERO) + _decimal(r["quantity"])
        # 冲突来源不提供一个臆测数量，仍保留其仓库组合并标记待确认。
        for pairs in self.db.execute("SELECT affected_pairs FROM audits WHERE blocking = 1"):
            for pair in json.loads(pairs[0]):
                result.setdefault(tuple(pair), ZERO)
        return result

    def detail(self, pairs):
        self.resolve()
        result = {}
        for warehouse, goods in sorted(set(pairs)):
            for r in self.db.execute("SELECT order_code, goods_code, quantity FROM effective WHERE warehouse_code = ? AND goods_code = ?", (warehouse, goods)):
                key = (r["order_code"], r["goods_code"])
                result[key] = result.get(key, ZERO) + _decimal(r["quantity"])
        return result

    def blocking_issues(self):
        self.resolve()
        return [dict(r) for r in self.db.execute("SELECT * FROM audits WHERE blocking = 1")]

    def write_audit(self, path):
        self.resolve()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fields = ["reconcile_type", "order_code", "goods_code", "direction", "decision",
                  "retained_source", "failure_reason", "common_table", "factory_table",
                  "common_num", "factory_num", "common_warehouse_codes", "factory_warehouse_codes",
                  "common_unit_codes", "factory_unit_codes", "common_business_dates", "factory_business_dates",
                  "common_psi_group_types", "factory_psi_group_types",
                  "common_records", "factory_records"]
        tables = SOURCE_TABLES[self.kind]
        with open(path, "w", newline="", encoding="utf-8-sig") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for r in self.db.execute("SELECT * FROM audits ORDER BY order_code, goods_code, direction"):
                row = {f: r[f] for f in fields if f in r.keys()}
                row.update(reconcile_type=self.kind, common_table="fms_cost." + tables[0], factory_table="fms_cost." + tables[1])
                for source in ("common", "factory"):
                    records = json.loads(r[source + "_records"])
                    row[source + "_num"] = str(sum((_decimal(v["quantity"]) for v in records), ZERO)) if records and all(v["quantity"] != "" for v in records) else ""
                    for field, suffix in (("warehouse_code", "warehouse_codes"), ("unit_code", "unit_codes"),
                                          ("business_date", "business_dates"), ("psi_group_type", "psi_group_types")):
                        row[source + "_" + suffix] = ";".join(sorted({v[field] for v in records}))
                writer.writerow(row)


def _columns(conn, table):
    with conn.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM " + table)
        return {r["Field"] for r in cursor.fetchall()}


def _ownership_sql(warehouse_alias, shop=False, warehouse_route=True, factory_code=False):
    conditions = [f"{warehouse_alias}.warehouse_use_type = 4"] if warehouse_route else []
    if factory_code:
        conditions.append("COALESCE(r.factory_code, '') <> ''")
    ordinary = "FALSE"
    if shop:
        conditions.append("(COALESCE(st.department, '') LIKE '%%产销%%' AND COALESCE(st.department_attribute, 0) = 2)")
        ordinary = "COALESCE(st.department, '') <> ''"
    factory = " OR ".join(conditions) or "FALSE"
    return f"CASE WHEN {factory} THEN 'factory' WHEN {ordinary} THEN 'ordinary' ELSE 'unknown' END"


def _date_ranges(start, end, days):
    start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
    if start_dt > end_dt or days < 1:
        raise ValueError("开始时间不能晚于结束时间，分批天数必须大于零")
    while start_dt <= end_dt:
        finish = min(datetime.combine((start_dt + timedelta(days=days - 1)).date(), datetime.max.time()).replace(microsecond=0), end_dt)
        yield start_dt.strftime("%Y-%m-%d %H:%M:%S"), finish.strftime("%Y-%m-%d %H:%M:%S")
        start_dt = finish + timedelta(seconds=1)


def source_queries(conn, module, kind):
    """只映射各类型字段；时间、分组、数量和白名单沿用已确认口径。"""
    result = []
    for source, table in zip(("common", "factory"), SOURCE_TABLES[kind]):
        params = []
        filters = []
        if kind in ("sales_outbound", "return_income", "no_order_return"):
            alias = "ps"
            wh = "out_warehouse_code" if kind == "sales_outbound" else "in_warehouse_code"
            warehouse, goods, code = f"ps.{wh}", "ps.goods_code", "ps.business_code"
            quantity = "ps.actual_num" if kind == "sales_outbound" else "ps.refund_num"
            direction = "'out'" if kind == "sales_outbound" else "'in'"
            cols = _columns(conn, "fms_cost." + table)
            unit = "COALESCE(ps.unit_code, '')" if "unit_code" in cols else "''"
            from_sql = f"FROM fms_cost.{table} ps "
            factory_wh = warehouse if kind == "sales_outbound" else "COALESCE(NULLIF(ps.out_warehouse_code, ''), ps.in_warehouse_code)"
            from_sql += f"LEFT JOIN oms_product.warehouse w ON {factory_wh} = w.warehouse_code "
            from_sql += "LEFT JOIN oms_business.shop sh ON ps.shop_code = sh.shop_code LEFT JOIN oms_business.structure st ON sh.structure_id = st.id "
            ownership = _ownership_sql("w", shop=True)
            group_types = module.PSI_GROUP_TYPES if source == "common" else module.FACTORY_PSI_GROUP_TYPES
            filters.append("ps.psi_group_type IN (" + ", ".join(["%s"] * len(group_types)) + ")")
            params.extend(group_types)
            if source == "factory" or kind == "no_order_return":
                from_type = {"sales_outbound": 1, "return_income": 5, "no_order_return": 4}[kind]
                filters.append("ps.psi_data_from_type = %s")
                params.append(from_type)
            if kind != "sales_outbound":
                filters.append(f"{warehouse} != ''")
            else:
                # 两个来源都使用相同的代发仓白名单条件。
                filters.append("(w.warehouse_use_type IS NULL OR w.warehouse_use_type <> 2 OR " + warehouse + " IN (" + ", ".join(["%s"] * len(WHITELIST)) + "))")
                params.extend(WHITELIST)
            date_only = True
        else:
            alias = "r"
            cols = _columns(conn, "fms_cost." + table + "_detail")
            main_cols = _columns(conn, "fms_cost." + table)
            unit = "COALESCE(d.unit_code, '')" if "unit_code" in cols else "''"
            code = "r.stock_order_code" if kind == "purchase" and source == "factory" else "r.business_no" if kind == "purchase" else "r.business_code"
            goods = "d.goods_code" if kind == "purchase" else "d.code" if source == "factory" else "d.sku_code"
            if kind == "purchase":
                warehouse = "r.warehouse_code"
                refund_groups = "6, 602" if source == "factory" else "6, 202"
                quantity = f"CASE WHEN r.psi_group_type IN ({refund_groups}) THEN d.refund_num ELSE d.num END"
                # 采购特殊出库可能不属于采退分组，用真实出库单号辅助确定方向。
                direction = f"CASE WHEN r.psi_group_type IN ({refund_groups}) OR {code} LIKE 'PCK%%' OR {code} LIKE 'CK%%' THEN 'out' ELSE 'in' END"
                join = "d.business_no = r.business_no"
                date_only = True
            else:
                warehouse = "r.out_stock_warehouse_code" if kind == "other_out" else "r.in_stock_warehouse_code"
                quantity = "d.num"
                direction = "'out'" if kind == "other_out" else "'in'"
                join = "d.stock_id = r.id"
                filters.append("r.psi_group_type IN (" + ", ".join(["%s"] * len(module.PSI_GROUP_TYPES)) + ")")
                params.extend(module.PSI_GROUP_TYPES)
                date_only = False
            from_sql = f"FROM fms_cost.{table} r JOIN fms_cost.{table}_detail d ON {join} "
            from_sql += f"LEFT JOIN oms_product.warehouse w ON {warehouse} = w.warehouse_code "
            if "shop_code" in main_cols:
                from_sql += "LEFT JOIN oms_business.shop sh ON r.shop_code = sh.shop_code LEFT JOIN oms_business.structure st ON sh.structure_id = st.id "
            # 采购和其他出入库不套用销售日志的工厂仓路由，避免仅因仓库就误报来源缺失。
            ownership = _ownership_sql("w", shop="shop_code" in main_cols,
                                       warehouse_route=False, factory_code="factory_code" in main_cols)

        # 合法拆分行按来源、业务日期与分组先求和，跨来源再比较完整数量分布。
        sql = (
            f"SELECT {code} AS order_code, {goods} AS goods_code, {direction} AS direction, "
            f"COALESCE({warehouse}, '') AS warehouse_code, {unit} AS unit_code, "
            f"CASE WHEN COUNT({quantity}) < COUNT(*) THEN NULL ELSE SUM({quantity}) END AS total_num, {alias}.business_date AS business_date, "
            f"{alias}.psi_group_type AS psi_group_type, {ownership} AS ownership "
            + from_sql + f"WHERE {alias}.business_date BETWEEN %s AND %s "
            + ("AND " + " AND ".join(filters) + " " if filters else "")
            + "GROUP BY order_code, goods_code, direction, warehouse_code, unit_code, business_date, psi_group_type, ownership"
        )
        result.append((source, sql, params, date_only))
    return result


def get_fms_dataset(conn, module, kind, start, end, day_batch_size=None):
    cache_key = (kind, start, end, day_batch_size)
    cache = getattr(conn, "_fms_source_dataset", None)
    if cache:
        if cache[0] != cache_key:
            raise ValueError("同一次 FMS 快照不能混用不同的时间范围或核对类型")
        return cache[1]
    datetime_start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    datetime_end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
    if datetime_start > datetime_end:
        raise ValueError("开始时间不能晚于结束时间")
    dataset = FmsDataset(kind)
    try:
        queries = source_queries(conn, module, kind)
        ranges = list(_date_ranges(start, end, day_batch_size)) if day_batch_size else [(start, end)]
        for source, sql, extra_params, date_only in queries:
            for range_start, range_end in ranges:
                with conn.cursor(SSDictCursor) as cursor:
                    cursor.execute(sql, [range_start[:10], range_end[:10]] + extra_params if date_only else [range_start, range_end] + extra_params)
                    while True:
                        rows = cursor.fetchmany(2000)
                        if not rows:
                            break
                        dataset.add(source, rows)
                dataset.db.commit()
        dataset.resolve()
        conn._fms_source_dataset = (cache_key, dataset)
        return dataset
    except BaseException:
        dataset.close()
        raise


def close_fms_dataset(conn):
    cached = getattr(conn, "_fms_source_dataset", None)
    if cached:
        cached[1].close()
        del conn._fms_source_dataset


def run_reconciliation(module, conn, args, kind):
    """现有 IOM 查询与 CSV 列保持兼容，新增跨来源处理明细。"""
    if args.batch_size < 1:
        raise ValueError("分批数量必须大于零")
    audit_output = getattr(args, "source_audit_output", None) or str(Path(args.detail_output).with_suffix("")) + "_source_audit.csv"
    if len({Path(p).resolve() for p in (args.summary_output, args.detail_output, audit_output)}) != 3:
        raise ValueError("汇总、单据明细和来源处理文件必须使用不同路径")
    days = args.day_batch_size if kind == "sales_outbound" else None
    if days is not None and days < 1:
        raise ValueError("分批天数必须大于零")
    dataset = get_fms_dataset(conn, module, kind, args.start_time, args.end_time, days)
    left = dataset.summary()
    if kind == "purchase":
        right = module.fetch_iom_summary(conn, args.start_time, args.end_time)
    elif kind == "sales_outbound":
        right = module.fetch_right_summary(conn, args.start_time, args.end_time, day_batch_size=days)
    else:
        right = module.fetch_right_summary(conn, args.start_time, args.end_time)
    summary_rows, numeric_pairs = module.build_summary_rows(left, right)
    issues = dataset.blocking_issues()
    issue_pairs = {tuple(p) for issue in issues for p in json.loads(issue["affected_pairs"])}
    presence_pairs = set(left) ^ set(right)
    pairs = sorted(set(numeric_pairs) | issue_pairs | presence_pairs)
    for row in summary_rows:
        if (row["warehouse_code"], row["goods_code"]) in issue_pairs:
            row["message"] = "FMS来源异常，数量待确认"
            # 空值表示未确定，而不是数量为零。原始两边数值均在审计文件保留。
            row["fms_cost_num" if kind in ("other_in", "other_out") else "fms_num"] = ""
            row["diff_num"] = ""
        elif (row["warehouse_code"], row["goods_code"]) in presence_pairs and _decimal(row["diff_num"]) == ZERO:
            row["message"] = "记录存在性不一致"

    detail_rows, right_detail = [], {}
    key_column = "order_code" if kind == "purchase" else "business_code"
    fms_column = "fms_cost_num" if kind in ("other_in", "other_out") else "fms_num"
    iom_column = "erp_iom_num" if kind in ("other_in", "other_out") else "iom_num"
    if pairs:
        left_detail = dataset.detail(pairs)
        if kind == "purchase":
            right_detail = module.fetch_iom_detail(conn, args.start_time, args.end_time, pairs, args.batch_size)
        elif kind == "sales_outbound":
            right_detail = module.fetch_right_detail(conn, args.start_time, args.end_time, pairs, args.batch_size, days)
        else:
            right_detail = module.fetch_right_detail(conn, args.start_time, args.end_time, pairs, args.batch_size)
        codes = sorted({code for code, _ in set(left_detail) | set(right_detail)})
        meta = module.fetch_iom_order_meta(conn, codes)
        detail_rows = module.build_detail_rows(left_detail, right_detail, meta, args.start_time, args.end_time)
        # 记录存在且数量为零，与根本没有记录分别返回。
        for key in set(left_detail) ^ set(right_detail):
            if left_detail.get(key, ZERO) == right_detail.get(key, ZERO):
                detail_rows.append({key_column: key[0], "goods_code": key[1], fms_column: str(left_detail.get(key, ZERO)),
                                    iom_column: str(right_detail.get(key, ZERO)), "diff_num": "0", "message": "单据存在性不一致",
                                    "failure_reason": "FMS零数量记录存在，IOM范围内无记录" if key in left_detail else "IOM零数量记录存在，FMS范围内无记录"})
    issue_keys = {(r["order_code"], r["goods_code"]) for r in issues}
    detail_rows = [r for r in detail_rows if (r[key_column], r["goods_code"]) not in issue_keys]
    for issue in issues:
        key = (issue["order_code"], issue["goods_code"])
        detail_rows.append({key_column: key[0], "goods_code": key[1], fms_column: "",
                            iom_column: str(right_detail[key]) if key in right_detail else "", "diff_num": "",
                            "message": issue["decision"], "failure_reason": issue["failure_reason"] + "；两边原值见来源处理明细"})
    detail_rows.sort(key=lambda r: (r[key_column], r["goods_code"], r["message"]))
    module.write_csv(args.summary_output, summary_rows, ["warehouse_code", "goods_code", fms_column, iom_column, "diff_num", "message"])
    module.write_csv(args.detail_output, detail_rows, [key_column, "goods_code", fms_column, iom_column, "diff_num", "message", "failure_reason"])
    dataset.write_audit(audit_output)
    duplicate_count = dataset.db.execute("SELECT COUNT(*) FROM audits WHERE decision = '跨来源重复'").fetchone()[0]
    print(f"核对完成，时间范围 {args.start_time} 到 {args.end_time}，汇总对比 {len(summary_rows)} 行，汇总差异组合 {len(pairs)} 个，单据差异 {len(detail_rows)} 条")
    print(f"跨来源重复 {duplicate_count} 组，来源异常 {len(issues)} 组；仓库商品汇总核对，单据下钻仅覆盖差异和来源异常组合")
    print(f"汇总文件: {args.summary_output}")
    print(f"单据差异文件: {args.detail_output}")
    print(f"来源处理文件: {audit_output}")
