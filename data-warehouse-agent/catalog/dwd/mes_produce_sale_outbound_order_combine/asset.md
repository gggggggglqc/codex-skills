---
asset_id: dwd.mes_produce_sale_outbound_order_combine
layer: DWD
table_name: doris_dwd_mes_produce_sale_outbound_order_combine
database: dp_dwd
business_name: 产销出库明细
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 产销出库单子单物料行
primary_key: 待确认（DDL 未声明键模型）
partition: { field: dt, semantic: 主单创建日期, strategy: 待确认 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 MES 五张 Combine DDL, locator: doris_dwd_mes_produce_sale_outbound_order_combine, observed_at: 2026-08-14 }
---

# 产销出库明细

提供工厂销售发货、出库、收货仓、发货子单与物料级要求/实际正残品出库数量及成本。
