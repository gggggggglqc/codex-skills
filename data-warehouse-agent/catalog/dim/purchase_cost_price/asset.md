---
asset_id: dim.purchase_cost_price
layer: DIM
table_name: purchase_cost_price
database: srm_billing
business_name: 采购成本表（含返利成本）
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 商品、仓库、货主、供应商和月份的采购成本价格行
primary_key: cost_price_id
partition: { field: month, semantic: 成本月份, strategy: 业务库索引字段，非 Doris 分区 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 返利后成本来源 DDL 已确认 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 srm_billing.purchase_cost_price DDL", locator: purchase_cost_price, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions:
  - 业务规则中的“仓库所在区域”通过 `doris_dim_warehouse` 由仓库编码取得；区域字段将在后续上线时增加。
  - “最新月份/对应月份”的精确排序与无对应月份时的回退规则，按每个成本分支确认。
---

# 采购成本表（含返利成本）

返利后成本（不含税）的一级来源。`purchase_cost_price` 为采购成本价，`cost_price` 为成本价，`rebate_amount` 为返利金额；各指标使用哪个字段，以 V6.5.1 规则为准。
