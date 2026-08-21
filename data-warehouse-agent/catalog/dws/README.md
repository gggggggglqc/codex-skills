# DWS 资产目录

## 销售模块 V6.5.1

销售模块的商品基础指标由以下三个 DWS Index 表共同承载。Excel 的 `基础指标-商品 1.0` 为历史版本；当前资产以 `基础指标-商品v6.5.1` 为准，不纳入“跨境销售”Sheet。

| 资产 ID | 物理表 | 行粒度 | 承载指标组 |
|---|---|---|---|
| `dws.trade_order_goods_index` | `doris_dws_trade_order_goods_index` | 系统订单子单商品行；原始子单可关联 | 原始订单、系统订单、系统订单组合装 |
| `dws.dms_trade_order_index` | `doris_dws_dms_trade_order_index` | 分销订单子单商品行 | 分销订单 |
| `dws.dms_delivery_index` | `doris_dws_dms_delivery_index` | 分销发货单子订单商品行 | 分销发货、分销退货 |

## 关联边界

- 原始订单与系统订单通过 `source_order_id`、`source_sub_order_id` 和系统订单字段保存关联线索。
- 分销订单和分销发货/退货不关联系统订单子单；它们分别使用分销 `order_id`、`sub_order_id` 与 `delivery_order_id`、`sub_delivery_order_id`。
- 不能跨三表直接按 `sub_order_id` 汇总；必须先按业务类型选择表，并在后续 APP 指标中定义 union/去重规则。

## 刷新规则

三张 Index 表均每日重算最近 60 天：先删除窗口内旧数据，再写入重算结果。该规则意味着业务发生晚到/修订时，只要发生日期处于窗口内即可被纠正；超过 60 天的历史修订需走专项重跑或版本变更。
