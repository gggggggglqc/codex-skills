---
asset_id: ods.dms_refund_delivery_order
layer: ODS
table_name: doris_ods_dms_refund_delivery_order
database: dp_ods
business_name: DMS 分销退货发货主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销退货发货主单行
primary_key: 待确认（候选为 refund_delivery_id，须确认）
partition: { field: dt, semantic: create_time 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: sources/ddl/2026-08-13-sales-module-ods.sql, locator: doris_ods_dms_refund_delivery_order, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions:
  - 缺少分销退货商品子单 DDL；当前表不能独立解释 DWS 退货数量/成本的商品级拆分。
---

# DMS 分销退货发货主单

分销退货的主单级来源，提供退货金额、总数量、状态和履约信息；商品编码 `goods_codes` 为聚合字符串，不能替代子单明细。
