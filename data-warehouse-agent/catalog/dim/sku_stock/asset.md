---
asset_id: dim.sku_stock
layer: DIM
table_name: doris_dim_sku_stock
database: dp_dim
business_name: SKU 当前库存来源
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 商品 + 仓库 + 货主当前库存行
primary_key: 待确认（DDL 未声明键模型）
partition: { field: 无, semantic: 当前维表无 dt 字段, strategy: 待确认 }
fields_file: fields.md
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 SKU 库存来源维表 DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 doris_dim_sku_stock DDL, locator: doris_dim_sku_stock, observed_at: 2026-08-14 }
---

# SKU 当前库存来源

与业务库保持一致的当前态库存来源，粒度为商品、仓库、货主。该表没有 `dt`，不承载历史切片；按自然日回溯应使用 `dws.sku_stock_index`。
