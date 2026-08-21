---
asset_id: dws.inbound_and_outbound_index
layer: DWS
table_name: doris_dws_inbound_and_outbound_index
database: dp_dws
business_name: 库存模块出入库商品指标
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近90天, load_strategy: 先删后新增 }
grain: 出入库子单商品行
primary_key: dt + inbound_and_outbound_sub_order_id + goods_code（UNIQUE KEY）
partition: { field: dt, semantic: 创建日期, strategy: RANGE 月分区；动态分区，history_partition_num=0 }
fields_file: fields.md
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 首次登记出入库 Index DDL }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/ac86ef59-d499-4e90-b45f-dba682553911/pasted-text.txt, locator: doris_dws_inbound_and_outbound_index, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: dwd.stock_order_combine
      join: 出入库主子单、商品、仓库、货主和单据时间转换
---

# 库存模块出入库商品指标

库存模块入库、出库的商品宽表。承载全部出入库类型、状态、数量/货值、采购/净利/供货成本、订单关联及商品、组织、工厂维度。

DDL 已确认：按三字段 UNIQUE KEY 去重；`dt` 使用 Asia/Shanghai 时区的月 RANGE 动态分区，并建有审核、到货、入库、出库时间 Bitmap 索引。每日删除近 90 天数据后新增重算结果。
