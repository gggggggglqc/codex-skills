# 字段与指标映射（售后模块 V6.5.1）

> 本表以 DDL 为物理字段依据；售后 Excel 的删除线指标不作为当前口径。字段计算公式待取得 ETL SQL 后可继续核查。

## 主键、关联与公共维度

| 逻辑字段 | 物理字段 | 说明 |
|---|---|---|
| 分区日期 | `dt` | 系统退单主单创建时间日期；非业务申请/退款时间 |
| 系统退单子单/主单 | `dt + sub_refund_id` / `refund_id` | 前者为物理唯一键；后者为系统退单主单标识 |
| 原始退单/订单/子单 | `source_refund_id` / `source_order_id` / `source_sub_order_id` | 原始售后与订单追溯 |
| 系统订单/子单 | `order_id` / `sub_order_id` | 关联系统订单成本、数量和费用 |
| 商品、货品、平台商品 | `goods_code` / `spu_code` / `sku_code` / `plat_*` | 商品维度 |
| 店铺、公司、货主、仓库、分销商、供应商 | `shop_*` / `company_*` / `owner_*` / `warehouse_*` / `distributor*` / `supplier_*` | 组织与履约维度 |

## 售后金额、数量与成本

| 逻辑指标 | 物理字段 | 口径说明 |
|---|---|---|
| 系统退单商品退款数量 / 退款金额 | `num` / `refund_fee` | 系统退单子单事实 |
| 关联系统订单购买数量 / 实发数量 / 分摊邮费 / 实付 | `trade_num` / `actual_num` / `share_post_fee` / `payment` | 关联系统订单子单口径 |
| 商品供货成本（已乘退款数量） | `brand_quotation` | 当前有效的供货总成本字段 |
| 系统订单预估品牌成本 | `estimate_brand_quotation` | DDL 已明确标记废弃，不作为当前参考 |
| 采购成本（含税/不含税，已乘退款数量） | `purchase_price_total` / `no_tax_purchase_price_total` | 退单成本比例还原结果 |
| 净利成本（含税/不含税，已乘退款数量） | `product_cost` / `no_tax_product_cost` | 退单成本比例还原结果 |
| 返利比率 | `rebate_rate` | 销售模块已确认的货主返利策略规则可复用 |
| 返利不含税采购价（已乘退款数量） | `no_tax_price` | 以当前售后 Excel 的指标名称解释；DDL 注释为“不含税采购价” |
| 退单返利成本金额 / 返利成本进项税额 | `rebate_cost_amount` / `input_tax_amount_rebate` | 均已落 Index，数量基数为退货数量 |

## 税额、状态与业务时间

| 逻辑指标/修饰词 | 物理字段 | 说明 |
|---|---|---|
| 税率 / 不含税退款金额 | `tax_rate` / `no_tax_refund_fee` | 退单收入税相关字段 |
| 退款销项税额 / 退款进项税额（成本） | `refund_output_tax_amount` / `refund_input_tax_amount` | DDL 已落物理字段 |
| 售后类型 / 阶段 | `after_sale_business_type` / `after_sale_stage` | 退款、退换、换货；售后、售中 |
| 申请 / 客户退货 / 商家退款时间 | `apply_time` / `good_return_time` / `return_time` | 售后动作时间 |
| 是否发货 | `delivery_status` | 0 未发货；1 已发货 |
| 主单 / 子单商家收货状态 | `receipt_status` / `sub_receipt_status` | 1 已收货；2 部分收货；3 未收货 |
| 原始/系统退单状态、订单状态 | `source_refund_plat_status` / `refund_status` / `original_*` / `inner_status` / `sub_inner_status` | 具体枚举以 DDL 注释为准 |

## 当前缺失或待确认

1. `receipt_status`、`sub_receipt_status` 直接使用 Index 既有结果；本期不从应收入库主子单反推或核查。
2. `dt` 是主单创建日期，与申请、客户退货、商家退款、发货等业务日期不同；各指标的查询分区/增量窗口待确认。
3. 表为 `UNIQUE KEY(dt, sub_refund_id)`、按月动态分区；每日覆盖更新滚动近 31 天数据。
