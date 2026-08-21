# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 分区日期 / 退款单 | `dt` / `refund_id` | date / varchar |
| 原始订单 | `source_order_id` | varchar |
| 退款申请/实际退款/其他退款 | `refund_amount` / `actual_refund_amount` / `actual_other_refund_amount` | varchar / decimal |
| 退款类型/状态/阶段 | `type` / `status` / `refund_phase` | varchar |
| 退款创建/成功/退货时间 | `refund_time` / `refund_success_time` / `good_return_time` | datetime |
| 是否有货物退还 | `has_good_return` | int |
