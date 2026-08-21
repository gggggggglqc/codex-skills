---
asset_id: dwd.mes_take_material_stock_order_combine
layer: DWD
table_name: doris_dwd_mes_take_material_stock_order_combine
database: dp_dwd
business_name: 领料出库明细
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 领料出库单子单物料行
primary_key: 待确认（DDL 未声明键模型）
partition: { field: dt, semantic: 主单创建日期, strategy: 待确认 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 MES 五张 Combine DDL, locator: doris_dwd_mes_take_material_stock_order_combine, observed_at: 2026-08-14 }
---

# 领料出库明细

提供领/补料单、生产销售单、工厂/仓库及物料级要求/实际正品出库数量和成本。
