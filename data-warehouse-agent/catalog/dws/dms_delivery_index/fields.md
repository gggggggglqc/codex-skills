# 字段与指标映射（V6.5.1）

## 主键与关联

`dt` 为主单创建时间，`sub_delivery_order_id` 为发货单子订单 ID；物理模型为 `UNIQUE KEY(dt, sub_delivery_order_id)`。每日删除并重算最近 60 天。通过 `order_id`、`sub_order_id` 可关联分销订单，但不关联系统订单子单。

## 分销发货与退货指标

| 逻辑指标 | 物理字段 |
|---|---|
| 发货数量 / 实到数量 / 实收数量 / 退货数量 | `delivery_num` / `receive_num` / `actual_receive_num` / `refund_num` |
| 发货金额 / 实收金额 | `delivery_amount` / `actual_amount` |
| 商品单价 | `price` |
| 分销发货单商品供货成本（已乘发货数量，财务口径） | `brand_quotation` |
| 分销发货单商品采购成本（含税） | `purchase_price_total`；规则见 `catalog/dws/cost-rules/purchase-cost-tax-included-v6.5.1.md` |
| `no_tax_purchase_price_total` | DDL 已存在，但“分销发货单商品采购成本（不含税）（已乘发货数量）”在 V6.5.1 最新文档中为删除线历史口径；当前业务含义/使用范围待 ETL SQL 确认 |
| 分销发货单商品净利成本（含税/不含税） | `product_cost` / `no_tax_product_cost`；不含税净利成本为含税净利成本减进项税额（成本），规则见 `catalog/dws/cost-rules/net-profit-cost-v6.5.1.md` |
| 返利比率 / 返利不含税采购价 | `rebate_rate` / `no_tax_price`；最新文档的返利不含税采购价为“已乘下单数量”，与发货事实的数量基数须确认 |
| 分销发货返利成本金额（已乘下单数量）/返利成本进项税额/返利比率 | `rebate_cost_amount` / `input_tax_amount_rebate` / `rebate_rate` |

## 修饰词

`order_function`、`sales_model`、`pay_status`、`order_status`、`exit_warehouse_way`、`status`、`delivery_status`、`is_brand_fix_priced`、`is_self_research`、`is_eliminate`、`goods_category` 的枚举以 DDL 为准。

## 待确认映射

1. 分销退货成本指标是使用本表退货数量计算，还是另有退货明细表/ETL 逻辑。
