#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
from decimal import Decimal


def to_decimal(value: str) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def row_abs_diff(row: dict) -> Decimal:
    return abs(to_decimal(row.get("in_diff_qty"))) + abs(to_decimal(row.get("out_diff_qty")))


def main() -> None:
    parser = argparse.ArgumentParser(description="从总差异 CSV 抽取高优先级样例")
    parser.add_argument("--input", required=True, help="总差异 CSV")
    parser.add_argument("--output", required=True, help="样例输出 CSV")
    parser.add_argument("--limit", type=int, default=10, help="抽取数量")
    parser.add_argument("--biz-type", action="append", default=[], help="只抽取指定 biz_type_code，可重复传入")
    parser.add_argument("--owner-code", action="append", default=[], help="只抽取指定 owner_code，可重复传入")
    parser.add_argument("--warehouse-code", action="append", default=[], help="只抽取指定 warehouse_code，可重复传入")
    parser.add_argument("--goods-code", action="append", default=[], help="只抽取指定 goods_code，可重复传入")
    parser.add_argument("--prefer-cost-less", action="store_true", help="优先抽取成本侧比业务侧少的行")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    def matched(row: dict) -> bool:
        if args.biz_type and row.get("biz_type_code", "") not in set(args.biz_type):
            return False
        if args.owner_code and row.get("owner_code", "") not in set(args.owner_code):
            return False
        if args.warehouse_code and row.get("warehouse_code", "") not in set(args.warehouse_code):
            return False
        if args.goods_code and row.get("goods_code", "") not in set(args.goods_code):
            return False
        return True

    rows = [row for row in rows if matched(row)]

    if args.prefer_cost_less:
        def priority(row: dict) -> tuple[int, Decimal]:
            inventory_income = to_decimal(row.get("inventory_income_qty"))
            source_in = to_decimal(row.get("source_in_qty"))
            inventory_delivery = to_decimal(row.get("inventory_delivery_qty"))
            source_out = to_decimal(row.get("source_out_qty"))
            cost_less = inventory_income < source_in or abs(inventory_delivery) < abs(source_out)
            return (0 if cost_less else 1, -row_abs_diff(row))

        rows = sorted(rows, key=priority)
    else:
        rows = sorted(rows, key=lambda row: -row_abs_diff(row))

    selected = rows[: args.limit]
    with open(args.output, "w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)

    print(f"输入行数={len(rows)}")
    print(f"输出样例={len(selected)}")
    print(f"样例文件={args.output}")


if __name__ == "__main__":
    main()
