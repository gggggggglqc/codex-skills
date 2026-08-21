---
asset_id: dim.srm_supplier_supplier
layer: DIM
table_name: doris_dim_srm_supplier_supplier
database: dp_dim
business_name: 供应商维表
status: 已确认
grain: 自然日、供应商编码的供应商属性快照
primary_key: 待确认（候选为 dt + supplier_code）
partition: { field: dt, semantic: 自然日快照, strategy: 按业务日期等值关联 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 新增返利成本金额的供应商税率来源 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_srm_supplier_supplier DDL", locator: doris_dim_srm_supplier_supplier, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# 供应商维表

分销发货返利成本金额的供应商税率来源。供应商编码由分销发货子单 SKU 关联 `doris_dim_oms_product_sku_supplier` 得到。
