# 字段与采购发货指标映射

| 指标 | 物理字段/公式 |
|---|---|
| 发货、到货、实收、拒收数量 | `delivery_num`、`receive_num`、`actual_receive_num`、`reject_num` |
| 不含税/含税含运费单价 | `no_tax_price` / `price` |
| 不含税发货收入总额 | `no_tax_delivery_income_total = price × actual_receive_num ÷ 1.13` |
| 不含税出库成本单价/总额 | `no_tax_cost_price` / `no_tax_cost_price_total` |
| 工厂物料与货主 | `material_code`、`material_name`、`factory_code`、`owner_code`、`owner_name`；收货仓库 → 工厂绑定表 → 工厂物料表（`goods_code = sku_code`） |
| 状态与动作时间 | `status`、`create_time`、`delivery_time`、`arrived_date`、`receive_time`、`audit_time` |

`no_tax_cost_price` 的具体取数分支以采购文档为准：产销出库成本优先，存货成本 `delivery_cost_price` 兜底。`cost_price` 与 `delivery_cost_price` 均已确认是不含税价，直接写入，不再做除税换算。
