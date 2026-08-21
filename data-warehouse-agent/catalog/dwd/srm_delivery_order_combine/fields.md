# 字段与采购发货指标映射

| 指标 | 物理字段 |
|---|---|
| 发货/到货/实收/拒收数量 | `delivery_num`、`receive_num`、`actual_receive_num`、`reject_num` |
| 不含税含运费单价 / 含税含运费单价 | `no_tax_price` / `price` |
| 不含税含运费总额 / 含税含运费总额 | `no_tax_freight_total` / `tax_freight_total` |
| 单据状态及动作时间 | `status`、`create_time`、`delivery_time`、`arrived_date`、`receive_time`、`audit_time` |
| 成本关联键 | `delivery_order_id`、`goods_code`、`warehouse_code`、`purchase_line_id`、`purchase_order_id` |

发货单状态：0 编辑中、10 待出库、20 已发货、30 已收货、40 已入库、50 已取消。
