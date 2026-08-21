# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 / 发货单 / 分销订单 | `dt` / `delivery_order_id` / `order_id` | date / varchar |
| 出库单 / 分销商 | `outbound_delivery_order_id` / `distributor_id` | varchar |
| 仓库 / 货主 / 店铺 | `warehouse_code` / `owner_code` / `shop_code` | varchar |
| 发货单状态 / 来源 | `status` / `delivery_order_source` | tinyint |
| 物流方式 / 单号 / 公司 | `logistics_mode` / `express_code` / `logistics_company` | tinyint / varchar |
| 提交/发货/收货/创建/更新时间 | `commit_time` / `delivery_time` / `receive_time` / `create_time` / `update_time` | datetime |
