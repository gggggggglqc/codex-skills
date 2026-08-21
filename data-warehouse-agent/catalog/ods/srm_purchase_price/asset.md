---
asset_id: ods.srm_purchase_price
layer: ODS
table_name: purchase_price
database: srm_billing
business_name: 采购价格业务表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 采购价格条目（purchase_price_id）
primary_key: purchase_price_id
partition: { field: 无, semantic: 业务库当前表, strategy: 无 }
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购价格业务源表并确认状态枚举 }
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 srm_billing.purchase_price DDL, locator: purchase_price, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dim.srm_purchase_price
      join: purchase_price_id；按 dt 形成每日全量快照
---

# 采购价格业务表

业务库状态枚举为唯一权威：`status = 0` 生效，`status = 1` 失效。价格生效时间类型：`time_type = 0` 下单时间，`1` 到货时间。
