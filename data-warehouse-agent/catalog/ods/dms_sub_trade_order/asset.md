---
asset_id: ods.dms_sub_trade_order
layer: ODS
table_name: doris_ods_dms_sub_trade_order
database: dp_ods
business_name: DMS 分销订单子单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销订单子单商品行
primary_key: 待确认（候选为 dt + sub_order_id，须确认）
partition: { field: dt, semantic: create_time 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: sources/ddl/2026-08-13-sales-module-ods.sql, locator: doris_ods_dms_sub_trade_order, observed_at: 2026-08-13 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: dws.dms_trade_order_index
      join: dms_trade_order.order_id = dms_sub_trade_order.order_id
open_questions: ["请确认分销子订单的键模型与增量更新规则。"]
---

# DMS 分销订单子单

分销订单商品粒度的直接 ODS 来源；与 DMS 分销订单主单按 `order_id` 关联。
