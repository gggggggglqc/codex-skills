# 核对规则

## 核心目标

按核算月核对 `erp_cost.inventory_cost_details` 与 IOM/MES/业务单据汇总数量。业务侧来源单据支持使用可调整起止时间范围，定位：

- 成本侧未计算或少计算的业务单据。
- 成本侧多计算或业务侧过滤少取的数据。
- 货主归属错位。
- 跨类型抵平。
- 抵消关系导致的剔除差异。

## 核对范围

只核对配置内仓库。

## 日期范围

`calculation_month` 始终表示成本侧 `inventory_cost_details` 的核算月。

业务侧来源单据时间范围可通过 `--start-time / --end-time` 调整，左闭右开：

```text
[start_time, end_time)
```

如果不传起止时间，默认使用核算月整月。

如果总表使用了自定义业务时间范围，后续单据下探必须使用相同的 `--start-time / --end-time`。

排除：

- 虚拟仓、三方仓、样品仓等不参与核对的仓库类型。
- 样品货主。
- 已配置排除仓，例如 `WH0171`、`WH0454`。
- 已配置排除货主，例如 `OW018`。

集团仓使用出库单价；工厂仓使用结存单价。

## 数据方向

IOM 入库数量与 `inventory_cost_details.income_num` 核对。

IOM 出库数量与 `inventory_cost_details.delivery_num` 核对。

成本侧收入数量如为负数，按发出数量规则处理。

退货应收入库单和无单退货入库单在成本侧通常表现为发出数量负数，核对时按出库方向处理。

## 类型映射

| biz_type_code | 成本侧 | 业务侧 |
|---|---|---|
| RETURN_ORDER_IN | order_type=10 | erp_iom.return_order |
| NO_ORDER_RETURN_IN | order_type=30 | erp_iom.no_order_inbound_order |
| SALES_OUT | order_type=105 | erp_iom.delivery_order |
| DISTRIBUTION_OUT | order_type=110 | erp_iom.outbound_delivery_order |
| CBS_OUT | order_type=115 | erp_iom.cbs_delivery_order |
| DISTRIBUTION_RETURN_IN | order_type=15 | erp_iom.refund_stock_order |
| PRODUCE_SALE_RETURN_IN | order_type=67 | mes_order.return_order |
| DELIVERY_REJECT_IN | order_type=69 | mes_order.reject_order |
| PRODUCE_SALE_OUT | order_type=167 | erp_iom.produce_sale_outbound_order |
| TAKE_MATERIAL_OUT | order_type=166 | erp_iom.take_material_stock_order |

## 数量字段

退货应收：

```sql
return_order_detail.arrive_num + COALESCE(return_order_detail.arrive_imperfect_num, 0)
```

无单退货：

```sql
sub_no_order_inbound_order.arrive_num + COALESCE(sub_no_order_inbound_order.arrive_defective_num, 0)
```

销售出库：

```sql
sub_delivery_order.goods_num
```

## 抵消口径

历史月份核对不能用当前业务表最新关联状态反推当时是否抵消。

如果用户要求严格历史月口径，只认：

```sql
cost_deduction_order.calc_month = 当前核算月
```

如果用户要求取消按计算月份过滤，则读取 `cost_deduction_order` 全量抵消关系。

当 4 月才建立关联，但核对 3 月时，应说明：

```text
现在看可以抵消，但 3 月核算当时关联关系不存在，所以不能倒推 3 月当时应抵消。
```

## 无单退货关系

无单退货通过退货应收确认关系时：

```text
no_order_inbound_order.relative_code = return_order.return_order_id
```

无单退货与销售出库抵消时，用无单退货自身数量与销售出库数量核对；退货应收用于确认 SKU 关系。

## 差异方向

入库：

```text
source_in_qty - inventory_income_qty > 0：成本侧比业务侧少
source_in_qty - inventory_income_qty < 0：成本侧比业务侧多
```

出库优先比较绝对值：

```text
abs(inventory_delivery_qty) < abs(source_out_qty)：成本侧比业务侧少
abs(inventory_delivery_qty) > abs(source_out_qty)：成本侧比业务侧多
```

定位缺失单据优先查“成本侧比业务侧少”。

## 常见模式

跨货主抵平：

同一 `warehouse_code + goods_code + biz_type_code` 下，一个货主成本侧多，另一个货主业务侧多，合计差异为 0。常见于 `OW0101` 与其他货主之间的退货应收货主归属错位。

跨类型抵平：

同一 `owner_code + warehouse_code + goods_code` 下，无单退货与销售出库一正一负抵平。

成本侧比业务侧多：

通常不是“业务单据缺失”，可能是成本侧多算、业务过滤少取、时间口径不同、货主错位或历史关联状态差异。

成本侧比业务侧少：

优先定位未参与成本计算的业务单据。

## 金额匹配

当总数量不能直接定位单据时，用单价和金额分桶：

```text
cost_source + cost_price + qty + amount
```

如果差异金额等于另一个货主同仓同 SKU 的某张业务单据金额，结论通常是货主错位，而不是单据完全未计算。

输出结论示例：

```text
不是存货侧完全没算，而是存货侧算到 A 货主，业务侧单据归属在 B 货主。
```

## 差异来源格式

`差异来源` 字段用三行说明：

```text
成本侧保留了这 -2749 个出库数量
业务侧 IOM return_order 退货应收统计了 -2715 个
所以产生差异 34
```

入库差异写“入库数量”；出库差异写“出库数量”。同一行入库和出库都差异时，用空行分隔。
