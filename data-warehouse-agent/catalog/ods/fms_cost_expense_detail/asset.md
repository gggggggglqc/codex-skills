---
asset_id: ods.fms_cost_expense_detail
layer: ODS
table_name: expense_detail
database: fms_cost
business_name: 国内费用明细表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 按 trans_dt 账单日期, load_strategy: 待确认 }
grain: 费用流水
primary_key: [id]
logical_unique_key: [log_id, is_deleted]
indexes: [[trans_dt], [tid], [trans_dt, plat_code, shop_code], [account_no]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE fms_cost.expense_detail DDL, locator: fms_cost.expense_detail, observed_at: 2026-08-18 }
---

# 国内费用明细表

国内费用账单原始事实。业务上传的国内费用数据进入本表。关键关联字段为账单日期 `trans_dt`、店铺/平台、原始订单 `tid`、子订单 `oid`、费用项目 `cost_code` 和费用类型 `cost_type`；金额字段包括收入 `income_cost`、支出 `expend_cost`、不含税金额 `no_tax_amount`、税额 `tax_amount`。

与凭证中间表的具体转换、删除状态过滤和实际/预计费用（`occurrence_type`）过滤规则待确认。
