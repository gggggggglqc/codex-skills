---
asset_id: ods.iom_sub_refund_stock_order
layer: ODS
table_name: sub_refund_stock_order
database: erp_iom
business_name: 退货应收入库明细单
status: 已确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 退货应收入库商品行
primary_key: sub_stock_order_id
partition: { field: 无, semantic: 源表未声明分区, strategy: 待确认 }
version: { scene: 售后模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记退货应收入库子单 DDL }
source_evidence:
  - { type: source_ddl, path: 用户于会话中提供的 erp_iom.sub_refund_stock_order DDL, locator: erp_iom.sub_refund_stock_order, observed_at: 2026-08-14 }
---

# 退货应收入库明细单

以 `sub_stock_order_id` 为主键，商品粒度记录申请入库数量 `apply_num`、实收入库数量 `actual_num`、收货数量 `arrive_num`、残品数量及入库成本。

`stock_order_id` 为入库单号，业务上关联退货应收入库主单 `return_order.return_order_id`；该关系未在源库以外键声明，但字段语义与售后文档一致。
