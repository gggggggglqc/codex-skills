---
asset_id: ods.ers_expense_expense_order_cost_detail
layer: ODS
table_name: expense_order_cost_detail
database: ers_expense
business_name: 费控费用明细表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 按消费/到票日期, load_strategy: 待确认 }
grain: 费控单据 + 费用明细
primary_key: [expense_order_cost_detail_id]
foreign_keys:
  - { field: order_id, references: ers_expense.expense_order.order_id }
indexes: [[order_id], [cost_code], [duty_by]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE ers_expense.expense_order_cost_detail DDL, locator: ers_expense.expense_order_cost_detail, observed_at: 2026-08-19 }
---

# 费控费用明细表

按 `order_id` 关联费控单据主表 `ers_expense.expense_order`。该表是费控进入净利费用链路的商品/费用项目级事实。

| 字段 | 净利用途 |
|---|---|
| `cost_code` | 费用项目编码；与费用采集策略/科目关系关联 |
| `expense_amount` | 费用含税金额候选 |
| `amount_pre_tax` | 不含税费用金额 |
| `approved_deduction_amount` | 抵扣税额 |
| `cost_center_type` / `cost_center_code` | 店铺、仓库、货主、部门、链接、账号归属 |
| `consume_date_start` / `consume_date_end` | 业务发生日期候选 |
| `currency_code` | 币种 |

主表负责审批状态和公司/申请部门，明细表负责费用项目及金额；构建费用事实时需按 `order_id` 合并。最终采用的日期字段、审批/付款/核销状态过滤、汇率折算规则由净利/凭证处理任务确定，当前 DDL 未声明。
