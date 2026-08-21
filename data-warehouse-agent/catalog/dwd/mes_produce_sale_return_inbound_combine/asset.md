---
asset_id: dwd.mes_produce_sale_return_inbound_combine
layer: DWD
table_name: doris_dwd_mes_produce_sale_return_inbound_combine
database: dp_dwd
business_name: 生产销退入库明细
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 生产销退入库单子单物料行
primary_key: 待确认（DDL 未声明键模型）
partition: { field: dt, semantic: 主单创建日期, strategy: 待确认 }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 MES 五张 Combine DDL, locator: doris_dwd_mes_produce_sale_return_inbound_combine, observed_at: 2026-08-14 }
---

# 生产销退入库明细

提供退货单、入库单、工厂、仓库及物料级要求/到货/实际入库正残品数量与成本。
