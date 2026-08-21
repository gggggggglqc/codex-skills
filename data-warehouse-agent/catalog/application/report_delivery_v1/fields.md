# 发货 V1 字段字典

## 时间与维度

| 字段组 | 物理字段 |
|---|---|
| 业务日期 | `dt`：系统/分销发货取发货日期；出入库取入库日期；系统退款取退款日期；分销退款取收货日期 |
| 店铺与组织 | `plat_code`、`shop_*`、`structure_id`、`department`、`company_code`、`company`、`business_group` |
| 商品 | `spu_*`、`sku_*`、`plat_spu_*`、`plat_sku_*`、`plat_goods_code`、`goods_category`、`category_level1~4`、`brand_*` |
| 经营属性 | `sales_model`、`country_code`、`country_name_cn`、`warehouse_*`、`distributor_*`、`supplier_*`、`is_stop_orders`、`is_defective`、`cbs_platform` |
| 达人与直播 | `author_id`、`author_name`、`is_self_live_stream` |

## 数量、收入与成本

| 应用指标 | 物理字段 | DDL 汇总口径要点 |
|---|---|---|
| 财务销售数量 / 退款数量 | `paid_num` / `refund_num` | 国内发货减各类退货入库，并叠加易仓/自研跨境发货及退款 |
| 财务销售收入 / 退款金额 | `sales_amount` / `refund_amount` | 国内发货收入减国内退款，叠加经易仓 DWS 接入的跨境差异历史数据及自研跨境；退款金额包含系统、分销及自研跨境退款 |
| 未发货退款 | `undelivery_refund_amount` / `undelivery_refund_num` | 系统、分销及自研跨境未发货退款 |
| 销售供货成本 / 退款供货成本 | `estimate_brand_quotation` / `refund_brand_quotation` | 国内发货减退款，并包含 DDL 指定的自研跨境成本 |
| 含税采购成本 / 退款含税采购成本 | `purchase_price_total` / `refund_purchase_price_total` | 国内、经易仓 DWS 接入的跨境差异历史数据、自研跨境及退款抵减 |
| 不含税采购成本 / 退款不含税采购成本 | `no_tax_purchase_price_total` / `refund_no_tax_purchase_price_total` | 同上，使用不含税含运成本口径 |
| 含税净利成本 / 退款净利成本 | `purchase_cost` / `refund_product_cost` | 国内与自研跨境发货减退款 |
| 不含税净利成本 / 退款净利成本 | `no_tax_product_cost` / `refund_no_tax_product_cost` | 国内与自研跨境发货减退款 |
| 不含税收入、销项/进项税额 | `no_tax_payment`、`output_tax_amount`、`input_tax_amount`、`input_tax_amount_rebate` | 国内系统/分销订单与退单的收入、税额抵减；销项含天猫超市税额，返利成本进项税额单列 |
| 返利成本 | `rebate_amount` | 系统订单 + 分销发货 − 系统退单 − 分销退单 |
| 体积 | `sku_volume` | SKU 体积 × 财务销售数量，另包含自研跨境体积 |

`distributor_settle_shop_code`、结算店铺名称未出现在 DDL；二者属于后续开发字段，不纳入当前 V1 表结构范围。
