# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 系统订单 / 原始订单 / 发货单 | `order_id` / `source_order_id` / `delivery_order_id` | varchar |
| 店铺 / 货主 / 仓库 / 物流 | `shop_*` / `owner_code` / `warehouse_code` / `logistics_code` | varchar |
| 主单金额 | `total_fee` / `post_fee` / `payment` / `discount_fee` | decimal(19,5) |
| 订单状态 | `trade_status` / `inner_status` / `refund_status` / `order_type` | int |
| 业务时间 | `trade_time` / `pay_time` / `audit_time` / `delivery_time` / `complete_time` | datetime |
| 收货地区 / 买家 | `receiver_province` / `receiver_city` / `receiver_district` / `buyer_open_uid` | varchar |
| 订单来源 / 功能线索 | `trade_from` / `order_category` | int |
