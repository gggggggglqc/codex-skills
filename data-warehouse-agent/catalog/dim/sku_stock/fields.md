# 字段与库存指标映射（V6.5.1）

| 库存逻辑指标 | 物理字段/公式 | 核对结论 |
|---|---|---|
| 正品总库存 | `total_stock` | 已确认 |
| 残品总库存 | `defective_total_stock` | 已确认 |
| 总库存 | `total_stock + defective_total_stock` | 与可见文档一致 |
| 正品锁定库存 | `lock_stock` | 已确认 |
| 正品可售库存 | `total_stock - lock_stock` | 与可见文档一致 |
| 可用库存 | 当前态：`total_stock + purchase_in_transit`；日切片：`authentic_total_stock + in_transit_stock` | 日切片 Index 已确认 `in_transit_stock` |
| 残品锁定库存 | `defective_lock_stock` | DDL 已有；文档第 17 行文字误写“残品可用库存”，需按指标名确认取值 |
| 残品可用库存 | `defective_total_stock - defective_lock_stock` | 与可见文档第 16 行一致 |
| 仓内暂存库存 | `temporary_stock` | 已确认 |
| 发货在途库存 | 当前态：`purchase_in_transit`；日切片：`in_transit_stock` | 日切片上游确认使用交货计划 `in_transit_num`；当前态字段与其是否同口径待核对 |

库存文档的“在途占用库存”对应 A20/C20，已为删除线内容，不纳入当前有效口径。正品策略锁定量按 `oms_strategy.stock_lock_detail.apply_lock_stock` 汇总：`lock_id = stock_lock.stock_lock_id`，过滤主表 `status = 1`、主/明细表 `deleted != -1`，并按 `warehouse_code + owner_code + goods_code` 对齐库存粒度。未交收库存和发货在途库存取 `dwd.srm_delivery_plan_combine`。
