---
asset_id: ods.fms_cost_expense_detail_cb
layer: ODS
table_name: expense_detail_cb
database: fms_cost
business_name: 跨境费用明细表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 按 trans_dt 账单日期, load_strategy: 待确认 }
grain: 跨境费用流水
primary_key: [id]
logical_unique_key: [log_id, is_deleted]
indexes: [[trans_dt, plat_code, shop_code], [tid], [trans_dt]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE fms_cost.expense_detail_cb DDL, locator: fms_cost.expense_detail_cb, observed_at: 2026-08-18 }
---

# 跨境费用明细表

跨境费用账单原始事实。业务上传的跨境费用数据进入本表。除国内费用共有字段外，还包括 `sku_id`、币别 `currency_code`、售后单号 `after_sales_tracking_number`、数量 `quantity` 与业务编号 `business_no`。

与凭证中间表的具体转换、币别折算、删除状态过滤和实际/预计费用过滤规则待确认。
