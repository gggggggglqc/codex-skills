---
asset_id: dim.warehouse
layer: DIM
table_name: doris_dim_warehouse
database: dp_dim
business_name: 仓库维度
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 仓库维度行
primary_key: 待确认（候选为 id 或 warehouse_code）
partition: { field: dt, semantic: 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 仓库公共维度作为仓库所在区域的正式来源 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_warehouse DDL", locator: doris_dim_warehouse, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions:
  - 用户已确认仓库所在区域以本表为准；区域字段将在本表后续上线时增加。上线后补充字段名，以及它与采购价格区域键的对应关系。
---

# 仓库维度

提供仓库名称、类别、功能、地址、供应商、组织等基础属性。仓库所在区域以本表为准：按 `warehouse_code` 关联；区域字段将在后续上线，届时补充与采购价格区域键的转换规则。
