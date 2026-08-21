# ODS 资产目录

ODS 只记录原始数据层已知的表与字段事实。字段清单应由正式 DDL、数据字典或数仓开发确认补齐；DAS 中出现的字段只能作为“应用读取证据”。

## 首批登记

| 资产 ID | 候选物理表 | 状态 | 已知用途 |
|---|---|---|---|
| `ods.upload_expense_detail` | `doris_ods_upload_expense_detail` | 待数仓确认 | 推广费、费用明细 |
| `ods.fms_cost_psi_sales` | `doris_ods_fms_cost_psi_sales` | 待数仓确认 | 销售与 T+1 核查 |
| `ods.fms_cost_psi_delivery_sales` | `doris_ods_fms_cost_psi_delivery_sales` | 待数仓确认 | 发货/销售分析 |
| `ods.fms_cost_psi_factory_sales` | `doris_ods_fms_cost_psi_factory_sales` | 待数仓确认 | 产销销售分析 |
| `ods.sku_estimate_sales` | `doris_ods_sku_estimate_sales` | 待数仓确认 | SKU 目标日销/月销 |
| `ods.zcm_cost_attribution` | `doris_ods_zcm_cost_attribution` | 待数仓确认 | 成本归属 |
| `ods.zcm_cost_item` | `doris_ods_zcm_cost_item` | 待数仓确认 | 成本项目 |
| `ods.erp_auth_ding_department` | `doris_ods_erp_auth_ding_department` | 待数仓确认 | 部门组织 |
| `ods.das_core_buyer_appraise` | `doris_ods_das_core_buyer_appraise` | 待数仓确认 | 买家评价 |

`doris_ods_SKU_estimate_sales` 与 `doris_ods_sku_estimate_sales` 的大小写差异已登记为待确认项，暂归并为同一资产。

## 销售模块已确认来源（V6.5.1）

| 资产 ID | 物理表 | 粒度 | 主要下游 |
|---|---|---|---|
| `ods.oms_order` | `doris_ods_oms_order` | 原始订单子单商品行 | `dws.trade_order_goods_index` |
| `ods.oms_refund` | `doris_ods_oms_refund` | 原始退款单主单行 | 原始订单退款口径待补 ETL |
| `ods.dms_trade_order` | `doris_ods_dms_trade_order` | 分销订单主单行 | `dws.dms_trade_order_index` |
| `ods.dms_sub_trade_order` | `doris_ods_dms_sub_trade_order` | 分销订单子单商品行 | `dws.dms_trade_order_index` |
| `ods.dms_sub_delivery_order` | `doris_ods_dms_sub_delivery_order` | 分销发货单子订单商品行 | `dws.dms_delivery_index` |
| `ods.dms_delivery_order` | `doris_ods_dms_delivery_order` | 分销发货单主单行 | `dws.dms_delivery_index` |
| `ods.dms_refund_delivery_order` | `doris_ods_dms_refund_delivery_order` | 分销退货发货主单行 | 退货商品级血缘待补 |
| `ods.trade_order` | `doris_ods_trade_order` | 系统订单主单行 | `dws.trade_order_goods_index` |
| `ods.sub_trade_order` | `doris_ods_sub_trade_order` | 系统订单子单商品行 | `dws.trade_order_goods_index` |
| `ods.trade_order_ext` | `doris_ods_trade_order_ext` | 系统订单主单扩展行 | 系统订单时效/分销商扩展 |
