# 字段与采购退货指标映射

| 指标组 | 核心字段 |
|---|---|
| 单据、状态与来源 | `refund_id`、`sub_refund_id`、`refund_status`、`refund_source`、`receipt_delay_status` |
| 数量与价格 | `deliver_num`、`actual_receive_num`、`refund_price`、`tax_price` |
| 商品与组织 | `goods_code`、`sku_code`、`spu_code`、`supplier_code`、`owner_code`、`warehouse_code`、`goods_type` |
| 动作与物流 | `create_time`、`submit_time`、`delivery_time`、`receipt_time`、`audit_time`、`express_code`、`logistics_company` |

退单状态：10 编辑中、20 待审核、30 待出库、40 已发货、50 已收货、60 已取消；退货来源：1 自营仓、2 代发仓。`refund_price` 在此 DWD 注释为“退货单价”，而 DWS 注释为“不含税退货单价”，税口径待确认。
