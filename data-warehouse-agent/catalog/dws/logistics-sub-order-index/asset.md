---
asset_id: dws.logistics_sub_order_index
layer: DWS
table_name: doris_dws_logistics_order_index
database: dp_dws
business_name: 物流宽表中的子单粒度逻辑视图
status: 已确认
grain: 发货日期、物流单号、原始子订单/商品子单
primary_key: 复用物流宽表 UNIQUE KEY(dt + express_code)
partition: { field: dt, semantic: 出库日期, strategy: 复用物流宽表月分区；每日覆盖更新最近 61 天 }
fields_file: fields.md
version: { scene: 物流模块当前版本, valid_from: 2026-08-13, valid_to: null, change_summary: 根据物流模块子单粒度文档首次登记 }
source_evidence:
  - { type: product_doc, path: "/Users/liuqingchen/Downloads/物流模块（主单、子单粒度）.xlsx", locator: "表字段说明（子单粒度index表）", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# 物流子单粒度 Index

物流模块没有独立子单 Index；主单、子单字段打平保存在 `dp_dws.doris_dws_logistics_order_index`。本资产仅保存其中子单商品粒度的逻辑规则。
