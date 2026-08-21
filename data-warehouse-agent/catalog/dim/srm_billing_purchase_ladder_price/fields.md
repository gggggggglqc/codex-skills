# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区/加价月份 | `dt` / `add_price_month` | date / varchar |
| 商品 / 货品 / 仓库 / 货主 / 供应商 | `goods_code` / `spu_code` / `warehouse_code` / `owner_code` / `supplier_code` | varchar |
| 含税含运费单价 | `tax_freight_price` | decimal(21,7) |
| 不含税含运费单价 | `no_tax_freight_price` | decimal(21,7) |
| 含税/不含税单价 | `price` / `no_tax_price` | decimal(21,7) |
| 税率 / 单位运费 | `tax_rate` / `unit_freight` | decimal |
