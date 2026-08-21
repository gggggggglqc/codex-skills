---
asset_id: ods.sms_sub_outbound_delivery_order
layer: ODS
table_name: sub_outbound_delivery_order
database: sms_ops
business_name: 分销销售出库子单
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 销售出库子单（sub_outbound_delivery_order_id）
primary_key: sub_outbound_delivery_order_id
partition: { strategy: 业务库表，无分区 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-17, valid_to: null, change_summary: 登记分销正向销售出库子单 DDL }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 sms_ops.sub_outbound_delivery_order DDL, locator: sms_ops.sub_outbound_delivery_order, observed_at: 2026-08-17 }
---

# 分销销售出库子单

通过 `sub_order_id`、`sub_delivery_order_id`、`delivery_order_id` 关联分销正向订单、发货和销售出库，用于售后退单关联原正向履约时追溯商品与出库单。
