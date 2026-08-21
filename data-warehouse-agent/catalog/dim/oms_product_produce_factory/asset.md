---
asset_id: dim.oms_product_produce_factory
layer: DIM
table_name: doris_dim_oms_product_produce_factory
database: dp_dim
business_name: 生产工厂维表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 日期 + 工厂编码
primary_key: dt + factory_code（UNIQUE KEY）
partition: { field: dt, semantic: 日期分区, strategy: DDL 未声明 PARTITION BY }
version: { scene: 采购模块, valid_from: 2026-08-17, valid_to: null, change_summary: 登记生产工厂基础维度 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_dim_oms_product_produce_factory DDL, locator: doris_dim_oms_product_produce_factory, observed_at: 2026-08-17 }
---

# 生产工厂维表

提供工厂名称、启用状态、货主、公司及地址等属性。采购发货通过工厂—仓库绑定表取得 `factory_code` 后，可关联本表补充工厂属性。
