---
name: t1-subject-cost-reconciliation
description: 当用户要求核对某月某个或多个 T+1 科目费用、科目费用分摊差异、FMS 业务报表/费用明细/CB/凭证详情与数仓 ODS/凭证中表/科目费用分摊成功失败表是否一致时使用，尤其涉及电商部门、费用采集策略、CB 原币折本位币、上游 FMS、中游 dp_ods/doris_dws_voucher_subject_mid、下游 doris_dws_finance_cost_sbjct/doris_dws_finance_cost_sbjct_failure 三方对数。
---

# T+1 科目费用核对

## 核心流程

除非用户只要 SQL，否则优先使用技能内置脚本：

```bash
python3 /Users/liuqingchen/.skills/t1-subject-cost-reconciliation/scripts/reconcile_t1_subject_cost.py \
  --month 2026-05 \
  --subject 6601.36
```

多个科目时重复传入 `--subject`：

```bash
python3 /Users/liuqingchen/.skills/t1-subject-cost-reconciliation/scripts/reconcile_t1_subject_cost.py \
  --month 2026-05 \
  --subject 6601.36 \
  --subject 6601.47.12 \
  --subject 6601.47.14 \
  --subject 6601.46.01
```

如果用户给的是科目名称而不是科目编码，先查询 FMS 科目或历史凭证确认准确的 `subject_code`。存在多个可能编码时，不要猜。

部门是可选条件。只有用户明确提供部门或要求按已知部门范围核对时，才添加 `--department-id <id>`。如果用户没有提供部门，不要限制部门。

## 必核范围

核对三层数据：

1. 上游 FMS：
   - `fms_cost.expense_detail`
   - `fms_cost.his_expense_detail_<year>`：当业务月份的费用明细已归档时需要一起纳入
   - `fms_cost.expense_detail_cb`
   - `fms_bill.voucher` + `fms_bill.voucher_detail`
2. 中游数仓：
   - `dp_ods.doris_ods_upload_expense_detail`
   - `dp_ods.doris_ods_fms_cost_expense_detail_cb`
   - `dp_dws.doris_dws_voucher_subject_mid`
3. 下游分摊：
   - 成功表：`dp_dws.doris_dws_finance_cost_sbjct`
   - 失败表：`dp_dws.doris_dws_finance_cost_sbjct_failure`

下游必须始终按成功表 + 失败表合计比较。

## 关键规则

- 使用业务月份：费用表按 `trans_dt`；凭证按 `business_date`；下游按 `dt`。
- 核对较早月份时，必须把对应 FMS 历史表一起纳入，例如 `fms_cost.his_expense_detail_2026` 与当前 `expense_detail` 合并，否则 FMS 可能看起来缺少月初已归档数据。
- 只有用户提供部门时才限制部门。费用/CB 按店铺组织过滤，凭证按部门核算维度过滤。用户未提供部门时不要限制部门。
- 使用 `fms_support.cost_gather_strategy.is_gather` 判断来源：
  - `is_gather != 0`：按映射的 `cost_code` 从费用明细 / CB 获取。
  - `is_gather = 0` 或没有采集映射：从凭证表获取。
- `expense_detail` 费用项目必须限制在 ZCM 费用项目归属 `attr.id in (1, 2, 3, 5, 17, 19)` 范围内。
- CB / 跨境费用明细同样使用 ZCM 费用项目限制，并且额外排除 `CI168`。
- 费用和 CB 金额方向按 `SUM(income_cost - expend_cost)`；凭证方向按 `-SUM(debit_standard_currency_amount - credit_standard_currency_amount)`。
- CB 金额是原币，与下游比较前必须折算为本位币。
- 与下游分摊核对时，汇率使用 FMS 汇率表 `fms_support.exchange_rate_system`，不要使用日汇率 `oms_business.exchange_rate`。
- FMS 业务报表凭证口径使用 `voucher.account_set = 4`。
- 凭证部门核算维度格式是 `2_&_<department_id>`；店铺维度分隔符是 `4_&_`。
- 下游成功表金额字段是 `share`；失败表金额字段是 `result_amount`。
- 下游必须与上游保持相同来源拆分：采集/费用类科目对比 `source = 0`；凭证类科目对比 `source = 1`。
- 如果部门范围内存在差异，但下游全部门合计与中游一致，要检查店铺组织历史。费用行按 `shop_code` 和业务日期关联 `dp_dim.doris_dim_shop`，再按下游 `department_id` + `shop_code` 拆分比较；店铺转部门可能导致部分下游金额留在原部门。
- 至少按以下口径展示差异：
  - FMS 合计 vs 中游合计
  - 中游合计 vs 下游成功表 + 失败表合计
  - 组成拆分：普通费用明细、CB 折本位币金额、凭证金额

## 差异排查顺序

按以下顺序排查：

1. CB 币别：对比原币合计和折 CNY 后合计。
2. FMS vs ODS 同步：比较 `expense_detail` 与 `doris_ods_upload_expense_detail`，以及 `expense_detail_cb` 与 `doris_ods_fms_cost_expense_detail_cb`。
3. 凭证方向和日期：使用凭证 `business_date`，不要使用数仓分区日期。是否纳入凭证科目必须根据 `cost_gather_strategy.is_gather` 判断。
4. 下游失败表：必须纳入 `doris_dws_finance_cost_sbjct_failure.result_amount`。
5. 核算维度缺失：费用行检查缺失或无法匹配的 `shop_code`；凭证在需要店铺级核对时检查是否缺少部门 `2_&_` 或店铺 `4_&_`。
6. 分摊逻辑：如果上游/中游一致，CB 折本位币后仍与下游不同，按下游 `source`、`cost_code`、`shop_code`、`dt` 拆分。
7. 部门归属漂移：如果拆分结果显示同一店铺/日期金额在下游进入了其他部门，要检查业务月份前后 `dp_dim.doris_dim_shop` 的组织变更。这属于部门归属不一致，不是数据丢失。

## 已知差异模式

- `2026-04` 电商一部 `1122.01.01 应收账款_国内销售_线上直销`：FMS 与中游一致，但下游部门范围内少约 `1,909,417.28`。根因是 `CI168 销售回款` 涉及 `2026-04-01` 转入电商一部的店铺；下游仍有部分金额留在原部门，主要是电商九部，少量在品牌四部。下游全部门合计与中游一致，因此问题是部门归属漂移。

## 参考资料

- 需要表字段、SQL 模板或口径说明时，读取 `references/schema-and-sql.md`。
- 数据库连接约定和只读 profile 使用方式参考 `数据查询助手`。
