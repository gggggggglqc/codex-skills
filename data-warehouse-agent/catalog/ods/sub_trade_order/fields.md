# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 系统子单 / 系统订单 | `sub_order_id` / `order_id` | varchar |
| 原始订单 / 原始子单 | `source_order_id` / `source_sub_order_id` | varchar |
| 商品 / 平台规格 / 平台商家编码 | `goods_code` / `plat_sku_id` / `plat_goods_code` | varchar |
| 组合装 | `combine_code` / `combine_num` / `combine_is_split` | varchar / int |
| 下单/实发数量和单价 | `num` / `actual_num` / `price` | int / decimal |
| 优惠/分摊/总价/实付/退款 | `adjust_fee` / `discount_fee` / `share_discount` / `share_post_fee` / `total_fee` / `payment` / `refund_fee` | decimal(19,5) |
| 子单状态 / 退款状态 / 系统子单状态 | `order_status` / `refund_status` / `sub_inner_status` | tinyint |
| 赠品/商品类型 | `goods_type` | tinyint |
| 创建/更新时间 | `create_time` / `update_time` | datetime |

该表可直接支持 DWS 中系统订单的数量、货款、优惠、分摊、实付、退款、组合装和部分修饰词字段；成本、物流、包材、组织维度需结合其他 ODS/DIM 表。
