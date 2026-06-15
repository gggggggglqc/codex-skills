#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
from collections import defaultdict
from decimal import Decimal


def to_decimal(value: str) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def classify_outbound(cost_qty: Decimal, source_qty: Decimal) -> str:
    if abs(cost_qty) < abs(source_qty):
        return "成本侧比业务侧少"
    if abs(cost_qty) > abs(source_qty):
        return "成本侧比业务侧多"
    return "一致"


def classify_inbound(cost_qty: Decimal, source_qty: Decimal) -> str:
    if cost_qty < source_qty:
        return "成本侧比业务侧少"
    if cost_qty > source_qty:
        return "成本侧比业务侧多"
    return "一致"


def load_rows(path: str) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as file_obj:
        for row in csv.DictReader(file_obj):
            row["_in_diff"] = to_decimal(row.get("in_diff_qty"))
            row["_out_diff"] = to_decimal(row.get("out_diff_qty"))
            row["_inventory_income"] = to_decimal(row.get("inventory_income_qty"))
            row["_source_in"] = to_decimal(row.get("source_in_qty"))
            row["_inventory_delivery"] = to_decimal(row.get("inventory_delivery_qty"))
            row["_source_out"] = to_decimal(row.get("source_out_qty"))
            rows.append(row)
    return rows


def print_type_summary(rows: list[dict]) -> None:
    by_type = defaultdict(lambda: {"count": 0, "in_sum": Decimal("0"), "out_sum": Decimal("0"), "abs": Decimal("0")})
    for row in rows:
        item = by_type[row.get("biz_type_code", "")]
        item["count"] += 1
        item["in_sum"] += row["_in_diff"]
        item["out_sum"] += row["_out_diff"]
        item["abs"] += abs(row["_in_diff"]) + abs(row["_out_diff"])

    print("按类型分布")
    for biz_type, item in sorted(by_type.items(), key=lambda kv: -kv[1]["abs"]):
        print(f"{biz_type}\tcount={item['count']}\tin_sum={item['in_sum']}\tout_sum={item['out_sum']}\tabs={item['abs']}")


def print_direction_summary(rows: list[dict]) -> None:
    summary = defaultdict(lambda: {"count": 0, "abs": Decimal("0")})
    for row in rows:
        if row["_in_diff"] != 0:
            label = classify_inbound(row["_inventory_income"], row["_source_in"])
            key = (row.get("biz_type_code", ""), label)
            summary[key]["count"] += 1
            summary[key]["abs"] += abs(row["_in_diff"])
        if row["_out_diff"] != 0:
            label = classify_outbound(row["_inventory_delivery"], row["_source_out"])
            key = (row.get("biz_type_code", ""), label)
            summary[key]["count"] += 1
            summary[key]["abs"] += abs(row["_out_diff"])

    print("\n按差异方向")
    for key, item in sorted(summary.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        print(f"{key[0]}\t{key[1]}\tcount={item['count']}\tabs={item['abs']}")


def print_offset_summary(rows: list[dict]) -> None:
    by_ownerless = defaultdict(list)
    by_type_less = defaultdict(list)
    for row in rows:
        by_ownerless[(row.get("warehouse_code", ""), row.get("goods_code", ""), row.get("biz_type_code", ""))].append(row)
        by_type_less[(row.get("owner_code", ""), row.get("warehouse_code", ""), row.get("goods_code", ""))].append(row)

    owner_offset_rows = 0
    owner_offset_abs = Decimal("0")
    for items in by_ownerless.values():
        if len(items) <= 1:
            continue
        in_sum = sum(item["_in_diff"] for item in items)
        out_sum = sum(item["_out_diff"] for item in items)
        if in_sum == 0 and out_sum == 0:
            owner_offset_rows += len(items)
            owner_offset_abs += sum(abs(item["_in_diff"]) + abs(item["_out_diff"]) for item in items)

    type_offset_rows = 0
    type_offset_abs = Decimal("0")
    for items in by_type_less.values():
        if len(items) <= 1:
            continue
        in_sum = sum(item["_in_diff"] for item in items)
        out_sum = sum(item["_out_diff"] for item in items)
        if in_sum == 0 and out_sum == 0:
            type_offset_rows += len(items)
            type_offset_abs += sum(abs(item["_in_diff"]) + abs(item["_out_diff"]) for item in items)

    print("\n抵平识别")
    print(f"跨货主抵平行数={owner_offset_rows}\tabs={owner_offset_abs}")
    print(f"跨类型抵平行数={type_offset_rows}\tabs={type_offset_abs}")


def print_top_rows(rows: list[dict], limit: int) -> None:
    print(f"\nTop {limit} 差异")
    sorted_rows = sorted(rows, key=lambda row: -(abs(row["_in_diff"]) + abs(row["_out_diff"])))
    for row in sorted_rows[:limit]:
        print(
            "\t".join(
                [
                    row.get("owner_code", ""),
                    row.get("warehouse_code", ""),
                    row.get("goods_code", ""),
                    row.get("biz_type_code", ""),
                    row.get("inventory_income_qty", ""),
                    row.get("source_in_qty", ""),
                    row.get("in_diff_qty", ""),
                    row.get("inventory_delivery_qty", ""),
                    row.get("source_out_qty", ""),
                    row.get("out_diff_qty", ""),
                ]
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="汇总 inventory_cost 差异 CSV")
    parser.add_argument("--input", required=True, help="差异 CSV 文件")
    parser.add_argument("--top", type=int, default=30, help="输出 Top N 差异")
    args = parser.parse_args()

    rows = load_rows(args.input)
    print(f"差异行数={len(rows)}")
    print_type_summary(rows)
    print_direction_summary(rows)
    print_offset_summary(rows)
    print_top_rows(rows, args.top)


if __name__ == "__main__":
    main()
