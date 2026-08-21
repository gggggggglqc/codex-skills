---
asset_id: dim.platform
layer: DIM
table_name: doris_dim_platform
database: dp_dim
business_name: 平台维表
status: 已确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 按 dt 日切片
  load_strategy: 待确认
grain: 日期 + 平台维度记录
primary_key: [dt, id]
partition:
  field: dt
  semantic: 日期
  strategy: 逻辑日切片（DDL 未声明 PARTITION BY）
distribution: HASH(id)，BUCKETS 3
version:
  scene: 发货 V1 平台与国别判定
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: 用户于会话中提供的 CREATE TABLE doris_dim_platform DDL
    locator: doris_dim_platform
    observed_at: 2026-08-18
---

# 平台维表

`plat_code` 为平台代码，`cbs_platform` 标识是否跨境平台（`0` 否、`1` 是）。发货 V1 按业务日期和店铺所属平台代码关联本表：用于输出 `cbs_platform`，并按当前有效规则判定国别；跨境平台记为空国别，非跨境平台记为 `CN`。
