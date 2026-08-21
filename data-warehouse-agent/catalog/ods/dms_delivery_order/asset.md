---
asset_id: ods.dms_delivery_order
layer: ODS
table_name: doris_ods_dms_delivery_order
database: dp_ods
business_name: DMS 分销发货单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销发货单主单行
primary_key: 待确认（候选为 delivery_order_id，须确认）
partition: { field: dt, semantic: create_time 日期, strategy: 按创建时间分区 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_ods_dms_delivery_order DDL", locator: doris_ods_dms_delivery_order, observed_at: 2026-08-13 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: dws.dms_delivery_index
      join: dms_delivery_order.delivery_order_id = dms_sub_delivery_order.delivery_order_id
open_questions:
  - 请确认 delivery_order_id 是否为稳定唯一键，以及主单状态更新/重跑策略。
---

# DMS 分销发货单主单

通过 `delivery_order_id` 与分销发货子单关联，提供分销发货单的订单、分销商、店铺、货主、仓库、状态、物流与履约时间属性。
