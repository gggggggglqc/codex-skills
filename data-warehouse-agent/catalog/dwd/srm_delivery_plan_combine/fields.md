# 字段与库存指标映射（V6.5.1）

| 库存指标 | 关联/汇总字段 | 有效条件 |
|---|---|---|
| 未交收库存 `Undelivered_stock` | `SUM(demand_num - actual_receive_num)` | `is_delete = 1`；采购订单状态剔除“已取消” |
| 发货在途库存 `in_transit_stock` | `SUM(in_transit_num)` | `is_delete = 1`；采购订单状态剔除“已取消”；`settlement_status = 20`（发货在途） |

关联维度为 `plan_goods_code`、`plan_warehouse_code`、`plan_owner_code`；快照日期按 `dws.sku_stock_index.dt` 的自然日口径。业务源 `srm_ops.delivery_plan` 不含 `settlement_status`；通过采购订单 Index 确认“发货在途”编码为 `20`。
