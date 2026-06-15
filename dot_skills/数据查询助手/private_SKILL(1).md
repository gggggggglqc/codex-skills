---
name: 数据查询助手
description: 查询 ERP MySQL 和 Doris 数仓数据库，执行凭证审核、出纳推送、费用账单、科目分摊、EP费用编码、跨库比对等查询。当用户要求查数据、核对数据、跑对数、看差异、查凭证、查费用、查推送失败时使用。
---

# 数据查询助手

## 用途

直接连接 ERP MySQL 和 Doris 数仓执行数据查询，回答涉及实际数据的问题。

## 何时使用

用户问到以下类型的问题时使用本 skill：

- 凭证审核了没有 / 有多少未审核凭证
- 付款单/收款单推送失败多少
- CI168 / CI044 / CI046 等科目的金额和差异
- EP001-EP036 费用编码的金额
- 某月费用账单和数仓数据对不上
- 重复凭证检查
- 付款差异单据定位

## Python 环境

**必须使用**: `C:\Users\lqc\AppData\Local\Python\bin\python.exe`
**禁止使用**: `python` 或 `python3`（会调用 Windows Store 桩程序，返回 exit code 49）

## 脚本位置

所有脚本在 `scripts/` 子目录下，执行时先确认脚本路径。

## 脚本用法速查

### 1. ERP MySQL 查询 (query_erp.py)

```bash
# 凭证审核状态
python scripts/query_erp.py voucher_status 2026-05

# 付款单推送状态
python scripts/query_erp.py payment_push 2026-05

# 收款单推送状态
python scripts/query_erp.py receipt_push 2026-05

# 费用账单汇总（全部科目）
python scripts/query_erp.py expense_summary 2026-05

# 费用账单汇总（单科目）
python scripts/query_erp.py expense_summary 2026-05 CI168

# 重复凭证检查（单日）
python scripts/query_erp.py duplicate_check 2026-05-15

# 付款单差异明细（按来源）
python scripts/query_erp.py payment_detail 2026-05 8
```

### 2. Doris 数仓查询 (query_doris.py)

```bash
# 科目费用分摊汇总（全部科目）
python scripts/query_doris.py cost_summary 2026-05

# 科目费用分摊汇总（单科目）
python scripts/query_doris.py cost_summary 2026-05 CI168

# EP 费用编码汇总
python scripts/query_doris.py ep_summary 2026-05

# EP 费用编码汇总（单编码）
python scripts/query_doris.py ep_summary 2026-05 EP004

# 科目费用逐日明细
python scripts/query_doris.py cost_daily 2026-05 CI168

# 分摊失败统计
python scripts/query_doris.py cost_failure 2026-05
```

### 3. 跨库比对 (query_compare.py)

```bash
# 全量比对（MySQL 费用账单 vs Doris 科目分摊）
python scripts/query_compare.py full_compare 2026-05

# 单科目逐日差异
python scripts/query_compare.py code_diff 2026-05 CI168
```

## 数据库连接信息

### ERP MySQL（只读）

| 参数 | 值 |
|---|---|
| Host | rr-2zeh95evp4y3t94fkmo.mysql.rds.aliyuncs.com |
| Port | 3306 |
| User | oms_query |
| Password | %zVtq^h$30fQIDav |
| 数据库 | fms_bill（凭证/出纳）、fms_cost（费用） |

### Doris 数仓

| 参数 | 值 |
|---|---|
| Host | cmccnet.jiabs.com |
| Port | 19130 |
| User | db_devops |
| Password | mVk3ydQVwN |
| 数据库 | dp_dws |

> **注意**: 内网地址 192.168.4.99:19030 不可用（无 MySQL 握手），必须用外网地址。

## 常用科目编码速查

| 编码 | 名称 | 关注点 |
|---|---|---|
| CI165 | 结算入账 | 重复检查重点 |
| CI168 | 销售回款 | 跨库比对差异最大，需关注 |
| CI044 | 售后返款 | 正负号可能与 Doris 相反 |
| CI046 | 平台佣金 | 常规比对 |
| CI170 | 提现 | — |
| CI184 | 卖家运费 | 检查上传人 |
| CI265 | 不取数 | 不参与分摊 |

## 自定义查询

如果脚本不满足需求，可以直接写 Python 代码查询。关键注意事项：

1. **大表必须逐日查询**：expense_detail（~1亿行）和 finance_cost_sbjct（~10亿行）直接按月查会超时，必须按天循环
2. **费用明细字段**：MySQL expense_detail 用 `income_cost`（收入）和 `expend_cost`（支出），不是 `amount`
3. **account_no 不是账套**：expense_detail.account_no 是邮箱/店铺ID，不是账套编号，不要过滤 `account_no = '4'`
4. **Doris 分摊金额字段**：finance_cost_sbjct 用 `share`（分摊金额）和 `no_tax_amount`（不含税金额）
5. **EP 费用编码**：net_profit_check_report_v2 用 `expense_code` 和 `expense_amount`

## 回答规范

1. 运行脚本后，将结果整理为简洁的中文总结回复
2. 金额超过 1 万的用"万元"表示，保留两位小数
3. 差异率超过 1% 的要特别提醒
4. 如果查询失败，告知用户具体错误信息并建议排查方向
