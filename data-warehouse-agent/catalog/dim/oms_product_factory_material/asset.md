---
asset_id: dim.oms_product_factory_material
layer: DIM
table_name: doris_dim_oms_product_factory_material
database: dp_dim
business_name: 工厂物料关系维表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 日期 + 工厂 + 物料关系行
primary_key: 待确认（DDL 未声明 Doris 键模型）
partition: { field: dt, semantic: 日期分区, strategy: 待确认 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 登记工厂物料与成品商品映射 DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 dp_dim.doris_dim_oms_product_factory_material DDL, locator: dp_dim.doris_dim_oms_product_factory_material, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.inbound_and_outbound_index
      join: factory_code + goods_code（工厂物料场景的 material_code）关联，补充 sku_code 与 stock_type
---

# 工厂物料关系维表

库存出入库中的工厂物料以 `factory_code + material_code` 关联本表，取得成品商品编码 `sku_code` 与存货类别 `stock_type`。使用时应限制有效、审核通过的记录；若同一工厂物料多条有效记录，当前 DDL 未给出优先级，待补充。
