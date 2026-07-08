---
name: t1-subject-cost-reconciliation
description: T+1 科目费用上中下游核对技能。Use when the user asks to 核对某月某个或多个 T+1 科目费用、科目费用分摊差异、FMS 业务报表/费用明细/CB/凭证详情与数仓 ODS/凭证中表/科目费用分摊成功失败表是否一致，尤其涉及电商部门、费用采集策略、CB 原币折本位币、上游 FMS vs 中游 dp_ods/doris_dws_voucher_subject_mid vs 下游 doris_dws_finance_cost_sbjct/doris_dws_finance_cost_sbjct_failure 的对数。
---

# T+1 科目费用核对

## Core Workflow

Use the bundled script first unless the user only wants SQL:

```bash
python3 /Users/liuqingchen/.skills/t1-subject-cost-reconciliation/scripts/reconcile_t1_subject_cost.py \
  --month 2026-05 \
  --subject 6601.36
```

For multiple subjects, repeat `--subject`:

```bash
python3 /Users/liuqingchen/.skills/t1-subject-cost-reconciliation/scripts/reconcile_t1_subject_cost.py \
  --month 2026-05 \
  --subject 6601.36 \
  --subject 6601.47.12 \
  --subject 6601.47.14 \
  --subject 6601.46.01
```

If the user gives subject names instead of codes, first query FMS subject or voucher history to confirm the exact `subject_code`. Do not guess a code when multiple matches are possible.

Department is optional. Only add `--department-id <id>` when the user explicitly provides a department or asks for a known department scope. If no department is provided, do not restrict department.

## Required Reconciliation Scope

Reconcile three layers:

1. Upstream FMS:
   - `fms_cost.expense_detail`
   - `fms_cost.his_expense_detail_<year>` when the business month has archived expense rows
   - `fms_cost.expense_detail_cb`
   - `fms_bill.voucher` + `fms_bill.voucher_detail`
2. Middle warehouse:
   - `dp_ods.doris_ods_upload_expense_detail`
   - `dp_ods.doris_ods_fms_cost_expense_detail_cb`
   - `dp_dws.doris_dws_voucher_subject_mid`
3. Downstream allocation:
   - success: `dp_dws.doris_dws_finance_cost_sbjct`
   - failure: `dp_dws.doris_dws_finance_cost_sbjct_failure`

Always compare downstream as success + failure.

## Critical Rules

- Use business month: expense tables by `trans_dt`; vouchers by `business_date`; downstream by `dt`.
- For older months, include the matching FMS history table such as `fms_cost.his_expense_detail_2026` together with current `expense_detail`; otherwise FMS may appear to miss early archived days.
- Filter department by shop structure for expense/CB rows and by department dimension for voucher rows only when the user provides a department. Otherwise do not restrict department.
- Use `fms_support.cost_gather_strategy.is_gather` to decide source:
  - `is_gather != 0`: collect from expense detail / CB by mapped `cost_code`.
  - `is_gather = 0` or no gathered mapping: collect from voucher tables.
- Expense detail cost codes must be limited to ZCM cost items whose attribution id is in `(1, 2, 3, 5, 17, 19)`.
- CB/cross-border expense detail follows the same ZCM cost item limit, and additionally excludes `CI168`.
- Treat expense direction as negative: `SUM(income_cost - expend_cost)` for expense and CB; voucher direction is `-SUM(debit_standard_currency_amount - credit_standard_currency_amount)`.
- CB amount is original currency. Convert CB to standard currency before comparing with downstream.
- Use FMS exchange rates from `fms_support.exchange_rate_system`, not daily `oms_business.exchange_rate`, when checking against downstream allocation.
- FMS business-report voucher scope uses `voucher.account_set = 4`.
- Voucher department dimension format is `2_&_<department_id>`; shop dimension delimiter is `4_&_`.
- Downstream success amount field is `share`; failure amount field is `result_amount`.
- Downstream must use the same source split as upstream: gathered/expense subjects compare to `source = 0`; voucher subjects compare to `source = 1`.
- When a department-scoped difference exists but all-department downstream total matches the middle layer, check shop organization history. Join expense rows to `dp_dim.doris_dim_shop` by `shop_code` and business date, then compare downstream `department_id` split by `shop_code`; shop transfers can leave part of downstream under the prior department.
- Report differences at least as:
  - FMS total vs middle total
  - middle total vs downstream success+failure total
  - component split: expense detail, CB converted amount, voucher amount

## When Results Differ

Check in this order:

1. CB currency: compare original currency totals and converted CNY totals.
2. FMS vs ODS sync: compare `expense_detail` to `doris_ods_upload_expense_detail`, and `expense_detail_cb` to `doris_ods_fms_cost_expense_detail_cb`.
3. Voucher direction and date: use voucher `business_date`, not warehouse partition date. Only include voucher subjects according to `cost_gather_strategy.is_gather`.
4. Downstream failure: include `doris_dws_finance_cost_sbjct_failure.result_amount`.
5. Missing accounting dimensions: for expense rows check missing/unmatched `shop_code`; for vouchers check missing department `2_&_` or shop `4_&_` only when shop-level reconciliation is requested.
6. Allocation logic: if upstream/middle match but downstream differs after CB conversion, split downstream by `source`, `cost_code`, `shop_code`, and `dt`.
7. Department allocation drift: if the split shows the same shop/date amount exists in downstream under other departments, inspect `dp_dim.doris_dim_shop` before and during the business month for organization changes. Treat this as department attribution mismatch, not data loss.

## Known Difference Patterns

- `2026-04` 电商一部 `1122.01.01 应收账款_国内销售_线上直销`: FMS and middle matched, but downstream department scope was lower by about `1,909,417.28`. Root cause was `CI168 销售回款` for shops transferred to 电商一部 on `2026-04-01`; downstream still kept part of the amount under prior departments, mainly 电商九部 and a small amount under 品牌四部. The all-department downstream total matched the middle layer, so the issue was department attribution drift.

## References

- Read `references/schema-and-sql.md` when you need table fields, SQL patterns, or to explain the logic.
- Use `数据查询助手` for database connection conventions and readonly profile handling.
