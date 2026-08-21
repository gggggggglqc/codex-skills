---
asset_id: dim.srm_billing_purchase_ladder_price
layer: DIM
table_name: doris_dim_srm_billing_purchase_ladder_price
database: dp_dim
business_name: 采购阶梯价格
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 商品、仓库、货主、供应商、加价月份的阶梯价格行
primary_key: 待确认
partition: { field: dt, semantic: 加价日期转为每月 1 日, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 采购成本一级取价来源首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_srm_billing_purchase_ladder_price DDL", locator: doris_dim_srm_billing_purchase_ladder_price, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["多条价格命中时的选择规则待确认。"]
---

# 采购阶梯价格

销售模块“采购成本（含税）”的一级来源：按仓库、商品和发货时间所在月份匹配，取含税含运费单价 `tax_freight_price`。
