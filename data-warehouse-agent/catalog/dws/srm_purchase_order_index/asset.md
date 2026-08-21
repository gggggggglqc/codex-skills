---
asset_id: dws.srm_purchase_order_index
layer: DWS
table_name: doris_dws_srm_purchase_order_index
database: dp_dws
business_name: 采购订单商品指标
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近365天, load_strategy: 覆盖更新 }
grain: 采购订单商品行（purchase_line_id）
primary_key: dt + purchase_line_id（UNIQUE KEY）
partition: { field: dt, semantic: 创建时间业务分区字段, strategy: DDL 未声明 PARTITION BY }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购订单商品 Index DDL，并确认交收状态枚举 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_dws_srm_purchase_order_index DDL, locator: doris_dws_srm_purchase_order_index, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: dwd.srm_purchase_order_combine
      join: purchase_line_id；补充商品、组织、人员和商品维度
---

# 采购订单商品指标

采购订单商品层 Index。按 `dt + purchase_line_id` UNIQUE KEY 去重；DDL 未声明 `PARTITION BY`。`settlement_status` 枚举已确认：10 未交收、20 发货在途、30 部分交收、40 全部交收、50 超量交收。采购订单量按 `purchase_order_id` 去重，且限制 `demand_num <> 0`。
