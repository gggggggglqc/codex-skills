# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 仓库 / 商品 | `warehouse_code` / `goods_code` | varchar |
| 价格类型 / 生效期 | `cost_type` / `price_start_time` / `price_end_time` | tinyint / date |
| 含税含运费单价 | `tax_freight_price` | decimal(18,5) |
| 不含税含运费单价 | `no_tax_freight_price` | decimal(18,5) |
| 品牌供货价 | `brand_quotation` | decimal(19,5) |
| 含税/不含税单价 | `price` / `no_tax_price` | decimal(18,5) |
