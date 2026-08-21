---
asset_id: dws.eb_trade_order_goods_index
layer: DWS
table_name: doris_dws_eb_trade_order_goods_index
database: dp_dws
business_name: 易仓跨境订单商品 Index
status: 部分确认
refresh:
  frequency: 已停止更新
  timezone: Asia/Shanghai
  load_window: 不适用（历史冻结数据）
  load_strategy: 不再调度；仅保留既有历史数据供查询和发货 V1 汇总
grain: 易仓销售订单子单商品行
primary_key: [dt, sub_order_id]
partition:
  field: dt
  semantic: 下单日期
  strategy: RANGE（月）+ 动态分区
  retention: 历史分区创建；动态规则从最早历史至未来 1 个月
distribution: HASH(dt, sub_order_id)，BUCKETS AUTO
version:
  scene: 发货 V1 跨境历史来源
  valid_from: 2026-08-17
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记；2026-08-18 确认已停止更新，定位为历史冻结来源
source_evidence:
  - type: warehouse_ddl
    path: /Users/liuqingchen/.codex/attachments/33c452cb-7048-4a18-ba88-cc9f596319f9/pasted-text.txt
    locator: CREATE TABLE doris_dws_eb_trade_order_goods_index
    observed_at: 2026-08-17
implementation_mapping:
  warehouse_references:
    - upstream_asset: ods.eb_trade_order_tmp
      usage: 跨境差异表（易仓历史订单汇总）的 ODS 输入
    - downstream_table: doris_app_report_delivery_v1
      usage: 跨境历史发货数据；V1 仅从 DWS Index 读取，历史切换日期以应用说明为准
---

# 易仓跨境订单商品 Index

该表是发货 V1 文档中“易仓”历史跨境订单来源的物理表，使用 `dt + sub_order_id` 唯一标识商品行。上游为 `doris_ods_eb_trade_order_tmp`；发货 V1 只读取本 DWS 表，不直接读取 ODS。已提供下单、易仓发货、FBA 发货时间，以及 `goods_qty`、`sku_total_cny`、含税/不含税含运费采购成本总额等字段。已确认该 DWS **停止更新**：只保留既有历史数据，不再设置日常调度、补数或滚动重算。
