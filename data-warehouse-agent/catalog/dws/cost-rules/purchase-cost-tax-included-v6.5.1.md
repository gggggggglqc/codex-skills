# 采购成本（含税）规则 — V6.5.1

## 输出字段

| DWS 资产 | 输出字段 | 数量基数 |
|---|---|---|
| `dws.trade_order_goods_index` | `purchase_price_total` | 系统订单 `num` |
| `dws.dms_trade_order_index` | `purchase_price_total` | 分销订单 `num` |
| `dws.dms_delivery_index` | `purchase_price_total` | 分销发货 `delivery_num` |

输出为“选定的含税含运费单价 × 对应商品数量”。退款分支归售后模块。

## 数据源强制约束

- **采购阶梯价**：只使用 `dp_dim.doris_dim_srm_billing_purchase_ladder_price.tax_freight_price`。
- **融合表采购价**：只使用 `dp_dim.doris_dim_sku_cost_price.tax_freight_price`，限制 `cost_type = 2`。
- **成本价**：只使用 `dp_dim.doris_dim_stock_cost.cost_price`；含税换算为 `cost_price × 1.13`。
- “仓库所在区域”以订单仓库编码关联 `dp_dim.doris_dim_warehouse` 取得，不直接使用原始仓库编码；区域字段将在后续上线时增加。

## 系统订单商品

### 已发货

1. 按“仓库 + 商品 + 货主 + 发货时间所在月份”查询采购阶梯价格，取 `tax_freight_price`；多条取最高价。
2. 空或 0 时，按“仓库所在区域 + 商品 + 发货时间”查询融合表，取 `tax_freight_price`；多条先取 `price_start_time` 最晚，再取最高价。
3. 空或 0 时，按“商品 + 发货时间”查询融合表，取最近生效的 `tax_freight_price`；多条先取 `price_start_time` 最晚，再取最高价。
4. 仍为空或 0 时，单价为 0。

### 未发货

1. 按“商品 + 支付时间”查询成本价表，取支付时间所在月的上月已关账成本价：`cost_price × 1.13`；限制 `is_closed = 1`。
2. 空或 0 时，按“商品 + 支付时间”查询融合表，取 `tax_freight_price`；多条先取 `price_start_time` 最晚，再取最高价。
3. 仍为空或 0 时，单价为 0。

## 分销订单商品

1. 按“仓库 + 商品 + 货主 + 创建时间所在月份”查询采购阶梯价格，取 `tax_freight_price`；多条取对应月份最高价。
2. 空或 0 时，按“仓库所在区域 + 商品 + 创建时间”查询融合表，取 `tax_freight_price`；多条先取 `price_start_time` 最晚，再取最高价。
3. 空或 0 时，按“商品 + 创建时间”查询融合表，取最近生效的 `tax_freight_price`；多条取最高价。
4. 仍为空或 0 时，单价为 0。

## 分销发货单商品

1. 按“仓库 + 商品 + 发货时间所在月份”查询采购阶梯价格，取 `tax_freight_price`；多条取对应月份最高价。
2. 空或 0 时，按“仓库所在区域 + 商品 + 发货时间”查询融合表，取 `tax_freight_price`；多条先取 `price_start_time` 最晚，再取最高价。
3. 空或 0 时，按“商品 + 发货时间”查询融合表，取最近生效的 `tax_freight_price`；多条取最高价。
4. 仍为空或 0 时，单价为 0。

## 来源与版本

- 产品口径：`销售模块.xlsx` → `基础指标-商品v6.5.1`，第 19、49、62 行。
- 生效版本：V6.5.1。
- 变更日期：2026-08-13。
