# 字段与指标映射（库存模块 V6.5.1）

| 指标组 | 核心物理字段 |
|---|---|
| 单据、方向与时间 | `inbound_and_outbound_order_id`、`inbound_and_outbound_sub_order_id`、`in_or_out_stock`、`inbound_and_outbound_type`、`inbound_and_outbound_status`、`create_time`、`inbound_time`、`outbound_time` |
| 订单关联 | `order_id`、`sub_order_id`、`refund_order_id`、`relative_code`、`sub_source_order_id` |
| 入库数量与货值 | `require_*`、`arrive_*`、`inbound_genuine_sku_*`、`inbound_defective_sku_*` |
| 出库数量与货值 | `outbound_genuine_sku_*`、`outbound_defective_sku_*` |
| 入库成本 | `inbound_brand_quotation`、`inbound_no_tax_price`、`inbound_no_tax_freight_price`、`inbound_tax_freight_price`、`inbound_price`、`inbound_product_cost`、`inbound_no_tax_product_cost` |
| 出库成本 | `outbound_brand_quotation`、`outbound_no_tax_price`、`outbound_no_tax_freight_price`、`outbound_tax_freight_price`、`outbound_price`、`outbound_product_cost`、`outbound_no_tax_product_cost` |
| 商品/组织/工厂 | `goods_code`、`spu_code`、`goods_type`、`owner_*`、`warehouse_*`、`factory_*`、`finished_sku_code`、`unit_*`、`country_code` |

`outbound_defective_sku_payment` 在 DDL 中标注为预留、暂不开发，不作为当前有效指标。

非 IOM（MES 等）来源不要求映射为统一的细分单据类型、状态；保留来源事实表及其原始状态字段。该约定不影响出/入库方向、数量、成本或库存余额计算。
