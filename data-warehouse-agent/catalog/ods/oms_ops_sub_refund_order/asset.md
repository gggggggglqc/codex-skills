---
asset_id: ods.oms_ops_sub_refund_order
layer: ODS
table_name: sub_refund_order
database: oms_ops
business_name: OMS 系统退单子单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 系统退单商品行
primary_key: sub_refund_id
partition: { field: 无, semantic: 源表未声明分区, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 OMS 系统退单子单 DDL }
source_evidence:
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/2ea90c89-8b54-472a-b22a-a30af37d4a72/pasted-text.txt, locator: oms_ops.sub_refund_order, observed_at: 2026-08-14 }
---

# OMS 系统退单子单

以 `sub_refund_id` 为主键。`refund_id` 关联系统退单主单；`sub_order_id` 关联系统订单子单。保留原始退单/订单的 `source_refund_id`、`source_order_id` 和 `source_sub_order_id`，可将原始及系统两套售后单据精确串联。

当前业务确认系统退单与系统订单可通过原始订单子单稳定关联，不启用补偿匹配或多订单拆分逻辑。
