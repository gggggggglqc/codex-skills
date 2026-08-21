---
asset_id: dwd.srm_delivery_order_combine
layer: DWD
table_name: doris_dwd_srm_delivery_order_combine
database: dp_dwd
business_name: 采购发货单主子单宽表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 采购发货子单商品行（sub_delivery_order_id）
primary_key: 待确认（DDL 未声明 Doris 键模型）
partition: { field: dt, semantic: 创建时间分区, strategy: 待确认 }
fields_file: fields.md
version: { scene: 采购模块, valid_from: 2026-08-14, valid_to: null, change_summary: 登记采购发货主子单事实 DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 dp_dwd.doris_dwd_srm_delivery_order_combine DDL, locator: dp_dwd.doris_dwd_srm_delivery_order_combine, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.srm_delivery_order_index
      join: sub_delivery_order_id；输出采购发货商品指标
---

# 采购发货单主子单宽表

采购发货商品事实表。价格字段契约已确认：`no_tax_price` 是不含税含运费单价，`price` 是含税含运费单价；数量字段为发货、到货、实收、拒收数量。
