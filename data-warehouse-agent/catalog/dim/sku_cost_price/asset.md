---
asset_id: dim.sku_cost_price
layer: DIM
table_name: doris_dim_sku_cost_price
database: dp_dim
business_name: 多种成本价融合维表
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 仓库、商品、价格类型和价格生效区间的价格行
primary_key: 待确认
partition: { field: dt, semantic: 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 融合表采购价唯一来源，按 V6.5.1 规则更新 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_sku_cost_price DDL", locator: doris_dim_sku_cost_price, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["价格开始时间最近的选择是否要求 price_start_time 小于等于业务时间，待确认。"]
---

# 多种成本价融合维表

采购成本（含税）的二、三级兜底来源：先按仓库所在区域、商品、下单时间取采购价；仍为空或 0 时，再按商品、下单时间查价格开始时间最近的采购价，均限制 `cost_type = 2`，商品级多条取最高的 `tax_freight_price`。
