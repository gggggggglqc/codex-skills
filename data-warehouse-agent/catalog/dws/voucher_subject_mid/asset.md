---
asset_id: dws.voucher_subject_mid
layer: DWS
table_name: doris_dws_voucher_subject_mid
database: dp_dws
business_name: 凭证科目中间表
status: 部分确认
refresh:
  frequency: 每日
  timezone: Asia/Shanghai
  load_window: 最近45天回刷
  load_strategy: 回刷方式待确认
grain: 业务日期 + 科目 + 分摊维度组合
primary_key: 待确认（DDL 未声明 KEY）
partition:
  field: dt
  semantic: 创建时间分区（业务发生日期）
  strategy: DDL 未声明 PARTITION BY
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE dp_dws.doris_dws_voucher_subject_mid DDL, locator: dp_dws.doris_dws_voucher_subject_mid, observed_at: 2026-08-18 }
---

# 凭证科目中间表

包含 `business_date`、科目层级、分摊维度/方法、货主/仓库/供应商/店铺/部门/分销商、达人，以及不含税 `result_amount`、税额 `tax_amount`、含税 `amount`。供科目费用分摊成功/失败表构建使用。

## 已确认构建规则

- 原始凭证链路：`fms_bill.voucher` 与 `fms_bill.voucher_detail` 按 `voucher_id` 关联；仅取 `voucher.account_set = 4`。
- 核算维度：`fms_bill.voucher_detail` 与 `fms_bill.voucher_detail_accounting_dimension` 按 `voucher_detail_id` 关联；依据 `accounting_dimension_type` 拆出经营维度。
- 金额方向：按 `cost_gather_strategy.cost_belong` 判断。收入类最终金额为正，成本类和费用类最终金额为负。
- 科目/费用策略：`cost_gather_strategy` 管理科目、费用项目、费用归属及是否采集/计提；文档说明同一科目仅有一种费用归属。

`expense_detail`、`expense_detail_cb` 是国内/跨境费用账单及业务上传的落表；它们的账单过滤与币别处理属于费用账单链路，不作为本 Sheet 已定义的凭证中间表构建前置规则。

## 核算维度类型：已确认语义

FMS 服务 `AccountingDimensionSupport` 已确认以下枚举名称及其业务编码字段。数仓构建可按名称对应 `accounting_dimension_type` 的数值；完整“枚举名称—数值”源码未在本地工作区或依赖缓存中找到，暂不臆测未核验数值。

| 枚举名称 | 维度编码 | 净利中间表去向 |
|---|---|---|
| `COMPANY` | `company_code` | 公司维度（辅助） |
| `SHOP` | `shop_code` | `shop_code` |
| `OWNER` | `owner_code` | `owner_code` |
| `WAREHOUSE` | `warehouse_code` | `warehouse_code` |
| `DEPARTMENT` | 组织 `id` | `department_code` |
| `SUPPLIER` | `supplier_code` | `supplier_code` |
| `DISTRIBUTOR` | `distributor_id` | `distributor_code` |
| `FEE` | `cost_code` | 费用项目/科目策略关联 |
| `MATERIALS` | `sku_code` 或 `material_code` | 商品/物料辅助维度 |
| `ACCOUNT` | `account_no` | 账户辅助维度 |
| `PRODUCE_FACTORY` | `factory_code` | 工厂辅助维度 |

来源：`/Users/liuqingchen/工作/代码/fms-bill/jbs-fms-bill-service/src/main/java/com/jbs/fms/bill/service/support/AccountingDimensionSupport.java`。
