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

Use `is_gather` to decide source:

- `is_gather != 0`: collect from expense detail / CB by mapped `cost_code`.
- `is_gather = 0`, or no gathered mapping for the subject: collect from voucher tables.

Expense detail cost codes must also exist in the ZCM allowed set:

```sql
SELECT item.cost_code, item.cost_name
FROM dp_ods.doris_ods_zcm_cost_item item
LEFT JOIN dp_ods.doris_ods_zcm_cost_attribution attr
  ON item.cost_attribution_id = attr.id
WHERE attr.id IN (1, 2, 3, 5, 17, 19);
```

For CB / cross-border expense detail, apply the same allowed set and additionally exclude `CI168`.

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

## Department Attribution Drift

Use this when FMS/middle totals match, downstream all-department totals match, but a single department is short or over. It often happens when shops changed departments around the business month.

Middle amount for the requested department, subject cost code, shop, and date:

```sql
SELECT
  e.trans_dt AS dt,
  e.shop_code,
  MAX(s.name) AS shop_name,
  SUM(e.income_cost - e.expend_cost) AS middle_amount
FROM dp_ods.doris_ods_upload_expense_detail e
JOIN dp_dim.doris_dim_shop s
  ON s.shop_code = e.shop_code
 AND s.dt = e.trans_dt
WHERE e.trans_dt >= '2026-04-01'
  AND e.trans_dt <  '2026-05-01'
  AND e.is_deleted = 0
  AND s.structure_id = 507
  AND e.cost_code = 'CI168'
GROUP BY e.trans_dt, e.shop_code;
```

Downstream split for the same shops across all departments:

```sql
WITH scoped_shops AS (
  SELECT DISTINCT e.shop_code
  FROM dp_ods.doris_ods_upload_expense_detail e
  JOIN dp_dim.doris_dim_shop s
    ON s.shop_code = e.shop_code
   AND s.dt = e.trans_dt
  WHERE e.trans_dt >= '2026-04-01'
    AND e.trans_dt <  '2026-05-01'
    AND e.is_deleted = 0
    AND s.structure_id = 507
    AND e.cost_code = 'CI168'
)
SELECT
  d.shop_code,
  MAX(d.shop_name) AS shop_name,
  d.department_id,
  SUM(d.share) AS downstream_amount
FROM dp_dws.doris_dws_finance_cost_sbjct d
JOIN scoped_shops ss ON ss.shop_code = d.shop_code
WHERE d.dt >= '2026-04-01'
  AND d.dt <  '2026-05-01'
  AND d.subject_code = '1122.01.01'
  AND d.source = '0'
  AND d.cost_code = 'CI168'
GROUP BY d.shop_code, d.department_id
ORDER BY ABS(SUM(d.share)) DESC;
```

Shop organization history around the month:

```sql
SELECT
  shop_code,
  structure_id,
  MIN(dt) AS min_dt,
  MAX(dt) AS max_dt,
  COUNT(*) AS days,
  MAX(name) AS sample_name
FROM dp_dim.doris_dim_shop
WHERE shop_code IN ('SC0082', 'SC0137')
  AND dt BETWEEN '2026-03-01' AND '2026-04-30'
GROUP BY shop_code, structure_id
ORDER BY shop_code, structure_id;
```

## Known Example From 2026-05 电商一部

After converting CB using `fms_support.exchange_rate_system`, these subjects reconcile to downstream within decimal precision:

- `6601.36` 卖家运费
- `6601.47.12` 环保费
- `6601.47.14` 平台罚款
- `6601.46.01` 直通车

The previous 9w difference on seller freight was caused by comparing CB original currency to downstream standard currency.

## Known Example From 2026-04 电商一部

`1122.01.01 应收账款_国内销售_线上直销` had a department-scoped downstream difference of about `1,909,417.28`. The main driver was `CI168 销售回款`: middle layer for 电商一部 was about `9,939,397.31`, while downstream 电商一部 was about `8,029,841.59`. The missing department amount existed downstream under prior departments: about `1,844,427.12` under 电商九部 and `65,128.60` under 品牌四部. Affected shops had changed to 电商一部 on `2026-04-01`, while downstream kept part of the amount under the previous department.
