---
asset_id: dws.logistics_order_index
layer: DWS
table_name: doris_dws_logistics_order_index
database: dp_dws
business_name: 物流主单粒度 Index
status: 已确认
grain: 发货日期、物流单号
primary_key: dt + express_code
partition: { field: dt, semantic: 出库日期, strategy: 月分区；每日覆盖更新最近 61 天 }
fields_file: fields.md
version: { scene: 物流模块当前版本, valid_from: 2026-08-13, valid_to: null, change_summary: 根据物流模块主单粒度文档首次登记 }
source_evidence:
  - { type: product_doc, path: "/Users/liuqingchen/Downloads/物流模块（主单、子单粒度）.xlsx", locator: "表字段说明（主单粒度index表）", observed_at: 2026-08-13 }
  - { type: warehouse_ddl, path: "/Users/liuqingchen/.codex/attachments/0b2e0818-23c3-4d5a-b302-70fed25ec1fa/pasted-text.txt", locator: "UNIQUE KEY(dt, express_code)", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# 物流主单粒度 Index

以物流单号为载体，服务物流公司分析、OMS 审单策略选物流和物流评估。
