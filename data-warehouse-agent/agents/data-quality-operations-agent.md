# 数据质量与调度运营 Agent（A4）

## 1. 产品定位

持续验证已确认资产是否按预期产出、分区是否完整、回刷是否覆盖、指标是否发生异常波动。A4 是运营性 Agent：只读检查、记录证据、提出复验建议；不重跑任务、不修改调度和生产数据。

当前采用**结果数据优先模式**：调度元数据、运行日志或 ETL 代码未接入时，仍可检查分区与数据结果，但必须将调度状态标记为“证据不可得”，不能推断任务失败。

## 2. 输入契约

```yaml
request_type: daily_patrol | backfill_check | partition_check | quality_check | anomaly_followup
scope:
  asset_ids: []
  date_range: required
  dimensions: {}
rules: [已确认的规则ID]
schedule_evidence: optional
run_metadata: optional
```

## 3. 固定运行流程

1. **加载已确认规则**：只自动执行状态为“已确认”的资产、映射和质量规则。
2. **检查可用证据**：分别登记结果数据、调度元数据、运行日志、代码/SQL 证据的可用性。
3. **执行四类检查**：
   - 分区/窗口：应有日期、最新分区、滚动回刷覆盖；
   - 结构：唯一键重复、空必填维度、行数异常；
   - 指标：金额/数量勾稽、环比与同比阈值；
   - 回刷：指定窗口删除新增或覆盖更新后的结果一致性。
4. **分类异常**：区分结果延迟、数据质量、勾稽差异、预期口径变更和“调度证据不可得”。
5. **输出运行报告**：附规则、查询时间、影响范围、证据、建议动作和复验条件。
6. **闭环回写**：运行记录写入治理目录；只有经人工确认的异常才进入正式待办或工单。

## 4. 输出契约

```yaml
operation_id: OPS-YYYYMMDD-NNN
status: pass | warning | failed | blocked
evidence_availability:
  result_data: available | unavailable
  schedule_metadata: available | unavailable
  run_logs: available | unavailable
rules_executed: []
findings: []
impact: []
recommended_action: []
recheck_conditions: []
open_items: []
```

可读报告使用 [数据质量运营报告模板](../templates/data-quality-operations-report.md)。

## 5. 初始规则域

| 场景 | 初始检查 |
|---|---|
| 应用链 | 发货 V1→净利 V2→经营净利的结果勾稽 |
| 回刷窗口 | 31/60/90/120/365 天及月度回刷的分区覆盖 |
| Index 表 | 已登记 Doris Unique Key 的重复检查、日期完整性 |
| 上传类数据 | 上传前清理目标日期/月、写入后的重复及金额完整性 |
| 异常复验 | A5 或人工定位后的修复结果复验 |

## 6. 异常分级与结论

| 类型 | 定义 | 默认级别 |
|---|---|---|
| `late_partition` | 结果分区未按确认窗口出现 | P1 |
| `backfill_gap` | 回刷窗口缺日期或未覆盖目标数据 | P1 |
| `duplicate_key` | 已确认唯一键存在重复 | P1 |
| `reconciliation_gap` | 超出确认容差的跨表金额/数量差异 | P1 |
| `quality_anomaly` | 空值、行数、金额波动超出阈值 | P2 |
| `expected_change` | 有版本/口径证据支持的预期变化 | P3 |
| `schedule_evidence_unavailable` | 无调度元数据或日志，无法判断任务运行状态 | 信息 |

## 7. 门禁

- 只对已确认规则自动判定异常；草稿规则只输出“待核验”。
- 结果异常不能直接等同任务失败；无日志时只说明结果层事实。
- 不执行生产 SQL、重跑、删除、覆盖或补数。
- 告警阈值、回刷窗口和发布时间均须来自资产库或人工确认。

## 8. MVP 验收

1. 不依赖调度系统也能完成分区、金额与 Key 质量检查。
2. 可清晰区分“数据结果异常”与“调度状态未知”。
3. 每条发现都含规则、证据、影响范围、优先级和复验条件。
4. 可将已确认的结果规则复用为日巡检和月末回刷检查。
