---
asset_id: ods.dms_trade_order
layer: ODS
table_name: doris_ods_dms_trade_order
database: dp_ods
business_name: DMS 分销订单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销订单主单行
primary_key: 待确认（候选为 order_id，须确认）
partition: { field: dt, semantic: create_time 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: sources/ddl/2026-08-13-sales-module-ods.sql, locator: doris_ods_dms_trade_order, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["请确认 order_id 是否可作为稳定唯一键及订单状态更新策略。"]
---

# DMS 分销订单主单

与分销订单子单通过 `order_id` 关联，承载分销商、货主、店铺、订单状态、付款和财审等主单属性。
