# 标准工作流

## 1. 总数核对

先执行主汇总脚本，只输出差异。默认业务时间范围为核算月整月：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\reconcile_inventory_cost_total_7day.py' --calculation-month 2026-03 --summary-output 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_diff_only.csv'
```

如果用户指定日期范围，传入 `--start-time / --end-time`。时间范围左闭右开：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\reconcile_inventory_cost_total_7day.py' --calculation-month 2026-03 --start-time '2026-03-14 00:00:00' --end-time '2026-03-15 00:00:00' --summary-output 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_0314_diff_only.csv'
```

注意：`calculation_month` 仍用于成本侧 `inventory_cost_details` 的核算月；`start-time/end-time` 控制业务侧来源单据时间范围。

记录：

- `inventory_cost` 组合数。
- 来源汇总组合数。
- 差异组合数。
- 输出文件路径。

## 2. 总表分析

用辅助脚本：

```powershell
py -3 'C:\Users\lqc\.codex\skills\inventory-cost-reconciliation\scripts\summarize_diff.py' --input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_diff_only.csv'
```

必须输出：

- 按类型分布。
- 成本侧比业务侧少/多。
- 跨货主抵平数量。
- 跨类型抵平数量。
- 剩余未抵平高优先级样例。

## 3. 样例下探

不要对全量差异直接下探。先抽样：

```powershell
py -3 'C:\Users\lqc\.codex\skills\inventory-cost-reconciliation\scripts\make_priority_samples.py' --input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_diff_only.csv' --output 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_priority_samples.csv' --limit 10
```

再运行下探：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\locate_inventory_cost_diff_docs.py' --calculation-month 2026-03 --summary-input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_priority_samples.csv' --suspected-output 'C:\Users\lqc\Desktop\inventory_cost_diff_suspected_docs_2026-03_priority_samples.csv' --unresolved-output 'C:\Users\lqc\Desktop\inventory_cost_diff_unresolved_keys_2026-03_priority_samples.csv' --price-diff-output 'C:\Users\lqc\Desktop\inventory_cost_diff_price_mismatch_docs_2026-03_priority_samples.csv'
```

如果总表使用自定义业务时间范围，下探必须使用相同范围：

```powershell
py -3 'D:\codex\工厂账务核对\fms-reconciliation\scripts\locate_inventory_cost_diff_docs.py' --calculation-month 2026-03 --start-time '2026-03-14 00:00:00' --end-time '2026-03-15 00:00:00' --summary-input 'C:\Users\lqc\Desktop\inventory_cost_total_compare_summary_2026-03_priority_samples.csv' --suspected-output 'C:\Users\lqc\Desktop\inventory_cost_diff_suspected_docs_2026-03_priority_samples.csv' --unresolved-output 'C:\Users\lqc\Desktop\inventory_cost_diff_unresolved_keys_2026-03_priority_samples.csv' --price-diff-output 'C:\Users\lqc\Desktop\inventory_cost_diff_price_mismatch_docs_2026-03_priority_samples.csv'
```

## 4. 单个组合排查

用户给出 `owner / warehouse / sku` 时，不重跑全量。直接从已有结果文件查该组合，然后单独查成本侧与业务侧。

步骤：

1. 从结果 CSV 找该组合所有 `biz_type_code`。
2. 查 `inventory_cost_details` 对应 `order_type`、`cost_source`、数量、单价。
3. 查业务侧对应单据明细。
4. 按 `cost_source + cost_price + qty + amount` 分桶。
5. 如果同仓同 SKU 其他货主存在等额业务单，判断为货主错位。

## 5. 输出方式

简单结论先行：

```text
这不是业务侧缺单，而是货主错位。
```

再给关键数字：

```text
成本侧：-29
业务侧：-26
差异：3
```

最后给必要单据号：

```text
差异单据：2036281673903665152
关联销售出库单：CK2603212035223351731183616
```

不要把几百行明细直接贴到最终回复；如果需要明细，生成文件并给路径。
