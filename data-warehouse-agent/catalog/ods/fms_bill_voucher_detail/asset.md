---
asset_id: ods.fms_bill_voucher_detail
layer: ODS
table_name: voucher_detail
database: fms_bill
business_name: 凭证记录明细表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 跟随凭证业务日期, load_strategy: 待确认 }
grain: 凭证明细分录
primary_key: [id]
logical_unique_key: [voucher_detail_id]
indexes: [[voucher_id], [subject_code], [accounting_dimension]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE fms_bill.voucher_detail DDL, locator: fms_bill.voucher_detail, observed_at: 2026-08-18 }
---

# 凭证记录明细表

以 `voucher_id` 关联凭证主表，以 `voucher_detail_id` 关联核算维度明细。提供科目 `subject_code`、借贷方本位币金额、币别、汇率、核算维度串、项目和费用报销标识，是构建凭证科目中间表金额与科目维度的核心明细。
