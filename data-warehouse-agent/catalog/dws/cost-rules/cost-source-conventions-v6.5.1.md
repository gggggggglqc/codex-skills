# 成本来源约定 — V6.5.1

本约定用于消除销售模块文档中“采购价、融合表、成本价”的叫法歧义。

| 业务称谓 | 唯一物理来源 | 可用字段 |
|---|---|---|
| 融合表 / 融合采购价 | `dp_dim.doris_dim_sku_cost_price` | `tax_freight_price`、`no_tax_freight_price`、`no_tax_price`、`brand_quotation` |
| 成本价 / 结存价 / 月末成本价 | `dp_dim.doris_dim_stock_cost` | `cost_price`、`delivery_cost_price` 等成本价字段 |
| 阶梯价格 | `dp_dim.doris_dim_srm_billing_purchase_ladder_price` | `tax_freight_price`、`no_tax_freight_price` |
| 采购成本表（含返利成本） | `srm_billing.purchase_cost_price` | `purchase_cost_price`、`cost_price`、`rebate_amount` |
| 货主返利策略 | `dp_dim.doris_dim_owner_markup_rule` | `rebate_rate` |
| 仓库维度 | `dp_dim.doris_dim_warehouse` | 仓库所在区域以仓库维表为准；区域字段将在后续上线时增加 |

不得把“融合表采购价”写到 `doris_dim_stock_cost`，也不得把“结存/出库成本价”写到 `doris_dim_sku_cost_price`。
