---
asset_id: ods.sub_trade_order
layer: ODS
table_name: doris_ods_sub_trade_order
database: dp_ods
business_name: OMS 系统订单子单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 系统订单子单商品行
primary_key: sub_order_id（OMS 源表主键；Doris 抽取表键模型待确认）
partition: { field: dt, semantic: 日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: V6.5.1, valid_from: 2026-08-13, valid_to: null, change_summary: 用户提供 DDL 后首次登记 }
source_evidence:
  - { type: warehouse_ddl, path: "用户于会话中提供的 doris_ods_sub_trade_order DDL", locator: doris_ods_sub_trade_order, observed_at: 2026-08-13 }
  - { type: source_ddl, path: /Users/liuqingchen/.codex/attachments/2ea90c89-8b54-472a-b22a-a30af37d4a72/pasted-text.txt, locator: oms_ops.sub_trade_order, observed_at: 2026-08-14 }
implementation_mapping:
  das_references: []
  warehouse_references:
    - downstream_asset: dws.trade_order_goods_index
      join: sub_trade_order.sub_order_id = trade_order_goods_index.sub_order_id
    - upstream_asset: ods.oms_order
      join: sub_trade_order.source_sub_order_id = oms_order.source_sub_order_id
open_questions:
  - 该 DDL 末尾注释写为“系统订单主单”，但字段和粒度均是子单；资产按子单登记，请确认是否为 DDL 注释笔误。
  - 请确认系统订单商品采购、净利、供货、物流和包材成本的其他上游表及 ETL 规则。
---

# OMS 系统订单子单

OMS 源表 `oms_ops.sub_trade_order` 以 `sub_order_id` 为主键。系统订单商品的直接 ODS 来源；通过 `order_id` 关联系统订单主单，通过 `source_order_id`、`source_sub_order_id` 关联原始订单，其中原始子单关联键为 `source_sub_order_id`。

`bn_replacement_order_id` 是班牛补发单 ID。当前售后模块不要求补发单据溯源，故不作为本期必需关联字段；补发识别以系统订单 `order_category` 为准。
