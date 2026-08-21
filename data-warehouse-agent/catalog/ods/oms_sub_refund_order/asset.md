---
asset_id: ods.oms_sub_refund_order
layer: ODS
table_name: oms_sub_refund_order
database: oms_order
business_name: OMS 原始退单子单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 原始退单商品行
primary_key: "(source_sub_order_id, refund_id)"
partition: { field: 无, semantic: 源表未声明分区, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 OMS 原生退单子单 DDL }
source_evidence:
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/24069069-a32d-4561-8695-166a77ab755a/pasted-text.txt, locator: oms_order.oms_sub_refund_order, observed_at: 2026-08-14 }
---

# OMS 原始退单子单

源表物理主键为自增 `id`，售后业务唯一键为 `(source_sub_order_id, refund_id)`。该表保存退款商品、数量、单价、分摊退回买家金额和其他退款金额。

`refund_id` 关联原始退单主单 `oms_order.oms_refund`；`source_sub_order_id` 关联原始订单子单 `oms_order.oms_order`，从而建立原始退单到原始订单商品行的确定性链路。
