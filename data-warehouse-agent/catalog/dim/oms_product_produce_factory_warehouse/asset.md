---
asset_id: dim.oms_product_produce_factory_warehouse
layer: DIM
table_name: doris_dim_oms_product_produce_factory_warehouse
database: dp_dim
business_name: 生产工厂绑定仓库维表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 日期 + 工厂仓库绑定记录（id）
primary_key: dt + id（UNIQUE KEY）
partition: { field: dt, semantic: 日期分区, strategy: DDL 未声明 PARTITION BY }
version: { scene: 采购模块, valid_from: 2026-08-17, valid_to: null, change_summary: 登记采购发货收货仓到工厂的映射维表 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_dim_oms_product_produce_factory_warehouse DDL, locator: doris_dim_oms_product_produce_factory_warehouse, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.srm_delivery_order_index
      join: 收货时间对应 dt + receive_warehouse_code = warehouse_code，获取 factory_code
---

# 生产工厂绑定仓库维表

采购发货场景以收货仓库关联本表获得工厂编码。采购文档中写作 `doris_dim_oms_product_produce_factory_ware`，实际 DDL 表名确认为 `doris_dim_oms_product_produce_factory_warehouse`。
