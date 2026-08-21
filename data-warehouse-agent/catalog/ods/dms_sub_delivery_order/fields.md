# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 / 发货单子单 | `dt` / `sub_delivery_order_id` | date / varchar |
| 分销订单/子单/发货单 | `order_id` / `sub_order_id` / `delivery_order_id` | varchar |
| 商品 / 货品 / SKU | `goods_code` / `spu_code` / `sku_code` | varchar |
| 单价 | `price` | decimal(19,5) |
| 发货/实到/实收/退货数量 | `delivery_num` / `receive_num` / `actual_receive_num` / `refund_num` | int |
| 创建/更新时间 | `create_time` / `update_time` | datetime |
