---
asset_id: dim.stock_cost
layer: DIM
table_name: doris_dim_stock_cost
database: dp_dim
business_name: 存货成本价
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 商品、货主、仓库、计价月份的成本价格行
primary_key: 待确认
partition: { field: dt, semantic: 计价月份（每月 1 日）, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 成本价/结存价唯一来源；用于系统订单未发货采购成本及净利成本规则 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_stock_cost DDL", locator: doris_dim_stock_cost, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions:
  - `accounting_organization` 计划于月底上线；售后分销退货成本规则上线后需限制该字段为 1，正向销售成本不使用此筛选。
---

# 存货成本价

成本价/结存价的唯一来源。系统订单未发货采购成本使用已关账的上月 `cost_price × 1.13`；净利成本规则也使用本表的 `cost_price` 或 `delivery_cost_price`，具体分支以对应规则文档为准。

`accounting_organization` 计划于月底上线。上线后，售后分销退货的相关成本取价限制 `accounting_organization = 1`；正向销售成本不增加该筛选。
