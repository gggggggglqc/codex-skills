---
asset_id: ods.abroad_production_revenue_profit
layer: DWD
table_name: abroad_production_revenue_profit
database: tmp_data
business_name: 跨境收入销量本月拆分数据
status: 部分确认
refresh: { frequency: 业务导入后按本月拆分, timezone: Asia/Shanghai, load_window: 对应业务时间, load_strategy: 系统由导入原始表拆分生成；先删除对应时间数据后写入 }
grain: 发货日期 + 店铺 + 货主 + 商品 + 字段编码 + 销售模式 + 平台链接
primary_key: [shipping_date, shop_code, owner_code, goods_code, field_code, sales_model, reserved_field1]
partition: { field: shipping_date, semantic: 发货日期, strategy: DDL 未声明 PARTITION BY }
distribution: HASH(shipping_date, owner_code)，BUCKETS 5
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE abroad_production_revenue_profit DDL, locator: abroad_production_revenue_profit, observed_at: 2026-08-18 }
---

# 跨境收入销量本月拆分数据

该表不是业务直接导入表。业务先导入 `abroad_production_revenue_profit_import`，系统再将导入数据拆分至本表的当月数据；写入前先删除对应业务时间数据，避免重复。`tmp_data.abroad_production_revenue_profit` 才是净利 V2 的跨境导入输入。

字段映射：`shipping_date → V2.dt`，`goods_code → V2.sku_code`，`reserved_field1 → V2.plat_spu_id`，`revenue_cost_amount` 为不含税收入/成本金额，`tax_income_inclusive` 为含税收入，`tax_self_rev` 为含税自研收入，`num` 为 SKU 销量，`sku_volume` 为 SKU 体积，`reserved_field2=6` 表示产销导入。

物理表为 `tmp_data.abroad_production_revenue_profit`。`field_code` 除 DDL 注释的 `EP001`（收入）、`EP003`（不含税成本）外，也支持 `EP042`（关税）和 `EP043`（头程费用）。
