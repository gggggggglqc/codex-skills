---
name: factory-finance-rules-1-7
description: 工厂财务 1-7 数据核对 skill。用于按月份核对完工入库、报工入库、实际成本还原、生产成本管理、委外加工金额、领料出库和倒冲领料数据；适用于用户要求“工厂财务核对”“1-7规则核对”“完工入库和成本核对”“委外加工金额核对”“领料出库和倒冲领料核对”“生成结果并发送机器人”时。内置数据库脚本、规则说明、桌面结果输出和钉钉/企业微信/飞书机器人通知能力。
---

# 工厂财务1-7数据核对

使用本 skill 按固定的 1-7 规则执行工厂财务数据核对，并生成 CSV 结果和汇总消息。

## 核心流程

1. 先确认核对月份，通常传入 `--start-date`、`--end-date`、`--calc-month`。
2. 读取 `references/check-rules.md` 确认规则口径。
3. 运行单条规则脚本或总入口脚本。
4. 结果文件默认生成到桌面，文件名默认使用中文规则名。
5. 如果配置了机器人，结果文件生成后调用机器人发送汇总。
6. 有差异不等于执行失败；脚本执行失败才应中断排查。

## 一键执行 1-7

使用总入口：

```powershell
python C:\Users\lqc\.codex\skills\factory-finance-rules-1-7\scripts\run_rules_1_7_and_notify.py --start-date 2026-03-01 --end-date 2026-03-31 --calc-month 2026-03-01 --title "工厂账务核对 1-7 结果"
```

总入口会依次执行：

- `scripts/check_rule1_db.py`
- `scripts/check_rule2_db.py`
- `scripts/check_rule3_db.py`
- `scripts/check_rule4_db.py`
- `scripts/check_rule5_db.py`
- `scripts/check_rule6_db.py`
- `scripts/check_rule7_db.py`

然后生成汇总文件并调用：

- `scripts/send_robot_message.py`

## 单条规则入口

需要单独排查某条规则时，直接运行对应脚本。

- 规则 1：`check_rule1_db.py`
- 规则 2：`check_rule2_db.py`
- 规则 3：`check_rule3_db.py`
- 规则 4：`check_rule4_db.py`
- 规则 5：`check_rule5_db.py`
- 规则 6：`check_rule6_db.py`
- 规则 7：`check_rule7_db.py`

常用参数：

- `--start-date`：业务起始日期
- `--end-date`：业务结束日期
- `--calc-month`：成本月份，规则 2-6 使用
- `--env-file`：数据库和机器人配置文件
- `--output`：结果文件路径

## 默认规则

详细表、字段、过滤条件和单位口径见 `references/check-rules.md`。

1. 完工入库单数量 = 报工入库数量
2. 完工入库单数量 = 实际成本还原的完工入库数量
3. 完工入库单数量 = 生产成本管理的生产入库数量
4. 完工入库单成本单价 * 数量 = 实际成本还原的生产成本总金额
5. 完工入库单成本单价 * 数量 = 生产成本管理的实际生产入库总金额
6. 实际成本还原的实际委外加工总费用 = 财务-委外加工明细金额
7. 领料出库单数量 = 生产收发-倒冲领料单数量

## 关键口径提醒

- 规则 1：报工数量按关联完工入库明细调整，不直接取原始 `report_work_num`。
- 规则 2 和规则 3：成本侧均取 `erp_cost.produce_cost.produce_num`。
- 规则 4 和规则 5：金额侧取 `erp_cost.produce_cost.actual_produce_amount`，不设容差，差异照常展示。
- 规则 6：这是金额核对；实际成本还原侧取 `produce_cost_detail.outside_cost`，并限定 `parent_id='root'`；财务侧取 `outsourcing_not_tax_freight_cost`，委外加工类型取外部往来 `outsourcing_order_type=2`。
- 规则 7：必须按基本单位核对；IOM 取 `actual_num`，MES 倒冲领料取 `base_unit_apply_num`。

## 机器人配置

机器人配置放在 `.env` 中。默认读取：

```powershell
D:\codex\codex-file-organizer\.env
```

支持两种发送方式。

第一种：复用现有命令。

```env
RECONCILE_NOTIFY_COMMAND=python D:\path\to\send_robot.py --title "{title}" --content-file "{content_file}"
```

第二种：使用 webhook。

```env
RECONCILE_NOTIFY_TYPE=dingtalk
RECONCILE_NOTIFY_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
RECONCILE_NOTIFY_SECRET=SECxxx
RECONCILE_NOTIFY_KEYWORD=数据核对
```

`RECONCILE_NOTIFY_TYPE` 支持：

- `dingtalk`
- `wecom`
- `feishu`

钉钉加签机器人必须配置 `RECONCILE_NOTIFY_SECRET`。如果有关键字校验，配置 `RECONCILE_NOTIFY_KEYWORD`，脚本会自动把关键字放入消息正文。

## 输出文件命名

默认脚本输出类似：

- `规则1-完工入库单数量等于报工入库数量-2026_03.csv`
- `规则2-完工入库单数量等于实际成本还原的完工入库数量-2026_03.csv`
- `规则3-完工入库单数量等于生产成本管理的生产入库数量-2026_03.csv`
- `规则4-完工入库单成本单价乘数量等于实际成本还原的生产成本总金额-2026_03.csv`
- `规则5-完工入库单成本单价乘数量等于生产成本管理的实际生产入库总金额-2026_03.csv`
- `规则6-实际成本还原的实际委外加工总费用等于财务委外加工明细金额-2026_03.csv`
- `规则7-领料出库单数量等于生产收发倒冲领料单数量-2026_03.csv`
- `规则1到7汇总结果-2026_03.md`

如需输出到非桌面目录，使用 `--output-dir` 指定。

## 差异排查

优先按最小粒度下钻：

- 物料编码
- 单据号
- 明细行号
- 账务时间
- 成本月份
- 单位口径

常见判断：

- 数量相等、金额差异很小时，优先看成本单价精度和系统金额字段是否由更细颗粒成本还原得出。
- 规则 4、规则 5 中，`cost_price * quantity` 与 `actual_produce_amount` 可能出现小额差异，原因通常是金额来源和展示单价精度不同。
- 规则 7 差异优先检查是否误用了生产单位字段 `pro_unit_real_num`。

## 资源说明

- 详细规则：`references/check-rules.md`
- CSV 配置示例：`references/config-example.json`
- 规则 1 旧配置参考：`references/rule-1-finished-vs-reporting.json`
- 数据库核对脚本：`scripts/check_rule*_db.py`
- 汇总和通知：`scripts/run_rules_1_7_and_notify.py`
- 机器人发送：`scripts/send_robot_message.py`
