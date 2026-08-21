---
asset_id: ods.trade_order_ext
layer: ODS
table_name: doris_ods_trade_order_ext
database: dp_ods
business_name: OMS 系统订单扩展
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 系统订单主单扩展行
primary_key: 待确认（候选为 dt + order_id，须确认）
partition: { field: dt, semantic: create_time 分区日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_ods_trade_order_ext DDL", locator: doris_ods_trade_order_ext, observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["外部订单信息 out_order_info（1688）是否参与当前销售模块指标，待确认。"]
---

# OMS 系统订单扩展

按系统订单补充应发货/预计到货时间、分销商与外部订单信息。
