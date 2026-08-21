# 字段与采购价格指标映射

| 指标组 | 核心字段/规则 |
|---|---|
| 条目和有效期 | `purchase_price_id`、`start_time`、`end_time`、`status`、`time_type` |
| 价格 | `no_tax_price`、`tax_rate`、`price`、`unit_freight`、`no_tax_freight_price`、`tax_freight_price` |
| 匹配维度 | `goods_code`、`sku_code`、`spu_code`、`supplier_code`、`warehouse_code`、`purchase_group_code`、`unit_code` |
| 时间类型 | `time_type = 0` 下单时间；`time_type = 1` 到货时间 |
| DDL 状态 | `status = 0` 生效；`status = 1` 失效 |

采购模块 Excel 的修饰词写“有效（1）/无效（2）”，与业务库、维表 DDL 不一致，已判定为历史/错误说明。当前过滤固定以业务库为准：`status = 0` 生效、`status = 1` 失效。
