---
asset_id: dws.cbs_refund_order_index
layer: DWS
table_name: doris_dws_cbs_refund_order_index
database: dp_dws
business_name: 跨境系统退款 Index
status: 已确认
refresh:
  frequency: 每日
  timezone: Asia/Shanghai
  load_window: 最近 90 天
  load_strategy: 覆盖更新最近 90 天数据
grain: 跨境系统退款子单商品行
primary_key: [dt, sub_refund_id]
partition:
  field: dt
  semantic: 主单创建时间
  strategy: RANGE（月）+ 动态分区
  retention: 历史分区创建；动态规则从最早历史至未来 1 个月
distribution: HASH(sub_refund_id)，BUCKETS 3
version:
  scene: 跨境系统表建设
  valid_from: 2026-08-17
  valid_to:
  change_summary: 依据跨境系统表建设文档和完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: /Users/liuqingchen/.codex/attachments/3a0c3a90-1180-4d19-895c-75f6f6e51220/pasted-text.txt
    locator: CREATE TABLE doris_dws_cbs_refund_order_index
    observed_at: 2026-08-17
  - type: product_doc
    path: /Users/liuqingchen/Downloads/跨境系统表建设-文秋红.xlsx
    locator: 可见 Sheet「跨境系统退单index」
    observed_at: 2026-08-17
implementation_mapping:
  warehouse_references:
    - upstream_table: doris_dwd_cbs_sysrefund_combine
      usage: 跨境系统退款主子单商品事实
    - downstream_table: doris_app_report_delivery_v1
      usage: 跨境退款、退货数量及相关成本汇总
---

# 跨境系统退款 Index

以跨境系统退款子单为商品粒度。发货 V1 使用已发货且退款成功的记录，按申请/完成时间汇总退款、退货数量、人民币退款支出和成本抵减。
