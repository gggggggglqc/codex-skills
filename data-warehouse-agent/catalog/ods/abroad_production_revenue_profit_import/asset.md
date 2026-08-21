---
asset_id: ods.abroad_production_revenue_profit_import
layer: ODS
table_name: abroad_production_revenue_profit_import
database: tmp_data
business_name: 跨境收入销量业务导入原始表
status: 已确认
refresh: { frequency: 业务导入, timezone: Asia/Shanghai, load_window: 对应业务时间, load_strategy: 写入前删除对应时间的数据，再写入新数据；与 abroad_production_revenue_profit 一致 }
grain: 发货日期 + 店铺 + 货主 + 商品 + 字段编码 + 销售模式 + 平台链接
primary_key: [shipping_date, shop_code, owner_code, goods_code, field_code, sales_model, reserved_field1]
partition: { field: shipping_date, semantic: 发货日期, strategy: DDL 未声明 PARTITION BY }
distribution: HASH(shipping_date, owner_code)，BUCKETS 5
source_evidence:
  - { type: business_confirmation, path: 用户于会话中确认, locator: 业务导入→系统拆分本月数据, observed_at: 2026-08-18 }
  - { type: business_confirmation, path: 用户于会话中确认, locator: tmp_data 库；与 abroad_production_revenue_profit 保存更新逻辑一致, observed_at: 2026-08-19 }
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE abroad_production_revenue_profit_import DDL, locator: abroad_production_revenue_profit_import, observed_at: 2026-08-18 }
---

# 跨境收入销量业务导入原始表

业务向 `tmp_data.abroad_production_revenue_profit_import` 导入数据。每次上传先删除对应业务时间的数据，再写入新数据；因此同一时间窗口为覆盖更新，其他历史时间保留。系统将数据拆分至 `tmp_data.abroad_production_revenue_profit` 的当月数据，后者再作为净利 V2 的跨境导入来源。

字段与本月拆分表一致：`shipping_date`、店铺/货主/商品、`field_code`、销售模式、`reserved_field1`（平台链接）、不含税金额 `revenue_cost_amount`、含税收入/自研收入、销量和体积。
