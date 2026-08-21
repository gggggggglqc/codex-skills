# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 成本价格主键 / 来源价格 | `cost_price_id` / `source_price_id` | varchar(64) |
| 商品 / 货品 / 仓库 / 货主 / 供应商 | `goods_code` / `spu_code` / `warehouse_code` / `owner_code` / `supplier_code` | varchar(64) |
| 成本月份 / 返利规则 | `month` / `rebate_rule` | varchar |
| 原不含税价 / 返利比例 / 返利金额 | `source_no_tax_price` / `rebate_ratio` / `rebate_amount` | decimal(21,7) |
| 采购成本价 / 成本价 / 上月存货成本 | `purchase_cost_price` / `cost_price` / `last_month_cost_price` | decimal(21,7) |
| 不含税含运费 / 含税含运费单价 | `no_tax_freight_price` / `tax_freight_price` | decimal(21,7) |
| 成本索引 | `(goods_code, warehouse_code, owner_code)` / `month` | MySQL index |
