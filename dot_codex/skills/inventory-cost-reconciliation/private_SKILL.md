---
name: inventory-cost-reconciliation
description: 用于执行存货成本月末核对技能包，核对 erp_cost.inventory_cost_details 与 IOM/MES/业务单据汇总差异，支持按核算月和可调整业务起止时间范围核对，定位未参与计算、货主错位、抵消关系、退货应收、无单退货、销售出库等问题。当用户提到存货收发存明细、inventory_cost_details、cost_deduction_order、按月份或日期范围核对、差异单据定位时使用。
metadata:
  short-description: 存货成本月末核对与差异单据定位
---

# 存货成本核对技能包

## 什么时候用

用户要求核对 `inventory_cost_details` 与 IOM/MES/业务单据、跑某月差异、解释退货应收/无单退货/销售出库差异、定位缺失单据、判断货主错位或 `cost_deduction_order` 抵消关系时使用。

## 固定入口

主汇总脚本：

`D:\codex\工厂账务核对\fms-reconciliation\scripts\reconcile_inventory_cost_total_7day.py`

单据下探脚本：

`D:\codex\工厂账务核对\fms-reconciliation\scripts\locate_inventory_cost_diff_docs.py`

技能包辅助脚本：

- `scripts/summarize_diff.py`：汇总差异类型、方向、跨货主抵平、跨类型抵平。
- `scripts/make_priority_samples.py`：从总差异文件抽取高优先级样例 CSV。

详细规则：

- `references/rules.md`：核对规则、类型映射、抵消口径、差异判断。
- `references/sql_patterns.md`：常用排查 SQL 模式。
- `references/workflow.md`：标准执行流程和输出约定。

## 标准流程

1. 先运行总数核对，只生成差异文件，不做全量明细下探。默认业务时间范围为核算月整月，也可以传入 `--start-time / --end-time` 调整。
2. 用 `scripts/summarize_diff.py` 汇总差异分布和方向。
3. 先判断是否为跨货主抵平、跨类型抵平。
4. 从总差异文件抽取少量高优先级样例。
5. 对样例 CSV 运行单据下探脚本。
6. 对退货应收/无单退货，必要时按 `cost_source + cost_price + qty + amount` 分桶定位差异单据。
7. 输出结论时先说总数和主因，再列必要的单据号。

## 常用命令

运行整月汇总：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\reconcile_inventory_cost_total_7day.py' --calculation-month 2026-03 --summary-output 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_diff_only.csv'
```

运行指定业务时间范围汇总：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\reconcile_inventory_cost_total_7day.py' --calculation-month 2026-03 --start-time '2026-03-14 00:00:00' --end-time '2026-03-15 00:00:00' --summary-output 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_0314_diff_only.csv'
```

汇总差异分布：

```powershell
py -3 'C:\Users\lqc\.codex\skills\inventory-cost-reconciliation\scripts\summarize_diff.py' --input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_diff_only.csv'
```

抽取高优先级样例：

```powershell
py -3 'C:\Users\lqc\.codex\skills\inventory-cost-reconciliation\scripts\make_priority_samples.py' --input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_diff_only.csv' --output 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_priority_samples.csv' --limit 10
```

运行样例下探：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\locate_inventory_cost_diff_docs.py' --calculation-month 2026-03 --summary-input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_priority_samples.csv' --suspected-output 'C:\Users\lqc\Desktop\inventory_cost_diff_suspected_docs_2026-03_priority_samples.csv' --unresolved-output 'C:\Users\lqc\Desktop\inventory_cost_diff_unresolved_keys_2026-03_priority_samples.csv' --price-diff-output 'C:\Users\lqc\Desktop\inventory_cost_diff_price_mismatch_docs_2026-03_priority_samples.csv'
```

如果总表使用了自定义业务时间范围，下探脚本必须传入同样的 `--start-time / --end-time`。

## 操作原则

不要一开始全量下探明细。总表只负责找差异和排序，明细定位必须另起小样例。

当用户给具体 `owner + warehouse + sku`，只查该组合，不重跑全量。

当用户问“是不是都由某货主导致”，必须按结果文件统计后回答。

当查询超时，缩小范围：先查头表取单号，再用单号查明细。
