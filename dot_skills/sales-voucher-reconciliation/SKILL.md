---
name: sales-voucher-reconciliation
description: 核对销售业务日志(fms_cost.psi_sales)与凭证科目发生额(oms_finance.voucher_detail)的差异。当用户提到"收入凭证核对"、"销售凭证核对"、"psi_sales vs voucher"、"收入对凭证"、"账面收入核对"、"凭证收入差异"、"销售与凭证核对"时使用。支持按月/按店铺/按科目维度核对，输出差异金额、差异率、逐日对比。
version: 1.0.0
---

# 销售业务日志与凭证科目发生额核对

## 核对逻辑

### 左侧：销售业务日志（psi_sales）

- 数据源：MySQL `fms_cost.psi_sales`
- 时间字段：`business_date`
- 公式：`income_fee - refund_amount = net_income`

### 右侧：凭证科目发生额（voucher_detail）

- 数据源：通过 `fms_bill` 库连接访问 `voucher_detail` JOIN `voucher`（oms_query 用户无 oms_finance 直接权限）
- 时间字段：`voucher.business_date`
- 过滤条件：`voucher_resource = 8`（PSI_SALES_RECORD）、`account_set = 3`（集团账套）
- 账面收入公式：`6001% 贷方（主营业务收入） + 2221.01.01% 贷方（应交增值税-销项税额） = book_income`

### 差异判定

- `diff = net_income - book_income`
- `diff_pct = diff / book_income * 100`
- 阈值：`|diff_pct| < 0.1%` 为 MATCH，`< 1%` 为 WARN，`>= 1%` 为 MISMATCH

### 9个业务分组（PsiGroupTypeEnum）

| 编码 | 说明 |
|------|------|
| 101 | 差价交易订单 |
| 105 | 补邮费/差价 |
| 107 | 一般交易-完成 |
| 114 | 售后退货退款 |
| 115 | 售后已收货仅退款 |
| 125 | 售后未收货仅退款 |
| 147 | 分销销售 |
| 148 | 线下零售 |
| 165 | 分销退货 |

## 技能目录

`/Users/liuqingchen/.qoderwork/skills/sales-voucher-reconciliation`

## 数据库配置

使用 `~/.config/db-profiles/` 下的配置文件：

- `erp-mysql.env` — ERP MySQL，psi_sales 查 `fms_cost` 库，voucher 查 `fms_bill` 库

## 脚本位置

`/Users/liuqingchen/.qoderwork/skills/sales-voucher-reconciliation/scripts/reconcile.py`

## 常用执行命令

### 按月核对（全量店铺）

```bash
python /Users/liuqingchen/.qoderwork/skills/sales-voucher-reconciliation/scripts/reconcile.py 2026-04
```

### 按月核对（指定店铺）

```bash
python /Users/liuqingchen/.qoderwork/skills/sales-voucher-reconciliation/scripts/reconcile.py 2026-04 --shop SH028
```

### 输出到文件

```bash
python /Users/liuqingchen/.qoderwork/skills/sales-voucher-reconciliation/scripts/reconcile.py 2026-04 --shop SH028 > result.json
```

## 输出字段说明

### 月度汇总（monthly_summary）

| 字段 | 说明 |
|------|------|
| psi_sales_income_fee | 业务日志收入合计 |
| psi_sales_refund | 业务日志退款合计 |
| psi_net_income | 业务日志净收入 |
| psi_cnt | 业务日志记录数 |
| voucher_income_credit | 凭证收入贷方（6001%） |
| voucher_income_debit | 凭证收入借方 |
| voucher_tax_credit | 凭证销项税贷方（2221.01.01%） |
| voucher_tax_debit | 凭证销项税借方 |
| voucher_book_income | 凭证账面收入（收入贷方+销项税贷方） |
| voucher_cnt | 凭证记录数 |
| diff | 差异金额（psi_net_income - voucher_book_income） |
| diff_pct | 差异率（%） |
| status | MATCH / WARN / MISMATCH |

### 科目明细（by_subject）

按凭证科目编码汇总，展示每个科目的贷方和借方发生额。主要关注科目：

- `6001%` — 主营业务收入
- `2221.01.01%` — 应交增值税-销项税额
- `6401%` — 主营业务成本
- `1405%` — 库存商品
- `1406%` — 发出商品
- `1122%` — 应收账款

### 逐日对比（daily_comparison）

每天的 psi 净收入 vs 凭证账面收入，以及差异金额和差异率。

## 排查差异时的固定顺序

1. 确认凭证是否已生成（某些日期 voucher_cnt = 0 说明尚未生成凭证）
2. 检查凭证生成时点（通常按周批量生成，非每日）
3. 对比科目明细，确认 6001 和 2221.01.01 是否完整
4. 检查是否存在其他收入相关科目（如 6001.01.04 等子科目）
5. 按店铺维度单独核对，定位差异来源店铺
6. 检查 psi_group_type 是否遗漏某个分组
7. 确认 voucher_resource=8 和 account_set=3 的过滤是否正确

## 回复要求

- 返回月度汇总的差异金额、差异率和状态
- 如果差异较大，列出差异最大的日期
- 按科目明细展示主要科目的贷方和借方
- 如果发现凭证未生成日期，明确标注
