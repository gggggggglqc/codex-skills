---
asset_id: dim.expense_subject_relation
layer: DIM
table_name: doris_dim_expense_subject_relation
database: dp_dim
business_name: 费用科目关系表
status: 部分确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 按 dt 自然日切片, load_strategy: 待确认 }
grain: 日期 + 费用编码
primary_key: 待确认（DDL 未声明 KEY）
partition: { field: dt, semantic: 自然日切片, strategy: DDL 未声明 PARTITION BY }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE dp_dim.doris_dim_expense_subject_relation DDL, locator: dp_dim.doris_dim_expense_subject_relation, observed_at: 2026-08-18 }
---

# 费用科目关系表

以 `expense_code` 映射费用名称、科目编码和层级，并提供 `cost_share_method`。关联失败时 `cost_share_method=-1`、科目层级 `-1`，相关科目字段置空。净利 V2 的 `expense_code` 以该表最新有效 `dt` 映射科目。
