---
asset_id: dim.cost_gather_strategy
layer: DIM
table_name: doris_dim_fms_support_cost_gather_strategy
database: dp_dim
business_name: 费用采集策略维表
status: 部分确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 按 dt 日切片
  load_strategy: 待确认
grain: 日期 + 策略 + 科目 + 费用项目
primary_key: [dt, id, subject_code, cost_code]
partition:
  field: dt
  semantic: 自然日
  strategy: DDL 未声明 PARTITION BY
distribution: HASH(subject_code, cost_code)，BUCKETS 3
version:
  scene: 发货 V1 产销费用采集和分摊规则
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: 用户于会话中提供的 CREATE TABLE doris_dim_fms_support_cost_gather_strategy DDL
    locator: dp_dim.doris_dim_fms_support_cost_gather_strategy
    observed_at: 2026-08-18
open_questions:
  - 刷新频率和装载策略待确认；不影响当前发货 V1 的销售模块直接字段。
---

# 费用采集策略维表

按 `dt + subject_code + cost_code` 关联财务科目费用分摊事实 `doris_dws_finance_cost_sbjct`。`is_gather`、`is_accrual_subject`：`1` 是、`2` 否；`cost_share_method`：`0` 销售收入、`1` 销售成本、`2` 发货方量。

`cost_belong` 及损益方向：`1` 收入（加）、`2` 成本（减）、`3` 费用（减）、`4` 专项支出（不计算）、`5` 无票费用（减）、`6` 所得税（减）、`7` 税金及附加（减）、`8` 营业外收入（加）、`9` 营业外支出（减）、`10` 应交税费（不计算）。本表用于财务费用治理；发货 V1 的销售模块直接字段不依赖其策略行。
