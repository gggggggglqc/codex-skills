---
asset_id: dws.dms_refund_return_index
layer: DWS
table_name: doris_dws_dms_refund_return_index
database: dp_dws
business_name: DMS 分销退单与退货明细指标
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近31天, load_strategy: 覆盖更新 }
grain: 分销退单子单 + 商品编码行
primary_key: dt + sub_refund_id + goods_code
partition: { field: dt, semantic: 分销退单主单创建时间, strategy: DDL 未声明分区策略 }
fields_file: fields.md
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 用户提供 DMS 分销退单与退货 Index DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/166ee304-5cca-43c2-b741-6019f74677a4/pasted-text.txt, locator: CREATE TABLE doris_dws_dms_refund_return_index, observed_at: 2026-08-14 }
  - { type: product_doc, path: /Users/liuqingchen/Downloads/售后模块.xlsx, locator: V6.5.1售后商品（分销退单、分销退货单指标）, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: ods.sms_sub_refund_order
      join: refund_id + sub_refund_id + goods_code；提供申请、发货、确认到货、实收数量与退回单价
    - upstream_asset: ods.sms_sub_refund_stock_order
      join: 经分销退货入库主单取得 refund_id 后，按 refund_id + goods_code 补充入库实收数量
    - upstream_asset: ods.sms_sub_outbound_delivery_order
      join: sub_order_id + goods_code；按需追溯原正向销售出库
---

# DMS 分销退单与退货明细指标

以 `dt + sub_refund_id + goods_code` 唯一标识记录，合并承载分销退单申请、分销退货发货/收货、退款、成本、税额及公共维度。`cost_price` 对应当前有效的“分销退货单商品供货成本（已乘申请退款数量）”。

模型按 `dt + sub_refund_id` Hash 分布，`apply_time` 有 Bitmap 索引。DDL 未声明分区与调度策略。
