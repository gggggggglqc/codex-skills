# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 / 退货发货单 / 退单 | `dt` / `refund_delivery_id` / `refund_id` | date / varchar |
| 分销商 / 仓库 / 收货货主 / 店铺 | `distributor_id` / `warehouse_code` / `owner_code` / `shop_code` | varchar |
| 退货状态 / 退货金额 / 邮费 / 总数量 | `delivery_status` / `total_fee` / `post_fee` / `goods_num` | int / decimal |
| 商品编码集合 | `goods_codes` | string |
| 物流单号 / 发货 / 收货时间 | `express_code` / `delivery_time` / `receive_time` | varchar / datetime |
