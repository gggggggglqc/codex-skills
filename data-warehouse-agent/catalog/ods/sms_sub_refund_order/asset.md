---
asset_id: ods.sms_sub_refund_order
layer: ODS
table_name: sub_refund_order
database: sms_ops
business_name: 分销退单子订单
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销退单子单（sub_refund_id）
primary_key: sub_refund_id
partition: { strategy: 业务库表，无分区 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-17, valid_to: null, change_summary: 登记分销退单子单 DDL，补齐分销退货商品事实 }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 sms_ops.sub_refund_order DDL, locator: sms_ops.sub_refund_order, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.dms_refund_return_index
      join: refund_id + sub_refund_id + goods_code；提供申请、发货、确认到货、实收数量及退回单价
---

# 分销退单子订单

商品事实主来源。`apply_num`、`deliver_num`、`confirm_arrival_num`、`actual_num` 分别为申请、退货发货、供应商确认到货、供应商实收数量；`refund_price` 为退回单价。申请退款金额为 `apply_num × refund_price`，退款金额为对应退货数量 × `refund_price`。
