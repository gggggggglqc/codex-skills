# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 / 分销子单 / 分销订单 | `dt` / `sub_order_id` / `order_id` | date / varchar |
| 仓库 / 货主 | `warehouse_code` / `owner_code` | varchar |
| 商品 / 货品 / SKU | `goods_code` / `spu_code` / `sku_code` | varchar |
| 单价 / 下单数量 | `price` / `num` | decimal / int |
| 发货/实到/实收数量 | `delivery_num` / `receive_num` / `actual_receive_num` | int |
| 创建/更新时间 | `create_time` / `update_time` | datetime |
