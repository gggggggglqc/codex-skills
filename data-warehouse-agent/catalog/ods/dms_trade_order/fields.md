# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 / 分销订单 | `dt` / `order_id` | date / varchar |
| 分销商 / 货主 / 店铺 | `distributor_id` / `owner_code` / `shop_code` | varchar |
| 货款 / 邮费 / 商品总数 | `total_fee` / `post_fee` / `goods_num` | decimal / int |
| 订单状态 / 类型 / 来源 | `status` / `order_type` / `order_source` | int |
| 付款 / 财审 | `pay_type` / `financial_audit_time` / `financial_audit_by` | int / datetime / varchar |
| 创建/更新时间 | `create_time` / `update_time` | datetime |
