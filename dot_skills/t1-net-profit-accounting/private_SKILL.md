---
name: t1-net-profit-accounting
description: T+1 净利核算规则技能。用于梳理、解释、实现或核对 T+1 净利报表口径，包括 doris_app_net_profit_check_report_v2、凭证科目中间表、科目费用分摊成功/失败表、费用编码 EP001-EP036、业务上传临时表、收入成本费用分摊、跨境费用分摊、人工/集团管理/分摊费用、天猫超市特殊分摊、供应商采购占比分摊、按收入/成本/发货方量分摊，以及相关 SQL/数据源/字段口径排查。
---

# T+1 净利核算

## Quick Start

Use this skill when the user asks about T+1 净利核算口径、字段来源、费用分摊、数据核对、SQL 实现或差异排查.

Start from the latest rule set unless the user specifies an older version:

1. Prefer `2026科目费用分摊优化` for 科目费用分摊.
2. Prefer `2025-08跨境收入成本费用分摊` for 净利 V2 收入、成本、费用汇总.
3. Use `新增费用名称字典表` for EP 编码到费用/科目的映射.
4. Use `业务上传临时表` for人工、研发、集团管理、分摊费用、费比和费用金额的上传规则.
5. When the question needs exact business logic, read [references/t1-net-profit-rules.md](references/t1-net-profit-rules.md).

The source workbook did not contain a literal sheet named `sheet1`; the rules were整理 from all named sheets except no literal `sheet1`.

## Workflow

1. Identify the target output.
   - 口径解释: summarize dimensions, source tables, filters, and calculation rules.
   - SQL/ETL implementation: produce source table joins, filters, allocation grain, success/failure handling, and sign rules.
   - 差异排查: check refresh window, date grain, source flag, allocation basis, supplier allocation fallback, upload month fallback, and failure-table reasons.

2. Choose the rule family.
   - 凭证科目: use `doris_dws_voucher_subject_mid`; voucher, voucher_detail, accounting_dimension, cost_gather_strategy, and subject are core.
   - 科目费用分摊: use `dp_dws.doris_dws_finance_cost_sbjct` and `dp_dws.doris_dws_finance_cost_sbjct_failure`.
   - 净利汇总: use `doris_app_net_profit_check_report_v2`.
   - 业务上传: use the temporary upload table rules; blank uploads become 0 in the net profit table.

3. Apply the common allocation hierarchy.
   - SKU income/cost/volume is allocated to suppliers by `dp_dws.doris_dws_srm_purchase_num_percentage_mid`.
   - If supplier purchase percentage is missing, fall back to the supplier from the order/index source, defaulting to the first supplier; skip defective supplier `G100197` when choosing the first supplier.
   - For account-subject expenses, use `cost_share_method`: `0` income, `1` cost, `2` shipped volume.
   - Treat income-side expense ownership as positive and cost/expense-side ownership as negative when building net profit amount rows.

4. Apply date and refresh rules.
   - Voucher subject middle table refreshes the recent 45 days.
   - Non-amortized account-subject expenses follow the recent 45-day update/delete window.
   - Amortized or monthly backfill data is processed separately for the prior month, historically on the 8th; later versions mention the 5th and 7th for some backfills.
   - Net profit V2 normally backfills the prior month on the 8th unless a specific version states otherwise.

5. Validate edge cases before concluding.
   - Domestic vs cross-border filters.
   - `佳帮手分销旗舰店XX【业务公共】`, `班牛`, and `产销事业群` exclusions.
   - Tmall Supermarket special handling.
   - Upload amount vs fee-ratio priority.
   - Negative income sign handling.
   - Failure-table path when no allocation basis can be found.

## Source Notes

This skill was created from `C:\Users\lqc\Downloads\T+1净利核算表.xlsx`, excluding only a literal `sheet1` if present.

If a future workbook version is provided, update the reference file first, then keep this `SKILL.md` focused on routing and workflow rather than copying every row into the main skill body.

## 最新 T+1 需求动态（2026-06 更新）

来源：[T+1需求登记表](https://alidocs.dingtalk.com/i/nodes/QOG9lyrgJP3PAm3kubkrwd0nVzN67Mw4)

| 日期 | 提出人 | 需求 | 状态 |
|---|---|---|---|
| 2026-06-18 | 冯小锋 | 所得税计算逻辑修改 | 已沟通 |
| 2026-04-24 | 吴泽祥 | T+1达人增加7日环比和月完成率，导入业务目标 | 待定 |
| 2026-04-20 | 冯小锋 | 凭证状态已审核+已过账都要取数 | 待定 |
| 2026-04-16 | 吴泽祥 | 补发订单成本归属达人 | 待定 |
| 2026-04-13 | 财务和业务 | 财年净利包含3.31数据 | 开发中 |
| 2026-04-10 | 内控组 | 部门增加可发天数，一元人力改成人力成本占比 | 需求梳理中 |
| 2026-04-01 | 老板 | 净利换成税后净利（不含税收入/成本/费用） | 开发中 |
| 2026-02-27 | 老板 | 收入用产值，成本用最新存货价/报价 | 待定 |
| 2026-01-21 | 吴泽祥 | 平台链接增加发货量字段 | 开发中 |
| 2025-10-16 | 郭元迎 | 完成口径T+1（收入/成本/科目分摊/净利） | 需求梳理中 |
