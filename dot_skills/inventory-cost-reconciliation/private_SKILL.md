---
name: inventory-cost-reconciliation
description: 用于执行存货成本月末核对技能包，核对 erp_cost.inventory_cost_details 与 IOM/MES/业务单据汇总差异，支持按核算月和可调整业务起止时间范围核对，定位未参与计算、货主错位、抵消关系、退货应收、无单退货、销售出库等问题。当用户提到存货收发存明细、inventory_cost_details、cost_deduction_order、按月份或日期范围核对、差异单据定位时使用。
version: 1.0.0
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

---

## 版本管理（遵循数仓文档管理规范v1.0）

> 来源：[数仓文档管理规范v1.0](https://alidocs.dingtalk.com/i/nodes/QOG9lyrgJP3PAm3kuvy0z6E3VzN67Mw4)

### 版本说明

| 版本号 | 版本内容 | 上线状态 | 上线时间 | 维护人 | 备注 |
|--------|----------|----------|----------|--------|------|
| V1.0.0 | 初始版本，录入核心规则与核对流程 | 已上线 | 2026-07-06 | QoderWork | 按数仓文档管理规范v1.0补充版本管理章节 |

### 版本更新规则

1. **版本号**：与禅道版本号保持一致（如 V1.0.0、V1.1.0、V2.0.0）
2. **Sheet 命名**：指标说明按"版本号 + 简述"格式（如 `V1.1.0 口径调整`）
3. **变更标识**：本期新增或修改内容使用**红色字体**标识；删除内容使用~~画线~~处理
4. **历史版本**：只隐藏不删除，便于追溯
5. **额外说明**：绑定版本号，格式为 `【V1.x.0 额外说明】`
6. **更新流程**：复制上一版本 → 修改本期内容（标红）→ 更新版本说明 → 检查额外说明 → 隐藏历史版本 → 上线后更新状态
