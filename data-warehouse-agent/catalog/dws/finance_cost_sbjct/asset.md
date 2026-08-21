---
asset_id: dws.finance_cost_sbjct
layer: DWS
table_name: doris_dws_finance_cost_sbjct
database: dp_dws
business_name: 财务科目费用分摊事实表
status: 已确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 待确认
  load_strategy: 待确认
grain: 业务发生日期 + 科目/费用项目 + 分摊归属维度的费用事实行
primary_key: DDL 未声明物理唯一键
partition:
  field: dt
  semantic: 创建时间分区（业务发生日期）
  strategy: DDL 未声明 PARTITION BY
version:
  scene: 发货 V1 天猫超市及产销费用补充
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: 用户于会话中提供的 CREATE TABLE dp_dws.doris_dws_finance_cost_sbjct DDL
    locator: dp_dws.doris_dws_finance_cost_sbjct
    observed_at: 2026-08-18
---

# 财务科目费用分摊事实表

提供科目 `subject_code`、费用项目 `cost_code`、含税金额 `share`、不含税金额 `no_tax_amount`、税额 `tax_amount`，以及店铺、平台、公司/部门、商品、仓库等归属维度。发货 V1 的天猫超市收入可按 `shop_plat_code = 'TMCS'` 且 `cost_code IN ('CI168', 'CI654')`、业务日期 `dt` 汇总；文档未要求额外筛选 `source`，不得自行增加。
