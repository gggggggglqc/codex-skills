# 库存模块场景梳理与资料缺口 — V6.5.1

> 仅依据《库存模块.xlsx》的可见 Sheet 解析；隐藏 Sheet 已按产品要求忽略。

## 当前有效范围

| 场景 | 当前可见说明 Sheet | 已确认承载表 |
|---|---|---|
| 库存快照 | `v6.5.1库存指标` | `dp_dim.doris_dim_sku_stock`（当前态）→ `dp_dws.doris_dws_sku_stock_index`（按日切片） |
| 出入库商品 | `v6.5.1入库商品表`、`v6.5.1出库指标` | `doris_dws_inbound_and_outbound_index` |
| 出入库成本中间计算 | 同上 | `doris_dws_inbound_and_outbound_index_mid` |
| 工厂生产发货 | 出库指标及模块说明 | `doris_dws_mes_delivery_order_index` |
| 通用出入库事实 | 模块说明 | `doris_dwd_stock_order_combine` |
| 工厂单据事实 | 更新记录/模块说明 | 五张 MES Combine 已登记 |

## 已确认指标能力

- 库存快照：库存数量/货值、月度成本价、采购单价、支付与销售出库滚动指标、周转天数与次数。
- 出入库商品：正残品的要求、收货、实际入/出库数量及货值；采购、净利、品牌供货成本。
- 出入库类型：销售、分销、采购退、跨/仓内调拨、盘亏、报残/报损、维修、奇门、其他、MES 产销/领料出库；以及退货应收、分销退货、采购收货、调拨、盘盈、维修、MES 入库等。
- 工厂单据：生产销退、完工入库、产销出库、发货拒收、领料出库和生产发货。

## 已确认的月度成本规则

可见 Sheet `v6.5.1库存指标` 的 C3、C4 明确指定 `dp_dim.doris_dim_district_stock_cost`：限制“已关账”和 `accounting_organization = 1`；不含税月度成本取仓库所在区域 + 商品的最大月份、最大 `cost_price`，取不到、为 0 或关联失败时按仓库映射区域兜底；含税月度成本为同一 `cost_price × 1.13`。

## 已确认的工厂物料映射

`dp_dim.doris_dim_oms_product_factory_material` 已提供。工厂物料场景按 `factory_code + material_code` 关联，补充 `sku_code`（成品商品编码）和 `stock_type`（存货类别）；可用状态字段为 `enable`、`audit_status`。同一工厂物料出现多条有效记录时的优先级仍待业务确认。

## 已确认的采购交货计划映射

`dp_dwd.doris_dwd_srm_delivery_plan_combine` 已提供。未交收库存按 `SUM(demand_num - actual_receive_num)` 汇总；发货在途库存按 `SUM(in_transit_num)` 汇总。两者均限制 `is_delete = 1` 且采购订单状态剔除“已取消”；发货在途库存还限制 `settlement_status = 20`（发货在途）。

## 待补资料与确认

| 优先级 | 待补项 | 原因/用途 |
|---|---|---|
| 中 | 当前有效版本确认 | 可见指标 Sheet 为 V6.5.1；更新记录还有更晚的 DWP V6.4.9.4，需确认本期采用范围 |

## 已确认待上线依赖

- 成本价组织字段 `accounting_organization` 计划月底上线；库存月度成本价按可见 V6.5.1 文档限制为 `1`。
- `dp_dim.doris_dim_district_stock_cost` 是区域存货成本新表，当前尚未上线；上线后需补 DDL，并启用月度含/不含税成本价的自动核查。
- `dp_dim.doris_dim_warehouse` 的仓库所在区域字段将在后续上线时增加；上线后补充字段名及其与采购价格区域键的对应，并启用区域取价核查。

> `v6.5.1库存指标` 的 A20、B20、C20（在途占用库存 / `in_transit_lock`）均为删除线，已按产品规则排除。

## 已确认的 DWS 技术属性

| 表 | UNIQUE KEY | `dt` 分区 | 历史分区保留 |
|---|---|---|---|
| `doris_dws_inbound_and_outbound_index` | `dt, inbound_and_outbound_sub_order_id, goods_code` | 月 RANGE 动态分区 | 0 |
| `doris_dws_inbound_and_outbound_index_mid` | `dt, inbound_and_outbound_sub_order_id, goods_code` | 月 RANGE 动态分区 | 17 |
| `doris_dws_mes_delivery_order_index` | `dt, detail_id` | 月 RANGE 动态分区 | 2 |
| `doris_dws_sku_stock_index` | `dt, goods_code, warehouse_code, owner_code` | 月 RANGE 动态分区 | 24 |

四表动态分区时区均为 `Asia/Shanghai`。前三张出入库相关表实际任务均为每日先删后新增，重算近 90 天；库存日切片 Index 每日先删后新增全量更新。
