---
asset_id: ods.oms_ops_refund_order
layer: ODS
table_name: refund_order
database: oms_ops
business_name: OMS 系统退单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 系统退单主单行
primary_key: refund_id
partition: { field: 无, semantic: 源表未声明分区, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 OMS 系统退单主单 DDL }
source_evidence:
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/22885e23-b2e4-4528-addb-d061d232fc25/pasted-text.txt, locator: oms_ops.refund_order, observed_at: 2026-08-14 }
---

# OMS 系统退单主单

以 `refund_id` 为系统退单主键；通过 `source_refund_id` 关联 OMS 原始退单主单 `oms_order.oms_refund.refund_id`。包含申请、退货、退款时间，退款状态/类型、申请金额、运单、店铺和商家收货状态。

`order_id` 是文本类型，且注释明确手工建退换单会设置系统订单 ID；系统退单的商品级关联应以系统退单子单为准。
