---
asset_id: dws.sku_stock_index
layer: DWS
table_name: doris_dws_sku_stock_index
database: dp_dws
business_name: SKU 库存按日切片指标
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 全量, load_strategy: 先删后新增 }
grain: 自然日 + 商品 + 仓库 + 货主
primary_key: dt + goods_code + warehouse_code + owner_code（UNIQUE KEY）
partition: { field: dt, semantic: 自然日期, strategy: RANGE 月分区；动态分区，history_partition_num=24 }
fields_file: fields.md
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 登记库存日切片 Index DDL，明确为库存历史承载表 }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/9e406b9e-90bf-47f0-9882-52509d4ab1ae/pasted-text.txt, locator: doris_dws_sku_stock_index, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: dim.sku_stock
      join: 商品 + 仓库 + 货主当前态库存按自然日切片，并补充库存指标、维度和滚动销售/出库指标
    - upstream_asset: ods.oms_strategy_stock_lock_detail
      join: 当日有效明细按 warehouse_code + owner_code + goods_code 汇总 apply_lock_stock，写入 strategized_lock_stock
---

# SKU 库存按日切片指标

库存模块按自然日查询、历史回溯与库存周转分析的正式承载表。`dp_dim.doris_dim_sku_stock` 仅与业务库保持当前态一致；历史切片以本表的 `dt` 为准。

DDL 已确认：按 `dt + goods_code + warehouse_code + owner_code` UNIQUE KEY 去重；`dt` 按月 RANGE 动态分区，时区为 Asia/Shanghai，保留 24 个历史分区；商品、仓库、货主和 MD5 建有 Bitmap 索引。每日先删后新增全量更新。
