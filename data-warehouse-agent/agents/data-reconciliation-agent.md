# 数据核对 Agent（MVP）

## 1. 产品定位

核对已确认口径下的数据是否完整、一致、按预期回刷，并在异常时向下穿透给出证据链。MVP 采用**结果数据核对模式**：仅依赖只读数据查询和已确认文档，不要求接入数仓代码或调度记录。MVP 合并“数据质量与调度运营”和“应用诊断”两类能力；后续规模化后可拆分。

## 2. 首批支持场景

| 场景 | 核对目标 | 当前数据产品 |
|---|---|---|
| 发货与净利 | 发货 V1、净利 V2、经营净利的日期/金额/数量勾稽 | `doris_app_report_delivery_v1`、`doris_app_net_profit_check_report_v2`、`doris_app_finance_profit_business` |
| 回刷与分区 | 窗口是否完整覆盖、重复写入或遗漏写入 | 31/60/90/120/365 天滚动表及月度净利回刷 |
| 应用异常 | 某天、店铺、SKU、订单或指标的缺失/金额异常 | 老板报表、发货、净利应用 |
| 规则核对 | 仅对“已确认”资产验证字段、金额、税额、成本和维度逻辑 | `catalog/` 中已确认规则 |

## 3. 输入与输出契约

### 输入

```yaml
request_type: daily_check | reconciliation | diagnose
scope:
  asset_ids: []
  date_range: 2026-08-18..2026-08-18
  dimensions:
    shop_code: []
    owner_code: []
    goods_code: []
    order_id: []
check_level: partition | aggregate | detail | lineage
```

### 输出

```yaml
check_id: REC-YYYYMMDD-001
status: pass | warning | failed | blocked
scope: {}
rules_executed: []
findings:
  - severity: P0 | P1 | P2 | P3
    type: task_failure | late_partition | duplicate | reconciliation_gap | rule_gap | lineage_gap
    evidence: []
    impact: []
    root_cause: confirmed | suspected | blocked
    suggested_action: ''
open_items: []
```

## 4. 核对方法

### 4.1 先判可核对性

仅执行确认状态为“已确认”的规则。草稿或待数仓确认资产只输出“缺少核对依据”，不产生确定性异常。

### 4.2 四层核对

1. **运行层**：任务是否成功、应有分区是否到达、回刷窗口是否覆盖。
2. **结构层**：Key 是否重复、日期/必填维度是否为空、数据量是否异常波动。
3. **金额层**：同口径的应用表、DWS、DWD 与 ODS 聚合是否可勾稽。
4. **明细/血缘层**：按订单、商品、店铺、货主向下穿透到应用表、DWS、DWD、ODS、维表和必要的业务事实表。

### 4.3 根因标识

| 标识 | 含义 |
|---|---|
| `confirmed` | 有 SQL/运行记录/代码证据可证实 |
| `suspected` | 已缩小范围但未取得最终证据 |
| `blocked` | 缺数据源、权限、DDL、ETL 仓或调度记录 |

## 5. 运行边界

- 默认只读查询，禁止修复生产数据或重跑任务。
- 任何修复建议都要附复验 SQL/条件。
- 不具备代码或调度记录时，Agent 只能确认“结果异常在哪一层首次出现”，不得断言任务失败、SQL 错误或调度未执行。
- 代码与调度记录是后续增强证据，不是 MVP 运行前提。
- 费用、成本、手机号等敏感明细采用最小权限和脱敏展示。

## 6. 首批核对规则清单

| 规则 ID | 规则 | 状态 |
|---|---|---|
| `check.app.v1.partition` | 发货 V1 近 90 日覆盖窗口的日期产出完整性 | 可用结果数据执行 |
| `check.net_profit.v2.partition` | V2 日更与月末/3/8/10 回刷应产出日期的结果完整性 | 可用结果数据执行 |
| `check.net_profit.v1_v2` | V1 与 V2 的确认口径字段按日期/维度勾稽 | 待补确认的可勾稽字段集 |
| `check.other_expense.pre_delete` | 其他费用上传是否先清理对应月份再写入 | 待接入调用/运行日志 |
| `check.dws.key_duplicate` | 各 Index 的已登记唯一键重复检查 | 可按已确认 DDL逐表启用 |

发货 V1 → 净利 V2 → 经营净利的首批字段级结果映射见 `agents/reconciliation-mappings/delivery-v1-net-profit-chain.md`。

## 7. MVP 验收

1. 可按表、日期、店铺、货主、商品或订单发起只读核对。
2. 每一异常都有规则 ID、证据、影响范围与根因状态。
3. 可说明“无异常”“无法核对”“已发现异常”三种不同结论。
4. 可从应用表向下定位到已接入的 DWS/DWD/ODS/维表/业务事实表，明确结果异常首次出现的层级。
