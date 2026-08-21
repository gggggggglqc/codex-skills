---
asset_id: ods.oms_strategy_stock_lock_detail
layer: ODS
table_name: stock_lock_detail
database: oms_strategy
business_name: 库存锁定策略明细表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 一条策略锁定商品明细（detail_id）
primary_key: id（业务标识：detail_id）
partition: { strategy: 业务库表，无分区 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-17, valid_to: null, change_summary: 登记库存策略锁定明细 DDL与指标映射 }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 oms_strategy.stock_lock_detail DDL, locator: stock_lock_detail, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: ods.oms_strategy_stock_lock
      join: lock_id = stock_lock_id；过滤主表 status = 1、deleted != -1
    - downstream_asset: dws.sku_stock_index
      join: warehouse_code + owner_code + goods_code；明细 deleted != -1 后汇总 apply_lock_stock
---

# 库存锁定策略明细表

正品策略锁定量为有效明细的 `SUM(apply_lock_stock)`。有效条件：明细 `deleted != -1`，且关联的策略主表 `status = 1`、`deleted != -1`。按 `warehouse_code + owner_code + goods_code` 对齐库存商品粒度。

`dws.sku_stock_index` 每日全量切片时，按当日运行时的有效策略明细计算并写入当天 `dt`，由 Index 自身保留历史策略锁定量；无需为本业务表另行提供 CDC 历史还原。
