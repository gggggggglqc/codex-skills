---
asset_id: dim.owner_markup_rule
layer: DIM
table_name: doris_dim_owner_markup_rule
database: dp_dim
business_name: 货主返利策略
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 货品、货主、加价月份的返利策略行
primary_key: 待确认（候选为 id）
partition: { field: month, semantic: 加价月份, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 货主返利比率来源首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_dim_owner_markup_rule DDL", locator: doris_dim_owner_markup_rule, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["多条命中时的优先级和无命中时默认 0 的 ETL 实现待确认。"]
---

# 货主返利策略

按“货品编码 + 货主编码 + 业务时间所在月份”匹配，取 `rebate_rate`；无匹配时返利比率为 0。
