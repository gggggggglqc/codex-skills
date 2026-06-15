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
