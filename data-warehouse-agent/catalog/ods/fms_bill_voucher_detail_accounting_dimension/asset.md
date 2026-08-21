---
asset_id: ods.fms_bill_voucher_detail_accounting_dimension
layer: ODS
table_name: voucher_detail_accounting_dimension
database: fms_bill
business_name: 凭证明细核算维度表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 跟随凭证业务日期, load_strategy: 待确认 }
grain: 凭证明细 + 核算维度
primary_key: [id]
indexes: [[voucher_detail_id], [voucher_id], [accounting_dimension]]
source_evidence:
  - { type: business_ddl, path: 用户于会话中提供的 CREATE TABLE fms_bill.voucher_detail_accounting_dimension DDL, locator: fms_bill.voucher_detail_accounting_dimension, observed_at: 2026-08-18 }
  - { type: business_confirmation, path: 用户于会话中提供的 AccountingDimensionTypeEnum, locator: 完整数值枚举, observed_at: 2026-08-19 }
---

# 凭证明细核算维度表

以 `voucher_detail_id` 关联凭证明细，提供拆开的 `accounting_dimension` 与 `accounting_dimension_type`。枚举已确认如下。

| 值 | 枚举 | 名称 | 来源 |
|---:|---|---|---|
| 1 | `SUPPLIER` | 供应商 | ERP |
| 2 | `DEPARTMENT` | 部门 | ERP |
| 3 | `COMPANY` | 公司 | ERP |
| 4 | `SHOP` | 店铺 | ERP |
| 5 | `OWNER` | 货主 | ERP |
| 6 | `FEE` | 费用项目 | ERP |
| 7 | `MATERIALS` | 物料 | ERP |
| 8 | `ACCOUNT` | 银行账号 | ERP |
| 9 | `CONTACT_COMPANY` | 往来单位 | ERP |
| 10 | `TAX_RATE` | 税率 | ERP |
| 11 | `WAREHOUSE` | 仓库 | ERP |
| 12 | `WAREHOUSE_USE_TYPE` | 仓库功能 | ERP |
| 13 | `EMPLOYEE` | 员工 | ERP |
| 14 | `DISTRIBUTOR` | 分销商 | ERP |
| 15 | `TRANSACTION_TYPE` | 交易类型 | 辅助材料 |
| 16 | `SETTING_TYPE` | 设置类型 | 辅助材料 |
| 17 | `REVENUE_COST_ITEMS` | 收入成本项目 | 辅助材料 |
| 18 | `DEVELOPMENT_TYPE` | 研发类型 | 辅助材料 |
| 19 | `DEVELOPMENT_ITEMS` | 研发项目 | 辅助材料 |
| 20 | `LONG_TERM_ITEMS` | 长期项目 | 辅助材料 |
| 21 | `INTELLECTUAL_PROPERTY_CODE` | 知识产权编码 | 辅助材料 |
| 22 | `ASSET_LOCATION` | 资产位置 | 辅助材料 |
| 23 | `FINANCE_CUSTOMER` | 财务客户 | ERP |
| 24 | `DISTRIBUTOR_SETTLE_SHOP` | 分销结算店铺 | ERP |
| 25 | `PRODUCE_FACTORY` | 生产工厂 | ERP |
| 26 | `WORK_SHOP` | 生产车间 | ERP |
| 27 | `LOGISTICS_TYPE` | 物流类型 | ERP |
| 28 | `MOLD` | 模具 | ERP |
| 29 | `LINK_ACCOUNT` | 链接账号 | 辅助材料 |
