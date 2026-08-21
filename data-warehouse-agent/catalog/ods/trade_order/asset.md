---
asset_id: ods.trade_order
layer: ODS
table_name: doris_ods_trade_order
database: dp_ods
business_name: OMS 系统订单主单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 系统订单主单行
primary_key: order_id（OMS 源表主键；Doris 抽取表键模型待确认）
partition: { field: dt, semantic: 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "/Users/liuqingchen/.codex/attachments/99ecd728-a7fd-45c6-b65c-8a4d5e3393e4/pasted-text.txt", locator: doris_ods_trade_order, observed_at: 2026-08-13 }
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/2ea90c89-8b54-472a-b22a-a30af37d4a72/pasted-text.txt, locator: oms_ops.trade_order, observed_at: 2026-08-14 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: dws.trade_order_goods_index
      join: trade_order.order_id = sub_trade_order.order_id
open_questions:
  - 请确认 dt 的业务日期定义与 create_time、trade_time 的关系。
---

# OMS 系统订单主单

OMS 源表 `oms_ops.trade_order` 以 `order_id` 为主键。系统订单主单按 `order_id` 与系统订单子单关联，提供店铺、货主、仓库、物流、订单状态、交易/支付/审核/发货时间和主单金额属性。

`order_category` 已定义售后换货（3）、订单补发（4）、配件补发（5）、售后补发（9、10）等系统订单场景。当前售后模块直接以该订单标记识别补发订单，不要求回溯班牛补发单或补发出库单。
