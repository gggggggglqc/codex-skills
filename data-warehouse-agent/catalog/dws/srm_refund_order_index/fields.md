# 字段与采购退货指标映射

| 指标组 | 核心字段 |
|---|---|
| 单据与状态 | `refund_id`、`sub_refund_id`、`refund_status`、`refund_source` |
| 数量与价格 | `deliver_num`、`actual_receive_num`、`refund_price`（DWD 同名不含税字段直接透传）、`tax_price`（含税退货单价） |
| 商品与组织 | `goods_code`、`sku_code`、`spu_code`、`supplier_code`、`owner_code`、`warehouse_code`、`brand_*`、`category_level*` |
| 动作与物流 | `create_time`、`submit_time`、`delivery_time`、`receipt_time`、`express_code`、`logistics_company` |

退单状态：10 编辑中、20 待审核、30 待出库、40 已发货、50 已收货、60 已取消；退货来源：1 自营仓退货、2 代发仓退货。

`refund_price` 已确认是 DWD 的不含税退货单价，DWS 直接透传，不做税额换算。
