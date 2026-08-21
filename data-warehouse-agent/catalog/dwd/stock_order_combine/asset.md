---
asset_id: dwd.stock_order_combine
layer: DWD
table_name: doris_dwd_stock_order_combine
database: dp_dwd
business_name: 出入库开单明细
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 出入库主单子单商品行
primary_key: 待确认（DDL 未声明键模型）
partition: { field: dt, semantic: 主单创建时间, strategy: 待确认 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记库存出入库核心 Combine DDL }
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 doris_dwd_stock_order_combine DDL, locator: doris_dwd_stock_order_combine, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: ods.iom_stock_order
      join: stock_order_code；补充通用出入库主单字段
    - downstream_asset: dws.inbound_and_outbound_index
      join: stock_order_combine 的出入库主子单和商品明细转换为 Index
---

# 出入库开单明细

库存模块核心通用事实表。按主单、子单与商品粒度保存出入库方向、类型、状态、正/残品数量、实际/收货数量、成本价、货主、仓库、供应商、物流及单据时间。
