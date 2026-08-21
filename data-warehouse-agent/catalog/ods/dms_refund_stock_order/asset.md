---
asset_id: ods.dms_refund_stock_order
layer: ODS
table_name: doris_ods_dms_refund_stock_order
database: dp_ods
business_name: DMS 分销退货入库主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 分销退货入库主单行
primary_key: 待确认（候选为 stock_order_id；DDL 未声明键模型）
partition: { field: dt, semantic: confirm_time 日期, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 DMS 分销退货入库主单 DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 doris_ods_dms_refund_stock_order DDL, locator: doris_ods_dms_refund_stock_order, observed_at: 2026-08-14 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - upstream_asset: ods.dms_refund_order
      join: dms_refund_stock_order.refund_id = dms_refund_order.refund_id
    - downstream_asset: dws.dms_refund_return_index
      join: dms_refund_stock_order.refund_id = dms_refund_return_index.refund_id
---

# DMS 分销退货入库主单

通过 `refund_id` 关联分销退单主单，通过 `refund_delivery_id` 关联分销退货发货主单。提供入库状态、到货/确认入库时间、仓库、物流和主单入库成本 `cost_price`。

本表是主单粒度且无商品子单；`goods_codes` 为聚合字段。因此不能独立产生“分销退货商品供货成本（已乘实收数量）”，该缺口仍需商品级字段或派生规则解决。
