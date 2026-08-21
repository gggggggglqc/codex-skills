# 核心字段

| 业务字段 | 物理字段 |
|---|---|
| 物流单/出库单/系统订单/原始订单/原始子单 | `express_code` / `delivery_order_id` / `order_id` / `source_order_id` / `source_sub_order_id` |
| 仓库、店铺、货主、物流 | `warehouse_code` / `shop_code` / `owner_code` / `logistics_code` / `logistics_type` |
| 商品与数量 | `spu_code` / `sku_code` / `goods_code` / `goods_num` |
| 主单费用与重量 | `logistics_fee` / `agent_delivery_fee` / `adjust_weight` / `collect_time` / `warehouse_delivery_time` |
| 箱规与收货地 | `carton_code` / `receiver_province` / `receiver_city` / `receiver_district` |
| 子单体积与分摊费用 | `weight` / `sku_num_mul_volume` / `sub_agent_delivery_fee` / `sub_logistics_cost_fee` / `settle_sub_agent_delivery_fee` / `settle_sub_logistics_cost_fee` |
