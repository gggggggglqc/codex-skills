---
asset_id: app.net_profit_check_report_v2
layer: APP
table_name: doris_app_net_profit_check_report_v2
database: dp_dws
business_name: 净利核算表 V2
status: 部分确认
refresh:
  frequency: 每日
  timezone: Asia/Shanghai
  load_window: 昨日
  load_strategy: 覆盖更新
  scheduled_backfills:
    - { day_of_month: 31, fallback: 当月最后一天, load_window: 上月, load_strategy: 覆盖更新 }
    - { day_of_month: 3, load_window: 上月, load_strategy: 覆盖更新 }
    - { day_of_month: 8, load_window: 上月, load_strategy: 覆盖更新 }
    - { day_of_month: 10, load_window: 本月, load_strategy: 覆盖更新 }
grain: 日期 + 商品 + 店铺/货主/供应商 + 费用编码 + 业务属性
primary_key: 待确认（DDL 未声明 KEY）
partition:
  field: dt
  semantic: 发货日期
  strategy: DDL 未声明 PARTITION BY
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE dp_dws.doris_app_net_profit_check_report_v2 DDL, locator: dp_dws.doris_app_net_profit_check_report_v2, observed_at: 2026-08-18 }
  - { type: product_doc, path: /Users/liuqingchen/Downloads/T+1净利核算表.xlsx, locator: 可见 Sheet「收入成本V6.4.9.3」, observed_at: 2026-08-18 }
---

# 净利核算表 V2

按 `dt`、商品、店铺/货主、供应商、平台商品、销售模式及 `expense_code` 保存收入、成本、费用和税额事实，金额字段为 `expense_amount`。基础任务每日覆盖更新昨日；月度额外补刷为 31 日（没有 31 日则当月最后一天）、3 日、8 日覆盖上月，10 日覆盖本月。`flag`：`1` 发货 V1、`2` 科目分摊成功、`3` 科目分摊失败、`4` 财务上传费用、`5` 系统单非业务协作费、`6` 系统单业务协作费、`-1` 为 2025-07-13 前历史数据。

`country_type`：`1` 国内、`2` 跨境。V6.4.9.3 定义了 `EP039`~`EP043` 等新增编码；物理字段为通用 `expense_code`，DDL 注释只列至 `EP038`，应以费用科目关系表的有效映射作为编码字典。
