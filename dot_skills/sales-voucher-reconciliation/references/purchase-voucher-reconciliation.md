# 采购业务与集团核算凭证借方核对

## 用户确认口径（2026-10-01）

每次核对由用户输入月份，两侧按 `business_date` 取同一期间。

| 目标科目 | 业务分组 | 金额字段 | 计算公式 | 凭证取值 |
|---|---|---|---|---|
| `1405.02.03` 库存商品_产成品_发货 | 201 采购入库、206 采购入库-线下分销、202 采购退货 | **子单** `no_tax_amount` | 201＋206－202 | 借方发生额 |
| `1405.05` 库存商品_耗材 | 205 耗材采购入库 | **子单** `no_tax_amount` | 205 | 借方发生额 |

账套固定集团核算 `account_set=3`，采购凭证来源 `voucher_resource=9`。

本表是用户明确指定的核对关系，优先于配置自动推导。不要纳入项目组自采、耗材项目组自采、返厂异常、开箱异常等其他分组；不要用主单金额、含税金额、采退金额字段或借贷净额替代。采购退货的不含税金额按公式减一次，不再额外套配置冲销减第二次。206 的贷方金额仅作附带诊断，不从借方发生额中减去。采购不应用销售的 JDZY 剔除规则。

## 取数与检查

使用 `database-config` 的本地只读 `erp-mysql` profile。业务来源 `fms_cost.psi_purchase_record` 主表关联 `psi_purchase_record_detail` 子单，关联键 `business_no`。先检查主表单号唯一性，避免关联放大；检查缺子单、空不含税金额，并单列异常。

逐日参数化取业务分组金额：

```sql
SELECT r.psi_group_type, COUNT(DISTINCT r.business_no) AS business_count,
       COUNT(d.id) AS detail_count,
       SUM(d.no_tax_amount) AS no_tax_amount
FROM fms_cost.psi_purchase_record r
JOIN fms_cost.psi_purchase_record_detail d ON d.business_no=r.business_no
WHERE r.business_date=%s
  AND r.psi_group_type IN (201,202,205,206)
GROUP BY r.psi_group_type;
```

逐日参数化取对应科目借方：

```sql
SELECT vd.subject_code, v.voucher_status,
       COUNT(DISTINCT v.voucher_id) AS voucher_count,
       SUM(COALESCE(vd.debit_amount,0)) AS debit_amount,
       SUM(COALESCE(vd.credit_amount,0)) AS diagnostic_credit_amount
FROM fms_bill.voucher v
JOIN fms_bill.voucher_detail vd ON vd.voucher_id=v.voucher_id
WHERE v.business_date=%s
  AND v.account_set=3 AND v.voucher_resource=9
  AND vd.subject_code IN ('1405.02.03','1405.05')
GROUP BY vd.subject_code,v.voucher_status;
```

保留红字借方的负号；不取绝对值，不把借方＋贷方或借方－贷方作为核对金额。凭证取上述来源和账套下两科目的全部借方，其他业务落入同科目时作为差异解释单列，不能静默筛掉。

**状态须核实真实枚举，不能只信数据库字段注释。** 本地 `fms-bill` 的 `VoucherAuditStatusEnum` 为 0已保存、1已审核、2已提交、3已过账、4暂存；2不是已删除。2026年8月查得目标凭证均为3已过账，应纳入。若发现无效/删除凭证，先验证真实删除机制后剔除并披露，不能按未经验证的状态排除。

## 差异定位

- `diff = 业务公式金额 - 凭证借方发生额`，正数表示业务侧较大。
- Decimal 保留子单源精度；展示保留两位小数，同时记录未四舍五入差异。月度小差异先按单据/凭证舍入检查，不能自行认定全部为尾差。
- 汇总输出两个科目分别的业务金额、借方发生额、差异、差异率、状态；并给出四个分组金额及逐日差异。
- 以 `business_no` 与 `voucher.resource_no` 关联定位前，验证实际值。合并凭证通过已核实的 `psi_merge_voucher_relation` 展开，不假设所有来源号均为单号。
- 保留全部业务，不限定推送成功；未生成金额不能因筛选状态消失。对“8月期间没凭证”的业务检查其他业务日期是否存在，区分跨期与未生成。
- 业务和凭证都为0不代表取数已完整；凭证为0而业务非0时差异率为空且明确有差异，不设0%判MATCH。
- 逐单不一致时，可查凭证配置、组织拆分、供应商属性、历史修改与尾差处理辅助解释，但不能修改用户已确认公式来让结果对平。

同时核对销售时，独立展示销售收入、采购产成品发货、采购耗材，不混合求和。

## 依据与执行方式

用户在2026-10-01明确确认以上公式；分组编号来自本地 `fms-cost` 的 `PsiGroupTypeEnum`。科目编码来自 `fms_support.subject` 的集团账套主数据；账套3来自 `fms-remote` 的 `KingDeeAccountBookEnum`；采购来源9来自 `fms-bill` 的 `VoucherResourceTypeEnum`。

现有 `scripts/reconcile.py` 仅执行销售。采购按本参考执行只读查询与公式汇总，不用销售脚本结果代替。输出包括金额口径与数据异常检查，不能在只更新技能后声称完成实际核对。
