---
asset_id: dim.fms_support_subject
layer: DIM
table_name: doris_dim_fms_support_subject
database: dp_dim
business_name: 财务科目维表
status: 部分确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 按 dt 自然日切片, load_strategy: 待确认 }
grain: 日期 + 账套 + 科目
primary_key: 待确认（DDL 未声明 KEY）
partition: { field: dt, semantic: 自然日分区, strategy: DDL 未声明 PARTITION BY }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE dp_dim.doris_dim_fms_support_subject DDL, locator: dp_dim.doris_dim_fms_support_subject, observed_at: 2026-08-18 }
---

# 财务科目维表

提供账套 `account_set`、科目层级、发生/余额方向、`is_tax`、分摊标识和维度。它是**科目维表**，不是费用归属策略表；费用归属 `cost_belong` 仍以 `doris_dim_fms_support_cost_gather_strategy` 为准。净利口径要求使用账套 `4` 的最新有效切片。
