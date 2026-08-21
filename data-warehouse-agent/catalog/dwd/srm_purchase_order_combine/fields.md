# 字段与采购指标映射

| 指标组 | 核心物理字段 |
|---|---|
| 单据与状态 | `purchase_order_id`、`purchase_line_id`、`status`、`settlement_status`、`audit_status` |
| 商品与组织 | `goods_code`、`sku_code`、`spu_code`、`supplier_code`、`warehouse_code`、`purchase_group_code`、`unit_code` |
| 采购数量 | `original_number`、`current_number`、`demand_num`、`delivery_num`、`receive_num`、`in_transit_num`、`actual_receive_num`、`reject_num` |
| 采购金额 | `purchase_line_no_tax_freight_price`、`purchase_line_no_tax_freight_total`、`purchase_line_tax_freight_price`、`purchase_line_tax_freight_total` |
| 动作时间 | `create_time`、`submit_time`、`audit_time`、`confirm_time`、`update_time` |

订单取消状态明确为 `status = 90`；交收状态：10 未交收、20 发货在途、30 部分交收、40 全部交收、50 超量交收。
