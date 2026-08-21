---
asset_id: ods.ers_expense_expense_order
layer: ODS
table_name: expense_order
database: ers_expense
business_name: 费控单据主表
status: 部分确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 待确认, load_strategy: 待确认 }
grain: 费控单据
primary_key: [id]
logical_unique_key: [instance_id, order_id]
indexes: [[applicant_by], [create_by], [create_time]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE ers_expense.expense_order DDL, locator: ers_expense.expense_order, observed_at: 2026-08-19 }
---

# 费控单据主表

费控报销、借款、还款、预付单据主事实。以 `order_id` / `instance_id` 唯一标识单据，包含审批状态、付款状态、公司、申请部门、成本中心及金额税额。

## 已知净利相关字段

| 字段 | 用途 |
|---|---|
| `approved_time` / `create_time` | 审批通过/建单时间候选 |
| `approve_status` | `99` 为已通过 |
| `cost_center_type` / `cost_center_code` | 店铺、仓库、货主、部门、链接或账号归属 |
| `amount_pre_tax` | 不含税金额 |
| `approved_deduction_amount` | 抵扣税额 |
| `currency_code` | 币种 |

费用项目、金额和税额明细已确认来自 `ers_expense.expense_order_cost_detail`，按 `order_id` 关联本表。
