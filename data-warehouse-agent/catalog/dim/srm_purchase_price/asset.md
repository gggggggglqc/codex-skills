---
asset_id: dim.srm_purchase_price
layer: DIM
table_name: doris_dim_srm_purchase_price
database: dp_dim
business_name: 采购价格维表
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 全量快照, load_strategy: 按 dt 写入每日全量分区 }
grain: 自然日 + 采购价格条目（purchase_price_id）
primary_key: dt + purchase_price_id（UNIQUE KEY）
partition: { field: dt, semantic: 每日全量分区日期, strategy: RANGE 月分区；动态分区，history_partition_num=18 }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购价格维表 DDL与生效时间类型 }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/e5a7680f-56e5-443e-b836-17f3df3a5cc8/pasted-text.txt, locator: doris_dim_srm_purchase_price, observed_at: 2026-08-14 }
---

# 采购价格维表

按日全量快照的采购价格维表。价格生效时间类型：`time_type = 0` 为下单时间，`1` 为到货时间；生效区间使用 `start_time`、`end_time`。按月动态分区，保留 18 个历史分区。状态枚举以业务库为准：`0` 生效、`1` 失效。
