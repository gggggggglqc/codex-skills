# 字段说明

| 业务字段 | 物理字段 | 说明 |
|---|---|---|
| 自然日快照 | `dt` | 按业务 `dt = dt` 关联 |
| 内部店铺编码 | `shop_code` | 与 Index 的店铺编码关联 |
| 公司编码 | `company_code` | 用于继续关联 `dim_company.company_code`；店铺禁用或未绑定公司编码时税率按 0 处理 |
| 公司名称 | `company_name` | 公司名称冗余展示字段 |
