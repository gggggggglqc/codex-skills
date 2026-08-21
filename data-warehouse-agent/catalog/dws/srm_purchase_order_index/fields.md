# 字段与采购订单指标映射

| 指标组 | 核心字段/规则 |
|---|---|
| 商品行标识 | `purchase_line_id`、`purchase_order_id` |
| 订单数量 | `original_number`、`current_number`、`demand_num`、`delivery_num`、`receive_num`、`in_transit_num`、`actual_receive_num`、`reject_num` |
| 订单金额 | `no_tax_freight_price`、`no_tax_freight_total`、`tax_freight_price`、`tax_freight_total` |
| 采购订单量 | `COUNT(DISTINCT purchase_order_id)`，限制 `demand_num <> 0` |
| 交收状态 | `settlement_status`：10 未交收、20 发货在途、30 部分交收、40 全部交收、50 超量交收 |
| 状态与动作时间 | `status`、`audit_status`、`create_time`、`submit_time`、`audit_time`、`confirm_time`、`update_time` |
| 维度 | 商品类目、供应商、仓库、采购组织、创建/提交/审核/确认人员、主跟单员、单位 |

订单状态 `90` 为已取消；交收状态 `20` 是库存“发货在途库存”规则使用的状态值。
