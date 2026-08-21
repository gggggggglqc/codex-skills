---
asset_id: app.finance_profit_business
layer: APP
table_name: doris_app_finance_profit_business
database: dp_dws
business_name: 净利指标中间表
status: 待数仓确认
release_status: 未上线（计划月底）
refresh:
  frequency: 每日（月底正式上线后）
  load_window: 昨日
  load_strategy: 覆盖更新
  timezone: Asia/Shanghai
  aligned_with: doris_app_net_profit_check_report_v2
  scheduled_backfills:
    - { day_of_month: 31, fallback: 当月最后一天, load_window: 上月, load_strategy: 覆盖更新 }
    - { day_of_month: 3, load_window: 上月, load_strategy: 覆盖更新 }
    - { day_of_month: 8, load_window: 上月, load_strategy: 覆盖更新 }
    - { day_of_month: 10, load_window: 本月, load_strategy: 覆盖更新 }
grain: 日期 + 经营/商品/科目/国别等净利汇总维度
primary_key: [dt, owner_code, shop_code, shop_plat_code, business_group, sales_model, subject_code, cost_belong, sku_code, spu_code, category_level1, category_level2, category_level3, category_level4, supplier_code, author_id, is_self_live_stream, plat_spu_id, country_type]
partition: { field: dt, semantic: 业务发生日期, strategy: DDL 未声明 PARTITION BY }
distribution: HASH(dt)，BUCKETS 2
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE doris_app_finance_profit_business DDL, locator: dp_dws.doris_app_finance_profit_business, observed_at: 2026-08-18 }
---

# 净利指标中间表

本表承接净利 V2、科目费用分摊成功/失败事实以及系统计算的税金指标，供老板报表 v5.8.6 按收入、成本、费用、税金及附加、营业外收支、所得税等净利维度汇总。该表计划于月底正式上线；上线后刷新节奏与净利 V2 一致：每日覆盖更新昨日；每月 31 日（没有 31 日则当月最后一天）、3 日、8 日覆盖上月，10 日覆盖本月。

金额字段：`no_tax_amount`（不含税金额）、`tax_amount`（税额）。`cost_belong` 虽为 `varchar(1500)`，实际保存费用归属枚举数字（整数文本），与费用采集策略枚举对应。
