---
asset_id: dwd.oms_logistics_order_combine
layer: DWD
table_name: doris_dwd_oms_logistics_order_combine
database: dp_dwd
business_name: OMS 物流订单组合
status: 已确认
grain: 物流单、出库单子单、商品行
primary_key: 待确认
partition: { field: dt, semantic: 出库时间分区, strategy: 待确认 }
fields_file: fields.md
version: { scene: 物流模块当前版本, valid_from: 2026-08-13, valid_to: null, change_summary: 物流主单/子单 Index 上游首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "用户提供的 doris_dwd_oms_logistics_order_combine DDL", locator: doris_dwd_oms_logistics_order_combine, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# OMS 物流订单组合

物流模块主单、子单 Index 的核心上游。仅使用 `order_status in (7, 8)`，即已完成、已发货的出库单。
