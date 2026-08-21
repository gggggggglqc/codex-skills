---
asset_id: dws.inbound_and_outbound_index_mid
layer: DWS
table_name: doris_dws_inbound_and_outbound_index_mid
database: dp_dws
business_name: 库存模块出入库中间表
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近90天, load_strategy: 先删后新增 }
grain: 出入库子单商品行（成本计算前中间粒度）
primary_key: dt + inbound_and_outbound_sub_order_id + goods_code（UNIQUE KEY）
partition: { field: dt, semantic: 创建日期, strategy: RANGE 月分区；动态分区，history_partition_num=17 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记出入库中间表 DDL }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/6c9a0c5b-88ce-46db-81e1-6933a5a1e818/pasted-text.txt, locator: doris_dws_inbound_and_outbound_index_mid, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.inbound_and_outbound_index
      join: 出入库子单商品行补充成本字段后写入 Index
---

# 库存模块出入库中间表

与出入库 Index 同粒度，保留出入库事实、状态、数量、订单和维度字段，不含最终采购/净利/供货成本金额列；是成本计算的中间承载表。

DDL 已确认：按三字段 UNIQUE KEY 去重；`dt` 使用 Asia/Shanghai 时区的月 RANGE 动态分区，保留 17 个历史分区，并建有审核、到货、入库、出库时间 Bitmap 索引。每日删除近 90 天数据后新增重算结果。
