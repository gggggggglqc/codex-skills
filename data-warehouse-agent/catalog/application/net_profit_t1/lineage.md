# T+1 净利血缘穿透图

> 范围为已确认链路。虚线表示当前仅确认业务来源或上游层级，尚未取得具体 ODS/DWD 物理表映射。

```mermaid
flowchart BT
  boss["老板报表 / 多维净利\nDWP v5.8.6"]
  profit["APP：dp_dws.doris_app_finance_profit_business\n净利指标中间表"]
  v2["APP：dp_dws.doris_app_net_profit_check_report_v2\n净利核算表 V2"]
  success["DWS：doris_dws_finance_cost_sbjct\n科目费用分摊成功"]
  failure["DWS：doris_dws_finance_cost_sbjct_failure\n科目费用分摊失败"]
  relation["DIM：doris_dim_expense_subject_relation\n费用—科目关系"]
  subject["DIM：doris_dim_fms_support_subject\n财务科目"]
  voucher["DWS：doris_dws_voucher_subject_mid\n凭证科目中间表"]
  voucherMain["业务库：fms_bill.voucher\n凭证主表"]
  voucherDetail["业务库：fms_bill.voucher_detail\n凭证明细"]
  voucherDim["业务库：fms_bill.voucher_detail_accounting_dimension\n凭证核算维度"]
  expense["业务库：fms_cost.expense_detail\n国内费用账单 / 上传费用"]
  expenseCb["业务库：fms_cost.expense_detail_cb\n跨境费用账单 / 上传费用"]
  v1["APP：doris_app_report_delivery_v1\n发货口径应用指标"]
  crossTmp["业务导入：tmp_data.abroad_production_revenue_profit\n当月跨境收入/成本拆分结果"]
  crossImport["业务导入：abroad_production_revenue_profit_import\n原始导入表"]
  supplierShare["供应商采购占比分摊\n具体落表待确认"]
  salesDws["DWS：系统订单 / 分销订单 / 分销发货 / 跨境订单 Index"]
  salesOds["ODS：订单、发货、退款等业务事实"]
  control["业务库：ers_expense.expense_order\n费控单据主表"]
  controlDetail["业务库：ers_expense.expense_order_cost_detail\n费控费用明细表"]
  otherExpense["APP：other_expense_data\n净利核算其他费用月度上传"]

  boss --> profit
  profit --> v2
  profit --> success
  profit --> failure
  profit --> relation
  profit --> subject
  success --> voucher
  failure --> voucher
  voucher --> voucherMain
  voucher --> voucherDetail
  voucher --> voucherDim
  voucher -.-> control
  controlDetail --> control
  voucherDetail --> voucherMain
  voucherDim --> voucherDetail
  v2 --> v1
  v2 --> crossTmp
  v2 --> supplierShare
  v2 -.-> otherExpense
  crossTmp --> crossImport
  v1 --> salesDws
  salesDws --> salesOds
```

## 层级说明

- `doris_app_finance_profit_business` 是老板报表的净利汇总入口；其唯一键包含日期、经营主体、商品、科目和国别等维度。
- `doris_app_net_profit_check_report_v2` 承接发货 V1、跨境业务导入、供应商采购占比分摊和业务上传费用。
- 财务费用链路由凭证科目中间表、分摊成功/失败表和费用—科目关系共同补充至净利中间表。凭证事实已确认通过 `voucher_id` 和 `voucher_detail_id` 两级关联，且限定账套 `4`；收入类金额为正，成本/费用类金额为负。费用账单与业务上传是独立费用事实链路，不混入本 Sheet 的凭证中间表构建规则。
- 发货 V1 已确认直接从 DWS Index 取数；DWS 的下游为订单/发货/退款 ODS。各 Index 到 ODS 的详细表级血缘见销售、售后与跨境资产文档。

## 待补的物理穿透

1. 供应商采购占比分摊的输入、计算结果表及其与 V2 的关联键。
