---
asset_id: ods.sms_sub_refund_stock_order
layer: ODS
table_name: sub_refund_stock_order
database: sms_ops
business_name: 分销退货入库明细单
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 退货入库子单（sub_stock_order_id）
primary_key: sub_stock_order_id
partition: { strategy: 业务库表，无分区 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-17, valid_to: null, change_summary: 登记分销退货入库子单 DDL，补齐商品级实收事实 }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 sms_ops.sub_refund_stock_order DDL, locator: sms_ops.sub_refund_stock_order, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: ods.dms_refund_stock_order
      join: stock_order_id；取得 refund_id、收货时间及入库主单状态
    - downstream_asset: dws.dms_refund_return_index
      join: refund_id + goods_code；补充商品级入库实收数量
---

# 分销退货入库明细单

通过 `stock_order_id` 关联分销退货入库主单，再以 `refund_id + goods_code` 对齐分销退单商品。已确认同一 `refund_id` 下不会出现多条相同 `goods_code` 的 `sub_refund_id`，故无需额外分摊。`actual_num` 为商品级入库实收数量，`apply_num` 为申请入库数量。
