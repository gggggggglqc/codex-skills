---
asset_id: ods.oms_order
layer: ODS
table_name: doris_ods_oms_order
database: dp_ods
business_name: OMS 原始订单子单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 原始订单子单商品行
primary_key: source_sub_order_id（OMS 源表主键；Doris 抽取表键模型待确认）
partition: { field: dt, semantic: create_time 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: sources/ddl/2026-08-13-sales-module-ods.sql, locator: doris_ods_oms_order, observed_at: 2026-08-13 }
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/24069069-a32d-4561-8695-166a77ab755a/pasted-text.txt, locator: oms_order.oms_order, observed_at: 2026-08-14 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: ods.sub_trade_order
      join: oms_order.source_sub_order_id = sub_trade_order.source_sub_order_id
---

# OMS 原始订单子单

原始订单商品数据的主入口。OMS 源表 `oms_order.oms_order` 的主键为 `source_sub_order_id`；按原始子订单商品行保存平台货品/规格、数量、优惠、分摊、实付、退款及平台状态。

原始订单主单 `oms_order.oms_trade` 与原始订单子单通过 `source_order_id` 关联；原始订单子单通过 `source_sub_order_id` 关联到系统订单子单，也可关联原始退单子单。
