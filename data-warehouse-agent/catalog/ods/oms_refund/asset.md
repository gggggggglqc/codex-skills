---
asset_id: ods.oms_refund
layer: ODS
table_name: doris_ods_oms_refund
database: dp_ods
business_name: OMS 原始退单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 原始退款单主单行
primary_key: refund_id（OMS 源表主键；Doris 抽取表键模型待确认）
partition: { field: dt, semantic: refund_time 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: sources/ddl/2026-08-13-sales-module-ods.sql, locator: doris_ods_oms_refund, observed_at: 2026-08-13 }
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/b0968b46-0a3a-4215-8397-05e515785b97/pasted-text.txt, locator: oms_order.oms_refund, observed_at: 2026-08-14 }
implementation_mapping: { das_references: [], warehouse_references: [] }
---

# OMS 原始退单主单

OMS 源表 `oms_order.oms_refund` 的主键为 `refund_id`。通过 `source_order_id` 与原始订单主单关联，并通过原始退单子单的 `refund_id` 下钻至原始订单子单。

提供退款申请、实际退款、退款状态、退款/退货/成功时间、退单类型和阶段等主单级信息。
