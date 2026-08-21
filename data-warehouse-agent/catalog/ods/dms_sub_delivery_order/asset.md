---
asset_id: ods.dms_sub_delivery_order
layer: ODS
table_name: doris_ods_dms_sub_delivery_order
database: dp_ods
business_name: DMS 分销发货单子单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销发货单子订单商品行
primary_key: 待确认（候选为 dt + sub_delivery_order_id，须确认）
partition: { field: dt, semantic: create_time 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: sources/ddl/2026-08-13-sales-module-ods.sql, locator: doris_ods_dms_sub_delivery_order, observed_at: 2026-08-13 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: dws.dms_delivery_index
      join: dms_sub_delivery_order.sub_delivery_order_id = dms_delivery_index.sub_delivery_order_id
open_questions: ["请提供分销发货主单 ODS DDL，用于补齐发货单状态、仓库、组织和时间等主单属性。"]
---

# DMS 分销发货单子单

分销发货商品的直接 ODS 来源，关联分销订单子单与分销订单；含发货、实到、实收、退货数量。
