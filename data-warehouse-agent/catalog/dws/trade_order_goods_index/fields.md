# 字段与指标映射（V6.5.1）

> 物理字段、类型和完整注释以建表语句为准。本表只列销售模块当前口径的核心映射；未列出的 DDL 字段仍可从来源 DDL 追溯。

## 主键、关联与公共维度

| 逻辑字段 | 物理字段 | 类型 | 说明 |
|---|---|---|---|
| 分区/下单日期 | `dt` | date | 分区字段，下单日期 |
| 系统订单子单 ID | `sub_order_id` | varchar(150) | 与 `dt` 组成唯一键 |
| 系统订单 ID | `order_id` | varchar(150) | 系统主单 |
| 原始订单/子单 ID | `source_order_id` / `source_sub_order_id` | varchar | 原始订单关联线索 |
| 商品/货品 | `sku_code` / `spu_code` | varchar(150) | 商品编码 / 货品编码 |
| 商品/货品名称 | `sku_name` / `spu_name` | varchar | 系统内部规格名称 / 货品名称 |
| 平台货品/规格 | `plat_spu_id` / `plat_sku_id` | varchar(150) | 平台商品维度 |
| 店铺、货主、仓库、分销商 | `shop_*` / `owner_*` / `warehouse_*` / `distributor*` | varchar | 公共组织与履约维度 |
| 类目、品牌、供应商 | `category_level1..4` / `brand_*` / `supplier_*` | varchar | 商品公共维度 |

## 原始订单商品指标

| 逻辑指标 | 物理字段 | 状态 |
|---|---|---|
| 原始订单商品数量、商家优惠、总价、商家分摊优惠、分摊邮费、已付金额、退款金额 | 待确认 | 待提供 ETL SQL 或字段对照；DDL 未用明确注释区分原始订单指标 |

## 系统订单商品指标

| 逻辑指标 | 物理字段 |
|---|---|
| 下单数量 / 实发数量 | `num` / `actual_num` |
| 货款 / 商家优惠 / 商品总价 | `paid_amount` / `detail_discount_fee` / `sub_total_fee` |
| 应收金额 / 商家分摊优惠 / 分摊邮费 / 已付金额 | `should_pay` / `share_discount` / `share_post_fee` / `payment` |
| 退款金额 | `refund_fee` |
| 采购成本（含税）总额 | `purchase_price_total`；规则见 `catalog/dws/cost-rules/purchase-cost-tax-included-v6.5.1.md` |
| `no_tax_purchase_price_total` | DDL 已存在，但“系统订单商品采购成本（不含税）（已乘下单数量）”在 V6.5.1 最新文档中为删除线历史口径；当前业务含义/使用范围待 ETL SQL 确认 |
| 净利成本（含税）/（不含税）总额 | `product_cost` / `no_tax_product_cost`；规则见 `catalog/dws/cost-rules/net-profit-cost-v6.5.1.md` |
| 系统订单商品返利不含税采购价（已乘下单数量） | `no_tax_price`；以当前业务确认的下单数量口径为准，DDL 的“退货数量”注释已过期 |
| 返利比率 / 返利成本金额 / 返利成本进项税额 | `rebate_rate` / `rebate_cost_amount` / `input_tax_amount_rebate`；返利比率规则见 `catalog/dws/cost-rules/owner-rebate-rate-v6.5.1.md` |
| 供货成本 / 预估供货成本 | `brand_quotation` / `estimate_brand_quotation`；融合价兜底只取 `doris_dim_sku_cost_price` |
| 分摊包材费 | `package_fee` |
| 预估物流费（主单/子单） | `estimate_logistics_fee` / `sub_estimate_logistics_fee` |
| 子单自发费 / 代发费 | `sub_logistics_cost_fee` / `sub_agent_delivery_fee` |
| 实际结算自发费 / 代发费 | `actual_settle_incurred_fee` / `actual_settle_agency_fee` |

## 组合装指标

| 逻辑指标 | 物理字段 | 规则 |
|---|---|---|
| 组合装编码 / 数量 | `combine_code` / `combine_num` | 组合装数量汇总按原始子订单去重 |
| 组合装优惠、总价、分摊优惠、分摊邮费、已付、退款 | 使用上游系统订单已处理结果 | 原始订单 → 系统订单阶段已完成组合装拆分、分摊及去重；本 Index 不重复处理 |

## 修饰词/枚举

`order_function`、`sales_model`、`is_pre_sale`、`exit_warehouse_way`、`delivery_status`、`pay_status`、`inner_status`、`refund_status`、`sub_inner_status`、`detail_refund_status`、`gift_type`、`is_brand_fix_priced`、`is_self_research`、`is_eliminate`、`goods_source`、`goods_category`、`is_cooperation_logistic` 与 `source_sub_order_status` 的代码说明均以 DDL 为准；业务解释见 Excel 的“修饰词”“修饰词-商品专属”。

## 待确认映射

1. “返利后成本（不含税）”仅为派生返利成本金额的中间计算，不是本 Index 的输出字段。
2. 原始订单商品的七项金额/数量指标需由 ETL SQL 补充物理映射；组合装由上游系统订单完成处理，本 Index 不重复拆分。
3. 公司税率为空或店铺未关联公司的 `input_tax_amount` 兜底规则尚未提供。
