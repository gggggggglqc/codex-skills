# T+1 科目费用核对 SQL 参考

## 数据层级

上游 FMS:

- `fms_cost.expense_detail`: 普通费用明细，金额 `income_cost - expend_cost`。
- `fms_cost.his_expense_detail_<year>`：归档后的普通费用明细。历史月份数据如果已从当前 `expense_detail` 迁出，需要一起纳入。
- `fms_cost.expense_detail_cb`: CB 费用明细，金额是原币，字段 `currency_code`。
- `fms_bill.voucher` + `fms_bill.voucher_detail`: FMS 凭证详情，业务报表口径 `account_set = 4`。

中游数仓:

- `dp_ods.doris_ods_upload_expense_detail`：普通费用明细 ODS。
- `dp_ods.doris_ods_fms_cost_expense_detail_cb`：CB 费用明细 ODS。
- `dp_dws.doris_dws_voucher_subject_mid`：凭证科目中表。

下游:

- `dp_dws.doris_dws_finance_cost_sbjct`：分摊成功表，金额字段 `share`。
- `dp_dws.doris_dws_finance_cost_sbjct_failure`：分摊失败表，金额字段 `result_amount`。

## 科目与费用项目映射

使用：

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

使用 `is_gather` 判断数据来源：

- `is_gather != 0`：按映射的 `cost_code` 从费用明细 / CB 获取。
- `is_gather = 0`，或科目没有采集映射：从凭证表获取。

费用明细的 `cost_code` 还必须在 ZCM 允许范围内：

```sql
SELECT item.cost_code, item.cost_name
FROM dp_ods.doris_ods_zcm_cost_item item
LEFT JOIN dp_ods.doris_ods_zcm_cost_attribution attr
  ON item.cost_attribution_id = attr.id
WHERE attr.id IN (1, 2, 3, 5, 17, 19);
```

CB / 跨境费用明细同样使用上述允许范围，并且额外排除 `CI168`。

## CB 汇率折算

CB 来源金额是原币：

```sql
SUM(income_cost - expend_cost)
```

按日期和币别分组后，用以下汇率范围折算：

```sql
SELECT source_currency_code, target_currency_code, direct_exchange_rate,
       effective_date, expiring_date
FROM fms_support.exchange_rate_system
WHERE target_currency_code = 'CNY'
  AND effective_date <  '2026-06-01'
  AND expiring_date >= '2026-05-01';
```

CNY 汇率按 `1` 处理。非 CNY 使用日期范围覆盖 `trans_dt` 的汇率。

## 凭证查询模板

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

用户未提供部门范围时，去掉 `FIND_IN_SET` 条件。

## 下游查询模板

成功表：

```sql
SELECT subject_code, SUM(share) AS amount
FROM dp_dws.doris_dws_finance_cost_sbjct
WHERE dt >= '2026-05-01'
  AND dt <  '2026-06-01'
  AND department_id = '507'
  AND subject_code IN ('6601.36')
GROUP BY subject_code;
```

用户未提供部门范围时，去掉 `department_id` 条件。

失败表：

```sql
SELECT subject_code, SUM(result_amount) AS amount
FROM dp_dws.doris_dws_finance_cost_sbjct_failure
WHERE dt >= '2026-05-01'
  AND dt <  '2026-06-01'
  AND department_id = '507'
  AND subject_code IN ('6601.36')
GROUP BY subject_code;
```

## 部门归属漂移

当 FMS/中游合计一致、下游全部门合计也一致，但单个部门少或多时使用本节。常见原因是店铺在业务月份前后发生部门变更。

按指定部门、科目费用项目、店铺、日期查询中游金额：

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

查询同一批店铺在下游全部门的拆分：

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

查询业务月份前后的店铺组织历史：

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

## 已知案例：2026-05 电商一部

使用 `fms_support.exchange_rate_system` 折算 CB 后，以下科目与下游可在小数精度内对齐：

- `6601.36` 卖家运费
- `6601.47.12` 环保费
- `6601.47.14` 平台罚款
- `6601.46.01` 直通车

卖家运费曾出现约 9 万差异，原因是拿 CB 原币金额直接和下游本位币金额比较。

## 已知案例：2026-04 电商一部

`1122.01.01 应收账款_国内销售_线上直销` 在部门范围内的下游差异约 `1,909,417.28`。主因是 `CI168 销售回款`：中游电商一部约 `9,939,397.31`，下游电商一部约 `8,029,841.59`。缺少的部门金额实际存在于下游原部门：电商九部约 `1,844,427.12`，品牌四部约 `65,128.60`。受影响店铺在 `2026-04-01` 转入电商一部，但下游仍有部分金额留在原部门。
