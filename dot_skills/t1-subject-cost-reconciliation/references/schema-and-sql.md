# T+1 科目费用核对 SQL 参考

## Layers

上游 FMS:

- `fms_cost.expense_detail`: 普通费用明细，金额 `income_cost - expend_cost`。
- `fms_cost.his_expense_detail_<year>`: archived ordinary expense detail. Include it for historical months when rows have moved out of current `expense_detail`.
- `fms_cost.expense_detail_cb`: CB 费用明细，金额是原币，字段 `currency_code`。
- `fms_bill.voucher` + `fms_bill.voucher_detail`: FMS 凭证详情，业务报表口径 `account_set = 4`。

中游数仓:

- `dp_ods.doris_ods_upload_expense_detail`: ordinary expense detail ODS.
- `dp_ods.doris_ods_fms_cost_expense_detail_cb`: CB expense detail ODS.
- `dp_dws.doris_dws_voucher_subject_mid`: voucher subject middle table.

下游:

- `dp_dws.doris_dws_finance_cost_sbjct`: allocation success, amount `share`.
- `dp_dws.doris_dws_finance_cost_sbjct_failure`: allocation failure, amount `result_amount`.

## Subject to Cost Item Mapping

Use:

```sql
SELECT
  cgs.subject_code,
  cgs.cost_code,
  ci.cost_name,
  cgs.is_gather
FROM fms_support.cost_gather_strategy cgs
LEFT JOIN fms_cost.cost_item ci ON ci.cost_code = cgs.cost_code
WHERE cgs.subject_code IN ('6601.36');
```

Use active/gathered mappings for reconciliation unless the user asks to audit disabled historical mappings.

## CB Conversion

CB source amount is original currency:

```sql
SUM(income_cost - expend_cost)
```

Convert each date/currency bucket with:

```sql
SELECT source_currency_code, target_currency_code, direct_exchange_rate,
       effective_date, expiring_date
FROM fms_support.exchange_rate_system
WHERE target_currency_code = 'CNY'
  AND effective_date <  '2026-06-01'
  AND expiring_date >= '2026-05-01';
```

For CNY use rate `1`. For non-CNY use the rate whose date range contains `trans_dt`.

## Voucher Query Pattern

```sql
SELECT
  vd.subject_code,
  -SUM(vd.debit_standard_currency_amount - vd.credit_standard_currency_amount) AS expense_amount
FROM fms_bill.voucher_detail vd
JOIN fms_bill.voucher v ON vd.voucher_id = v.voucher_id
WHERE v.business_date >= '2026-05-01'
  AND v.business_date <  '2026-06-01'
  AND v.account_set = 4
  AND vd.subject_code IN ('6601.36')
  AND FIND_IN_SET('2_&_507', vd.accounting_dimension) > 0
GROUP BY vd.subject_code;
```

Omit the `FIND_IN_SET` condition when the user does not provide a department scope.

## Downstream Query Pattern

Success:

```sql
SELECT subject_code, SUM(share) AS amount
FROM dp_dws.doris_dws_finance_cost_sbjct
WHERE dt >= '2026-05-01'
  AND dt <  '2026-06-01'
  AND department_id = '507'
  AND subject_code IN ('6601.36')
GROUP BY subject_code;
```

Omit `department_id` when the user does not provide a department scope.

Failure:

```sql
SELECT subject_code, SUM(result_amount) AS amount
FROM dp_dws.doris_dws_finance_cost_sbjct_failure
WHERE dt >= '2026-05-01'
  AND dt <  '2026-06-01'
  AND department_id = '507'
  AND subject_code IN ('6601.36')
GROUP BY subject_code;
```

## Known Example From 2026-05 电商一部

After converting CB using `fms_support.exchange_rate_system`, these subjects reconcile to downstream within decimal precision:

- `6601.36` 卖家运费
- `6601.47.12` 环保费
- `6601.47.14` 平台罚款
- `6601.46.01` 直通车

The previous 9w difference on seller freight was caused by comparing CB original currency to downstream standard currency.
