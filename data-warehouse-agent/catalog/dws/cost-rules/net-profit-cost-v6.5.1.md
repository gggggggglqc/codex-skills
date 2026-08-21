# 净利成本规则 — V6.5.1

## 输出映射

| 业务事实 | 含税净利成本 | 不含税净利成本 | 当前有效规则 |
|---|---|---|---|
| 系统订单商品 | `product_cost` | `no_tax_product_cost` | 不含税 = 含税净利成本 − 进项税额（成本） |
| 分销订单商品 | `product_cost` | `no_tax_product_cost` | 仍按文档直接不含税取价链计算 |
| 分销发货单商品 | `product_cost` | `no_tax_product_cost` | 不含税 = 含税净利成本 − 进项税额（成本） |

## 系统订单商品

### 含税净利成本

1. 已发货：按商品、发货时间查询上月已关账 `dp_dim.doris_dim_stock_cost.cost_price`，取 `cost_price × 1.13`；空或 0 时，按商品、发货时间查询 `dp_dim.doris_dim_sku_cost_price.tax_freight_price`（`cost_type = 2`）。
2. 未发货：按商品、支付时间查询上月已关账成本价，取 `cost_price × 1.13`；空或 0 时，按商品、支付时间查询融合表 `tax_freight_price`（`cost_type = 2`）。
3. 单价为空或 0 时取 0，总额乘下单数量 `num`。

### 不含税净利成本

`no_tax_product_cost = product_cost - input_tax_amount`。

其中 `input_tax_amount` 取值如下：

- 当公司性质为小规模纳税人（`company_nature = 1`）时：`0`。
- 其他公司性质（一般纳税人及个体户）：`product_cost / (1 + company_tax_rate) × company_tax_rate`。

`company_tax_rate` 通过业务 `dt + shop_code → dp_dim.doris_dim_shop.company_code → dp_dim.doris_dim_company.tax_rate` 取得；计算时将税率转换为小数。店铺禁用或未绑定公司编码时，税率取 0。

## 分销订单商品

### 含税净利成本

1. 按商品、创建时间查询上月已关账 `stock_cost.cost_price`，取 `cost_price × 1.13`。
2. 空或 0 时，按商品、创建时间查询融合表 `sku_cost_price.tax_freight_price`（`cost_type = 2`）。
3. 单价为空或 0 时取 0，总额乘下单数量 `num`。

### 不含税净利成本

1. 按商品、创建时间查询上月已关账 `stock_cost.cost_price`。
2. 空或 0 时，按商品、创建时间查询融合表 `sku_cost_price.no_tax_freight_price`（`cost_type = 2`）。
3. 单价为空或 0 时取 0，总额乘下单数量 `num`。

## 分销发货单商品

### 含税净利成本

1. 按商品、发货时间查询上月已关账 `stock_cost.cost_price`，取 `cost_price × 1.13`。
2. 空或 0 时，按商品、发货时间查询融合表 `sku_cost_price.tax_freight_price`（`cost_type = 2`）。
3. 单价为空或 0 时取 0，总额乘发货数量 `delivery_num`。

### 不含税净利成本

`no_tax_product_cost = product_cost - input_tax_amount`。

其中 `input_tax_amount` 取值如下：

- 当公司性质为小规模纳税人（`company_nature = 1`）时：`0`。
- 其他公司性质（一般纳税人及个体户）：`product_cost / (1 + company_tax_rate) × company_tax_rate`。

`company_tax_rate` 通过业务 `dt + shop_code → dp_dim.doris_dim_shop.company_code → dp_dim.doris_dim_company.tax_rate` 取得；计算时将税率转换为小数。店铺禁用或未绑定公司编码时，税率取 0。

## 计算注意

- “不是小规模公司”按当前公司维表编码理解为 `company_nature <> 1`，即一般纳税人（0）与个体户（2）均按税率公式计算。
- 公司税率取店铺绑定公司在公司维表中的 `tax_rate`；店铺禁用或未绑定公司编码时税率为 0。
- 分销订单是否也应统一采用“含税净利成本减进项税额”新算法，当前最新文档没有如此规定，暂不推断。

## 来源与版本

- 产品口径：`销售模块.xlsx` → `基础指标-商品v6.5.1`，第 21、22、51、52、64、65 行。
- 生效版本：V6.5.1。
