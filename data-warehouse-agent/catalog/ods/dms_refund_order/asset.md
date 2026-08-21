---
asset_id: ods.dms_refund_order
layer: ODS
table_name: doris_ods_dms_refund_order
database: dp_ods
business_name: DMS 分销退单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销退单主单行
primary_key: dt + refund_id
partition: { field: dt, semantic: finance_audit_time 日期, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 DMS 分销退单主单 DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 doris_ods_dms_refund_order DDL, locator: doris_ods_dms_refund_order, observed_at: 2026-08-14 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: dws.dms_refund_return_index
      join: dms_refund_order.refund_id = dms_refund_return_index.refund_id
---

# DMS 分销退单主单

以 `dt + refund_id` 唯一标识，`dt` 为财审时间分区，不是创建时间。提供分销退单状态、类型、申请金额/数量、退货仓库/货主/店铺、创建人、申请/审核时间以及换货信息。

当前分销退单与退货 Index 直接使用既有结果；本期不重建或核查影刀分支，`create_by` 仅作为源表可用字段登记。
