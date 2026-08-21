---
asset_id: ods.oms_trade
layer: ODS
table_name: oms_trade
database: oms_order
business_name: OMS 原始订单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 原始订单主单行
primary_key: source_order_id
partition: { field: 无, semantic: 源表未声明分区, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 OMS 原生订单主单 DDL }
source_evidence:
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/24069069-a32d-4561-8695-166a77ab755a/pasted-text.txt, locator: oms_order.oms_trade, observed_at: 2026-08-14 }
---

# OMS 原始订单主单

以 `source_order_id` 为主键，承载平台、店铺、收货信息、订单金额、支付/发货/完成时间与订单状态。

与 `oms_order.oms_order` 通过 `source_order_id` 关联；与原始退单主单 `oms_order.oms_refund` 亦通过该字段关联。
