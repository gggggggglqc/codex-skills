---
asset_id: dwd.srm_purchase_order_combine
layer: DWD
table_name: doris_dwd_srm_purchase_order_combine
database: dp_dwd
business_name: 采购订单主子单宽表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 采购订单商品行（purchase_line_id）
primary_key: 待确认（DDL 未声明 Doris 键模型）
partition: { field: dt, semantic: 创建时间分区, strategy: 待确认 }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购订单主子单事实 DDL }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/329fcca9-44f7-4c3e-99aa-bf672369f8dc/pasted-text.txt, locator: doris_dwd_srm_purchase_order_combine, observed_at: 2026-08-14 }
---

# 采购订单主子单宽表

按采购行承载采购订单状态、审核状态、交收状态以及原始/当前数量、要求/发货/到货/实收/在途数量和含税/不含税含运金额。`settlement_status` 已存在，但 DDL 未给出具体枚举。
