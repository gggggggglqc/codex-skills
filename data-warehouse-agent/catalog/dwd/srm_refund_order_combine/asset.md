---
asset_id: dwd.srm_refund_order_combine
layer: DWD
table_name: doris_dwd_srm_refund_order_combine
database: dp_dwd
business_name: 采购退单主子单宽表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 采购退货子单商品行（sub_refund_id）
primary_key: dt + sub_refund_id（UNIQUE KEY）
partition: { field: dt, semantic: 创建时间业务分区字段, strategy: DDL 未声明 PARTITION BY }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购退单主子单事实 DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_dwd_srm_refund_order_combine DDL, locator: doris_dwd_srm_refund_order_combine, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.srm_refund_order_index
      join: dt + sub_refund_id；补充商品、供应商、人员及维度信息
---

# 采购退单主子单宽表

采购退货商品事实表。按 `dt + sub_refund_id` UNIQUE KEY 去重；包含退货、实收数量，退单/来源/物流状态和退货价格。DDL 未声明物理分区及调度策略。
