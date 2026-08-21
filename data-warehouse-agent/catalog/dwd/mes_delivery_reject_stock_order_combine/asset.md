---
asset_id: dwd.mes_delivery_reject_stock_order_combine
layer: DWD
table_name: doris_dwd_mes_delivery_reject_stock_order_combine
database: dp_dwd
business_name: 发货拒收入库明细
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 发货拒收入库单子单物料行
primary_key: 待确认（DDL 未声明键模型）
partition: { field: dt, semantic: 主单创建日期, strategy: 待确认 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 MES 五张 Combine DDL, locator: doris_dwd_mes_delivery_reject_stock_order_combine, observed_at: 2026-08-14 }
---

# 发货拒收入库明细

提供销售发货拒收后的入库单、工厂/仓库、物料级要求/到货/实际正残品入库数量及成本。
