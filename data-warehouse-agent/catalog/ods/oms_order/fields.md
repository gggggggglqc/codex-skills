# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 | `dt` | date |
| 原始子单 / 原始订单 | `source_sub_order_id` / `source_order_id` | varchar |
| 平台货品 / 规格 | `source_spu` / `source_sku` | varchar |
| 内部匹配商品 / SKU | `matched_goods_code` / `sku` | varchar |
| 数量 / 单价 / 优惠 / 总价 | `quantity` / `unit_price` / `discount_fee` / `total_fee` | varchar |
| 分摊优惠 / 分摊后总价 / 分摊邮费 / 已付 | `share_discount_fee` / `sharedtotal_fee` / `share_post_fee` / `paid` | varchar |
| 原始退单 / 退款金额 | `source_refund_order_id` / `refund_fee` | varchar |
| 原始子单状态 / 原始订单状态 | `source_sub_order_status` / `status` | varchar |
| 创建/更新时间 | `create_time` / `update_time` | datetime |

金额与数量在当前 ODS 为 varchar；进入 DWS 前的类型转换、异常值处理与退款归属规则待以 ETL SQL 确认。
