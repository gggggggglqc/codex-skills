---
asset_id: dws.refund_order_index
layer: DWS
table_name: doris_dws_refund_order_index
database: dp_dws
business_name: 系统退单指标
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 滚动近 31 天, load_strategy: 覆盖更新滚动近 31 天数据 }
grain: 系统退单子单商品行
primary_key: dt + sub_refund_id
partition: { field: dt, semantic: 系统退单主单创建时间, strategy: 按月 RANGE 分区；动态分区保留历史并预建至下月 }
fields_file: fields.md
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 用户提供系统退单 Index DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/9dd62cc2-447e-4a46-8cd9-776f64c96d52/pasted-text.txt, locator: CREATE TABLE doris_dws_refund_order_index, observed_at: 2026-08-14 }
  - { type: product_doc, path: /Users/liuqingchen/Downloads/售后模块.xlsx, locator: V6.5.1售后商品（系统退单商品指标）, observed_at: 2026-08-14 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - upstream_asset: ods.oms_ops_refund_order
      join: refund_order.refund_id = refund_order_index.refund_id
    - upstream_asset: ods.oms_ops_sub_refund_order
      join: sub_refund_order.sub_refund_id = refund_order_index.sub_refund_id
    - upstream_asset: ods.iom_return_order
      join: return_order.refund_order_id = refund_order_index.refund_id
---

# 系统退单指标

售后系统退单的商品宽表，以 `dt + sub_refund_id` 唯一标识系统退单子单。承载原始/系统订单关联、退款、成本、税额、返利、收货状态、售后动作时间、商品与组织维度。

`estimate_brand_quotation` 在 DDL 中已标注为废弃字段，当前指标应使用 `brand_quotation`（供货总成本，已乘退款数量）。

物理模型为 `UNIQUE KEY(dt, sub_refund_id)`，按 `dt` 月度 RANGE 动态分区；`apply_time`、`good_return_time`、`return_time`、`pay_time` 配有 Bitmap 索引。每日覆盖更新滚动近 31 天数据。
