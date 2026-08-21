---
asset_id: dws.mes_delivery_order_index
layer: DWS
table_name: doris_dws_mes_delivery_order_index
database: dp_dws
business_name: 工厂生产发货单指标
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近90天, load_strategy: 先删后新增 }
grain: 工厂生产发货子单商品/物料行
primary_key: dt + detail_id（UNIQUE KEY）
partition: { field: dt, semantic: 主单创建日期, strategy: RANGE 月分区；动态分区，history_partition_num=2 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记 MES 发货单 Index DDL }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/c59831f1-1a68-4783-9e46-f0ae5e1eb616/pasted-text.txt, locator: doris_dws_mes_delivery_order_index, observed_at: 2026-08-14 }
---

# 工厂生产发货单指标

按工厂发货子单承载发/收货仓、商品/物料、发货/拒收数量及含税/不含税含运采购成本，用于库存模块工厂发货场景。

DDL 已确认：按 `dt + detail_id` UNIQUE KEY 去重；`dt` 使用 Asia/Shanghai 时区的月 RANGE 动态分区，保留 2 个历史分区。每日删除近 90 天数据后新增重算结果。
