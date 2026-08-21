---
asset_id: dws.srm_delivery_order_index
layer: DWS
table_name: doris_dws_srm_delivery_order_index
database: dp_dws
business_name: 采购发货单商品指标
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近120天, load_strategy: 覆盖更新 }
grain: 采购发货子单商品行（sub_delivery_order_id）
primary_key: dt + sub_delivery_order_id（UNIQUE KEY）
partition: { field: dt, semantic: 创建时间业务分区字段, strategy: DDL 未声明 PARTITION BY }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购发货 Index DDL及成本字段 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_dws_srm_delivery_order_index DDL, locator: doris_dws_srm_delivery_order_index, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: dwd.srm_delivery_order_combine
      join: sub_delivery_order_id；补充工厂物料、货主、供应商、商品和成本字段
    - upstream_asset: dim.oms_product_produce_factory_warehouse
      join: 收货时间对应 dt + 收货仓库编码，获取 factory_code
    - upstream_asset: dim.oms_product_factory_material
      join: 收货时间对应 dt + factory_code + goods_code = sku_code，获取 material_code、material_name
---

# 采购发货单商品指标

采购发货商品层 Index。按 `dt + sub_delivery_order_id` 唯一去重。价格字段为 `no_tax_price`（不含税含运费单价）与 `price`（含税含运费单价）；成本输出为 `no_tax_cost_price`、`no_tax_cost_price_total`。
