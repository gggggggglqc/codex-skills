# 字段与库存指标映射（V6.5.1）

| 指标组 | 核心物理字段 |
|---|---|
| 日切片键 | `dt`、`goods_code`、`warehouse_code`、`owner_code`、`concat_md5` |
| 库存数量 | `authentic_total_stock`、`authentic_lock_stock`、`defective_total_stock`、`defective_lock_stock`、`all_stock`、`all_lock_stock`、`temporary_stock` |
| 补充库存 | `strategized_lock_stock`、`Undelivered_stock`、`in_transit_stock` |
| 月度成本单价 | `brand_quotation`（不含税）、`tax_brand_quotation`（含税） |
| 采购价单价 | `no_tax_purchase_price`、`tax_purchase_price` |
| 支付滚动指标 | `yst_sale_num`、`three_sale_num`、`seven_sale_num`、`fourteen_sale_num`、`month_sale_num`、`monthly_payment_qty`、`last_monthly_payment_qty` |
| 出库滚动指标 | `yst_delivery_num`、`three_delivery_num`、`seven_delivery_num`、`fourteen_delivery_num`、`month_delivery_num`、`monthly_qty`、`last_monthly_qty` |
| 有效出库滚动指标 | `yst_effective_delivery_num`、`three_effective_delivery_num`、`seven_effective_delivery_num`、`fourteen_effective_delivery_num`、`month_effective_delivery_num`、`monthly_effective_qty`、`last_monthly_effective_qty` |
| 商品与组织维度 | `warehouse_*`、`owner_*`、`brand_*`、`category_level*`、`supplier_*`、`department`、`business_group`、`goods_type`、`product_code` |

`strategized_lock_stock` 为当日有效策略锁定明细的 `SUM(apply_lock_stock)`：按 `warehouse_code + owner_code + goods_code` 汇总，关联策略主表后限制 `status = 1` 且主/明细表 `deleted != -1`。每日全量切片将结果写入当天 `dt`，本表自身保留历史。`Undelivered_stock` 与 DDL 中的字段大小写一致；其上游为 `dwd.srm_delivery_plan_combine` 的 `SUM(demand_num - actual_receive_num)`。`in_transit_stock` 上游为该表的 `SUM(in_transit_num)`，限制交收状态为“发货在途”。跨境订单 SKU 纳入库存出库指标；该边界独立于销售模块“跨境销售忽略”的范围。文档中的 `in_transit_lock` 对应内容已划删除线，不纳入当前有效字段。

月度成本规则见可见 Excel `v6.5.1库存指标`：不含税成本取 `dp_dim.doris_dim_district_stock_cost.cost_price`，限制“已关账、`accounting_organization = 1`”，按 `doris_dim_warehouse` 提供的仓库所在区域 + 商品取最大月份的最大成本价；为空、0 或关联失败时按仓库映射区域兜底。含税成本按同一规则取值后乘 `1.13`。区域存货成本表和仓库区域字段均为待上线能力；上线后补 DDL/字段对照并启用自动核查。
