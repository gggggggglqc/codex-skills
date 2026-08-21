---
asset_id: dws.cbs_trade_order_index
layer: DWS
table_name: doris_dws_cbs_trade_order_index
database: dp_dws
business_name: 跨境系统订单 Index
status: 已确认
refresh:
  frequency: 每日
  timezone: Asia/Shanghai
  load_window: 最近 90 天
  load_strategy: 覆盖更新最近 90 天数据
grain: 跨境系统订单子单商品行
primary_key: [dt, sub_order_id]
partition:
  field: dt
  semantic: 下单时间
  strategy: RANGE（月）+ 动态分区
  retention: 历史分区创建；动态规则从最早历史至未来 1 个月
distribution: HASH(dt, sub_order_id)，BUCKETS AUTO
version:
  scene: 跨境系统表建设
  valid_from: 2026-08-17
  valid_to:
  change_summary: 依据跨境系统表建设文档和完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: /Users/liuqingchen/.codex/attachments/65caa639-638b-4ba8-bb24-75b445b50071/pasted-text.txt
    locator: CREATE TABLE doris_dws_cbs_trade_order_index
    observed_at: 2026-08-17
  - type: product_doc
    path: /Users/liuqingchen/Downloads/跨境系统表建设-文秋红.xlsx
    locator: 可见 Sheet「V6.5.1跨境系统订单」
    observed_at: 2026-08-17
implementation_mapping:
  warehouse_references:
    - upstream_table: doris_dwd_cbs_systrade_order_combine
      usage: 跨境系统订单主子单商品事实
    - downstream_table: doris_app_report_delivery_v1
      usage: 跨境发货数量、收入和成本汇总
---

# 跨境系统订单 Index

以跨境系统订单子单为商品粒度。发货 V1 使用其中已发货订单的数量、人民币发货收入、供货成本、采购成本及净利成本，并按订单功能、销售模式等条件筛选。跨境订单与退款链路不可替代国内系统订单 Index。
