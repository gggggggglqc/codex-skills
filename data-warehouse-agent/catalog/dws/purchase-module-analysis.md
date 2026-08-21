# 采购模块场景梳理与资料缺口

> 依据《采购模块.xlsx》的全部可见 Sheet 解析；无隐藏 Sheet。本文件未出现版本号，当前以更新记录最新条目（2024-06-24）为可见口径基线。

## 当前有效范围

| 场景 | 文档承载 | 已知目标表/来源 |
|---|---|---|
| 采购价格 | 采购订单商品表第 1–7 行 | `srm_billing.purchase_price` → `doris_dim_srm_purchase_price` |
| 采购订单商品 | 采购订单商品表第 9–13 行 | `doris_dwd_srm_purchase_order_combine` → `doris_dws_srm_purchase_order_index` |
| 采购订单 | 采购订单表第 2 行 | `doris_dws_srm_purchase_order_index` |
| 采购发货商品 | 采购订单商品表第 15–24 行 | `doris_dwd_srm_delivery_order_combine` → `doris_dws_srm_delivery_order_index` |
| 采购发货单 | 采购订单表第 6–8 行 | `doris_dws_srm_delivery_order_index` |
| 交货计划商品 | 采购订单商品表第 26–36 行 | `srm_ops.delivery_plan` → `dwd.srm_delivery_plan_combine` |
| 采购退货商品/退单 | 采购订单商品表第 38–41 行、采购订单表第 12 行 | `srm_ops.sub_refund_order` / `srm_ops.refund_order` → `doris_dws_srm_refund_order_index` |

## 已确认规则

### 采购价格

- 不含税、税率、含税、单位运费、不含税含运费、含税含运费单价，分别直取 `no_tax_price`、`tax_rate`、`price`、`unit_freight`、`no_tax_freight_price`、`tax_freight_price`。
- 价格状态：当前日期位于价格开始与结束日期区间内为有效，否则无效。
- 价格时间类型：`time_type = 0` 按采购订单下单时间生效；`time_type = 1` 按采购发货单到货时间生效。
- 状态过滤以业务库为准：`status = 0` 生效、`1` 失效；Excel 修饰词的有效/无效 `1/2` 已判定为历史/错误说明。

### 交货计划（已与库存模块关联）

- 要求、到货、实收、拒收、在途数量分别直取 `demand_num`、`receive_num`、`actual_receive_num`、`reject_num`、`in_transit_num`。
- 未收数量 = `demand_num - actual_receive_num`。
- 交货计划的不含税/含税含运单价与总额直取四个 `delivery_plan_*freight_*` 字段。
- 交收状态修饰词来自采购订单/交货计划链路；`settlement_status = 20` 为发货在途。

### 采购发货与成本

- 发货、到货、实收、拒收数量直取 `delivery_num`、`receive_num`、`actual_receive_num`、`reject_num`。
- 不含税发货收入总额 = `price × actual_receive_num ÷ 1.13`。
- 工厂物料链路：按收货日期与收货仓库关联 `doris_dim_oms_product_produce_factory_warehouse` 取得 `factory_code`；再按收货日期、`factory_code` 及 `goods_code = doris_dim_oms_product_factory_material.sku_code` 取得 `material_code`、`material_name`。工厂名称、所属货主和公司等属性可由 `doris_dim_oms_product_produce_factory` 补充。
- 采购发货不含税出库成本单价：优先按 `delivery_order_id + material_code` 关联产销出库成本；其次按物料、货主、工厂取最新非 0 产销出库成本；仍无则按商品、货主、仓库和收货月份取已关账存货成本的 `delivery_cost_price`；最后为 0。产销出库 `cost_price` 与存货成本 `delivery_cost_price` 均已确认是不含税价，直接写入，不做税额换算。
- 采购发货 DWD 已确认 `no_tax_price` 为不含税含运费单价、`price` 为含税含运费单价，文档字段契约无冲突。

### 采购退货

- `refund_price` 为不含税退货单价，DWS `doris_dws_srm_refund_order_index` 直接透传 DWD `doris_dwd_srm_refund_order_combine.refund_price`；`tax_price` 为含税退货单价。

## 删除线排除

- 采购订单表 A3/C3「采购行单量」及其公式为删除线，不纳入当前有效指标。
- 维度 Sheet A15/B15「业务单元」为删除线，不纳入当前有效维度。

## 版本说明

- 文档更新记录仅有 2022-09-15 初版、2024-06-24 工厂维度补充，未提供版本号、上线状态或当前上线时间。
