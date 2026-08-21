---
asset_id: ods.srm_delivery_plan
layer: ODS
table_name: delivery_plan
database: srm_ops
business_name: 采购交货计划业务表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 交货计划行（delivery_plan_id）
primary_key: delivery_plan_id
partition: { field: 无, semantic: 业务库当前表, strategy: 无 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 登记交货计划业务源表并对照 DWD Combine }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 srm_ops.delivery_plan DDL, locator: srm_ops.delivery_plan, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dwd.srm_delivery_plan_combine
      join: delivery_plan_id；提供交货计划、商品、仓库、货主、数量及在途数量基础字段
---

# 采购交货计划业务表

主键为 `delivery_plan_id`。提供 `demand_num`、`actual_receive_num`、`in_transit_num`、`is_delete` 等基础字段；不包含采购订单状态或 `settlement_status`（交收状态）。后两项由 DWD Combine 的采购订单关联补充，但当前 DDL 未提供“发货在途”的交收状态枚举。
