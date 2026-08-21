---
asset_id: ods.oms_strategy_stock_lock
layer: ODS
table_name: stock_lock
database: oms_strategy
business_name: 库存锁定策略主表
status: 部分确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 一条库存锁定策略（stock_lock_id）
primary_key: id（业务唯一键：stock_lock_id、strategy_code）
partition: { strategy: 业务库表，无分区 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-17, valid_to: null, change_summary: 登记库存策略锁定主表 DDL }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 oms_strategy.stock_lock DDL, locator: stock_lock, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: ods.oms_strategy_stock_lock_detail
      join: stock_lock_id = lock_id；过滤 stock_lock.status = 1 且 deleted != -1
---

# 库存锁定策略主表

用于确定策略是否有效：`status = 1` 为启用，`2` 为禁用；逻辑删除标识 `deleted = -1`。`sku_num_lock` 是策略当前总锁定量，库存指标“正品策略锁定量”仍须以明细表的 `apply_lock_stock` 汇总，不能以该字段替代。
