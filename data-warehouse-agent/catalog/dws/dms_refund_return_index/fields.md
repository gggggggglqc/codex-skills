# 字段与指标映射（售后模块 V6.5.1）

> 以 DDL 物理字段和售后 Excel 当前有效指标为准。Excel 第 49 行“已乘实收数量”供货成本与第 52 行不含税采购成本均为删除线历史口径，不作为当前有效指标。

## 主键、关联与业务时间

| 逻辑字段 | 物理字段 | 说明 |
|---|---|---|
| 物理唯一键 | `dt + sub_refund_id + goods_code` | 分销退单子单与商品粒度 |
| 分区日期 | `dt` | 分销退单主单创建时间日期 |
| 分销退单子单/主单/原订单 | `sub_refund_id` / `refund_id` / `order_id` | 分销退单关联标识 |
| 分销退货发货主/子单 | `refund_delivery_id` / `sub_refund_delivery_id` | 分销退货履约关联标识 |
| 申请 / 客户退货 / 商家收货时间 | `apply_time` / `good_return_time` / `receive_time` | 三个售后业务动作时间 |
| 主单 / 子单收货状态 | `receipt_status` / `detail_receipt_status` | 1 已收货；2 部分收货；3 未收货 |

## 分销退单与退货数量金额

| 当前逻辑指标 | 物理字段 | 核对结论 |
|---|---|---|
| 分销退单商品申请退款数量 / 金额 | `apply_refund_num` / `apply_refund_amount` | 已落字段 |
| 分销退货单申请退款商品数量 / 金额 | `apply_return_num` / `apply_return_amount` | 已落字段；影刀替代逻辑直接使用 Index 既有结果 |
| 分销退货单实际退货商品金额 | `actual_return_amount` | 已落字段 |
| 分销退单发货数量 | `delivery_num` | 已落字段；影刀状态为已收货且数量为空时取申请数的规则直接使用 Index 既有结果 |
| 分销退货数量 / 退款金额 | `actual_refund_num` / `refund_amount` | `actual_refund_num` 的 DDL 注释为实收数量；`refund_amount` 为退货数量 × 退回单价 |

ODS 重建来源已确认：`sms_ops.sub_refund_order.apply_num`、`deliver_num`、`confirm_arrival_num`、`actual_num`、`refund_price` 提供商品级退单事实；`sms_ops.sub_refund_stock_order.actual_num` 通过退货入库主单补充分商品入库实收事实。已确认同一 `refund_id + goods_code` 只对应一个 `sub_refund_id`，可直接关联。

## 成本与税额

| 逻辑指标 | 物理字段 | 核对结论 |
|---|---|---|
| 分销退货商品供货成本（已乘申请退款数量） | `cost_price` | 对应 Excel 第 50 行；与 DDL“已乘申请数量”注释一致 |
| 分销退货商品供货成本（已乘实收数量） | 已删除 | Excel 第 49 行已划线，不纳入当前口径或字段映射 |
| 采购成本（含税，已乘申请退款数量） | `purchase_price_total` | 已落字段 |
| 采购成本（不含税） | `no_tax_purchase_price_total` | DDL 有字段；Excel 对应第 52 行是删除线历史口径，当前业务用途待确认 |
| 净利成本（含税/不含税） | `product_cost` / `no_tax_product_cost` | 已落字段；不含税为含税净利成本减进项税额（成本） |
| 税率、不含税退款收入、销项/进项税额 | `tax_rate` / `no_tax_payment` / `output_tax_amount` / `input_tax_amount` | 已落字段 |
| 返利比率、返利不含税采购价、返利成本、返利进项税额 | `rebate_rate` / `no_tax_price` / `rebate_cost_amount` / `input_tax_amount_rebate` | DDL 已落字段；当前售后 Excel 未给出对应有效公式，不能直接复用正向分销规则 |

## 影刀分支

售后 Excel 要求自 4 月 1 日起，常规分销退货剔除创建人为影刀账号 `1810592227250778112` 的数据；影刀数据改取分销退单，且限定 `refund_status = 60`（已收货）。本期直接使用该 Index 既有结果，不重建或核查该分支，故不要求提供 `doris_dwd_dms_refund_order_combine` 或相关 ODS DDL。

已补充的 ODS 分销退单主单和退货入库主单均不具备商品级实收成本明细：入库主单 `cost_price` 为主单字段，`goods_codes` 为聚合字符串。当前有效指标直接使用 Index 的 `cost_price` 作为申请退款数量供货成本，不从 ODS 重算或核查。
