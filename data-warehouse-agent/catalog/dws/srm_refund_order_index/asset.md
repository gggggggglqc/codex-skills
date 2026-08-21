---
asset_id: dws.srm_refund_order_index
layer: DWS
table_name: doris_dws_srm_refund_order_index
database: dp_dws
business_name: 采购退单商品指标
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近120天, load_strategy: 覆盖更新 }
grain: 采购退货子单商品行（sub_refund_id）
primary_key: dt + sub_refund_id（UNIQUE KEY）
partition: { field: dt, semantic: 创建时间业务分区字段, strategy: DDL 未声明 PARTITION BY }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购退单 Index DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_dws_srm_refund_order_index DDL, locator: doris_dws_srm_refund_order_index, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: dwd.srm_refund_order_combine
      join: dt + sub_refund_id；补充维度、人员名称和单位名称
---

# 采购退单商品指标

采购退货商品层 Index，包含退货数量、实收数量、不含税/含税退货单价、退单状态、来源、物流及商品、仓库、货主、供应商维度。`refund_price` 为不含税退货单价，直接透传 `dwd.srm_refund_order_combine.refund_price`；`tax_price` 为含税退货单价。按 `dt + sub_refund_id` UNIQUE KEY 去重；DDL 未声明 `PARTITION BY` 与调度策略。
