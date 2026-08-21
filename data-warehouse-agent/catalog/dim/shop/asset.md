---
asset_id: dim.shop
layer: DIM
table_name: doris_dim_shop
database: dp_dim
business_name: 店铺维表
status: 已确认
grain: 自然日、内部店铺编码的店铺属性快照
primary_key: 待确认（候选为 dt + shop_code）
partition: { field: dt, semantic: 自然日快照, strategy: 按业务日期等值关联 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 新增店铺到公司的返利税额关联链路 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_shop DDL", locator: doris_dim_shop, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# 店铺维表

返利成本税额按业务店铺确定公司：`shop_code → company_code`。
