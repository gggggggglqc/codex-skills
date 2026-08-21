---
asset_id: dim.oms_product_sku_supplier
layer: DIM
table_name: doris_dim_oms_product_sku_supplier
database: dp_dim
business_name: 商品 SKU 供应商关系
status: 已确认（字段 DDL 待补）
grain: SKU 与供应商的关系行
primary_key: 待确认
partition: { field: dt, semantic: 待确认, strategy: 按业务 dt 关联待 DDL 确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 新增分销发货供应商来源链路 }
source_evidence:
  - { type: product_confirmation, path: "用户于会话中确认", locator: "子单 SKU → doris_dim_oms_product_sku_supplier", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: []
---

# 商品 SKU 供应商关系

分销发货供应商由子单 SKU 查询本表获得；一个 SKU 命中多个供应商时，保留全部供应商编码并使用逗号拼接。该多值关系不参与返利成本税率计算。
