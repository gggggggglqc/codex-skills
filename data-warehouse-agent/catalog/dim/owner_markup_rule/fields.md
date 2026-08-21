# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 策略主键 | `id` | bigint |
| 货品 / 货主 / 加价月份 | `spu_code` / `owner_code` / `month` | varchar / date |
| 返利比率 | `rebate_rate` | decimal(19,6) |
| 命中规则 / 销量 / 排名 | `hit_rule` / `sales_volume` / `sales_ranking` | varchar / int |
