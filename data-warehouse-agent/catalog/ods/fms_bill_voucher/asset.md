---
asset_id: ods.fms_bill_voucher
layer: ODS
table_name: voucher
database: fms_bill
business_name: 凭证记录主表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 按 business_date 业务发生日期, load_strategy: 待确认 }
grain: 凭证
primary_key: [id]
logical_unique_key: [voucher_id]
indexes: [[account_set, org_code, business_date], [business_date], [business_date, voucher_no, voucher_id], [fiscal_period], [resource_no, voucher_resource]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE fms_bill.voucher DDL, locator: fms_bill.voucher, observed_at: 2026-08-18 }
---

# 凭证记录主表

以 `voucher_id` 关联 `fms_bill.voucher_detail`。提供账套、组织、业务发生日期、凭证审核/结账状态、凭证来源及来源单号；净利规则要求使用账套 `4` 的有效科目口径，最终状态过滤待确认。
