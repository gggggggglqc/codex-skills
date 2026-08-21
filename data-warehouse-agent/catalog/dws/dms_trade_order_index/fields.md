# 字段与指标映射（V6.5.1）

## 主键与维度

`dt` 为主单创建时间，`sub_order_id` 为分销子订单 ID；物理模型为 `UNIQUE KEY(dt, sub_order_id, order_id)`。每日删除并重算最近 60 天；商品、货品、店铺、货主、仓库、分销商、组织、地区、类目、品牌、供应商等维度均有同名物理列。

## 分销订单指标

| 逻辑指标 | 物理字段 |
|---|---|
| 分销订单商品下单数量 | `num` |
| 分销订单商品金额 | `amount` |
| 分销订单商品供货成本（财务口径） | `estimate_brand_quotation` |
| 分销订单商品采购成本（含税） | `purchase_price_total`；规则见 `catalog/dws/cost-rules/purchase-cost-tax-included-v6.5.1.md` |
| `no_tax_purchase_price_total` | DDL 已存在，但“分销订单商品采购成本（不含税）（已乘下单数量）”在 V6.5.1 最新文档中为删除线历史口径；当前业务含义/使用范围待 ETL SQL 确认 |
| 分销订单商品净利成本（含税/不含税） | `product_cost` / `no_tax_product_cost`；不含税指标仍为文档的直接取价链，规则见 `catalog/dws/cost-rules/net-profit-cost-v6.5.1.md` |

## 修饰词

`order_function`、`sales_model`、`pay_status`、`order_status`、`is_brand_fix_priced`、`is_self_research`、`is_eliminate`、`goods_category` 为当前已确认映射；业务解释以 Excel “修饰词”和“修饰词-商品专属”为准。

## 待确认映射

1. “返利后成本（不含税）”仅为派生计算中间金额，不是本 Index 的输出字段。
2. 当前最新文档未定义分销订单的返利比率、返利成本金额和返利成本进项税额；若业务需要三项指标，应补充产品口径和 DWS 字段。
