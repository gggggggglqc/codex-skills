---
asset_id: dim.exchange_rate_system
layer: DIM
table_name: exchange_rate_system
database: fms_support
business_name: 汇率体系表
status: 已确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 生效区间
  load_strategy: 按生效/失效日期匹配
grain: 汇率编码
primary_key: [exchange_rate_code]
effective_time:
  start_field: effective_date
  end_field: expiring_date
version:
  scene: 跨境订单与退款人民币折算
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据业务库完整 DDL 首次登记
source_evidence:
  - type: business_ddl
    path: 用户于会话中提供的 CREATE TABLE fms_support.exchange_rate_system DDL
    locator: fms_support.exchange_rate_system
    observed_at: 2026-08-18
---

# 汇率体系表

按 `source_currency_code`、`target_currency_code` 与业务时间落在 `effective_date`、`expiring_date` 的生效区间匹配汇率。跨境系统建设文档明确使用直接汇率 `direct_exchange_rate` 兑换人民币：币种为 CNY 时汇率固定为 1；业务时间没有生效汇率时取最新日期的汇率。订单按字段规定的支付、发货或完成时间取值，退款按申请或完成时间取值。
