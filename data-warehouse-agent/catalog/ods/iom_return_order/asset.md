---
asset_id: ods.iom_return_order
layer: ODS
table_name: return_order
database: erp_iom
business_name: 退货应收入库单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 退货应收入库主单行
primary_key: return_order_id
partition: { field: 无, semantic: 源表未声明分区, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记退货应收入库主单 DDL }
source_evidence:
  - { type: source_ddl, path: 用户于会话中提供的 erp_iom.return_order DDL, locator: erp_iom.return_order, observed_at: 2026-08-14 }
---

# 退货应收入库单

以 `return_order_id` 唯一标识应收入库单。通过 `refund_order_id` 关联 OMS 系统退单主单 `oms_ops.refund_order.refund_id`；同时保留 `source_refund_id`、`source_order_id`、`order_id` 以支持原始/系统订单追溯。

可用于售后商家收货相关状态：`order_status` 含待入库、待推送、已推送、已到货、已完成、部分完成、完成异常、撤销等状态；`arrive_time` 和 `finish_time` 分别记录到货与完成时间。
