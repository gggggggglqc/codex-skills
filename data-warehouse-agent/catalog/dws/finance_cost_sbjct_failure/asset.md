---
asset_id: dws.finance_cost_sbjct_failure
layer: DWS
table_name: doris_dws_finance_cost_sbjct_failure
database: dp_dws
business_name: 财务科目费用分摊失败事实表
status: 已确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 待确认
  load_strategy: 待确认
grain: 业务发生日期 + 未分摊科目/费用项目 + 归属维度的异常事实行
primary_key: DDL 未声明物理唯一键
partition:
  field: dt
  semantic: 创建时间分区（业务发生日期）
  strategy: DDL 未声明 PARTITION BY
version:
  scene: 费用分摊数据质量核查
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: 用户于会话中提供的 CREATE TABLE dp_dws.doris_dws_finance_cost_sbjct_failure DDL
    locator: dp_dws.doris_dws_finance_cost_sbjct_failure
    observed_at: 2026-08-18
---

# 财务科目费用分摊失败事实表

记录未成功分摊的费用/科目事实，包括 `associated_data_code`、`is_share_cost`、`result_amount`、不含税金额和税额。该表用于日常数据核查和差异定位，不作为发货 V1 的金额输入。
