# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区/计价月份 | `dt` / `calculation_month` | date / varchar |
| 商品 / 货主 / 仓库 | `goods_code` / `owner_code` / `warehouse_code` | varchar |
| 结存单价 / 出库成本价 | `cost_price` / `delivery_cost_price` | decimal(18,6) |
| 关账 / 成本类型 | `is_closed` / `company_cost_price_type` / `cost_price_category` | tinyint / int |
| 成本价组织 | `accounting_organization` | 计划于月底上线；售后分销退货成本限制为 `1`，正向销售不筛选 |
| 总成本 / 头程成本 | `total_cost_price` / `first_mile_cost_price` | decimal(18,6) |
