---
asset_id: dim.company
layer: DIM
table_name: doris_dim_company
database: dp_dim
business_name: 公司维表
status: 已确认
grain: 自然日、公司编码的公司属性快照
primary_key: 待确认（候选为 dt + company_code）
partition: { field: dt, semantic: 自然日快照, strategy: 按业务日期等值关联 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 新增返利成本税额的公司纳税人性质与开票税率来源 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_company DDL", locator: doris_dim_company, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# 公司维表

返利成本进项税额的公司纳税人性质和开票税率来源。
