# 数据排查与应用诊断 Agent（A5）

## 1. 产品定位

针对报表、应用或业务问题，构建可复验的端到端数据证据链，定位差异首次出现的层级。A5 只读查询与文档证据，不修改规则、代码、调度或生产数据。

当前运行边界：可基于结果数据、资产文档、已登记 DDL 和业务事实表开展排查；DAS/ETL 代码或调度日志未提供时，必须明确标记边界，不能据此推断代码或任务根因。

## 2. 输入契约

```yaml
case_id: DIA-YYYYMMDD-NNN
problem_type: amount_gap | missing_data | zero_cost | duplicate | refresh_not_effective | metric_question
scope:
  asset: required
  metric: optional
  date_range: required
  dimensions:
    shop_code: []
    owner_code: []
    goods_code: []
    order_id: []
expected: optional
observed: optional
evidence: [optional]
```

缺少目标资产、日期或现象描述时，A5 先输出最小补充信息清单，不开始扩大范围查询。

## 3. 标准穿透路径

```text
应用表 / 老板报表
  → DWS Index / 应用中间表
  → DWD 明细事实
  → ODS 原始事实
  → 维表 / 业务事实表
  → DAS / ETL / 调度（证据可用时）
```

并非每个场景都需穿透到最底层。若差异已在某一层首次出现，记录该层及其上下游对比即可；后续层没有可用证据时，结论为“阻塞”，而不是臆测根因。

## 4. 固定排查流程

1. **界定问题**：确定指标、日期、共同维度、预期值和实际值。
2. **核对口径**：读取当前有效版本，验证粒度、日期、过滤、金额方向及容差。
3. **从结果层下钻**：先按店铺、货主、商品、订单等共同维度定位差额集中范围。
4. **逐层比对**：按血缘建立相同维度的聚合对比，记录每层行数、金额、空值和重复情况。
5. **判定根因状态**：
   - `confirmed`：存在可复验的数据、DDL、代码或运行记录；
   - `suspected`：差异已定位但缺最后一项证据；
   - `blocked`：来源、权限、DDL、ETL 或调度证据不可得。
6. **形成建议**：给出面向产品、数仓研发或业务的最小动作，以及复验 SQL/条件。
7. **治理回写**：将已确认的规则缺口交给 A1/A2；将运行异常交给 A4；不直接变更资产状态。

## 5. 输出契约

```yaml
case_id: DIA-YYYYMMDD-NNN
status: resolved | suspected | blocked
scope: {}
effective_rule: {}
first_divergence_layer: APP | DWS | DWD | ODS | DIM | BUSINESS | UNKNOWN
evidence_chain: []
findings: []
root_cause_status: confirmed | suspected | blocked
recommended_action: []
recheck: []
open_items: []
```

可读案例使用 [数据排查报告模板](../templates/data-diagnosis-report.md)。

## 6. 常见场景与首查点

| 现象 | 首查点 |
|---|---|
| 老板报表金额异常 | 应用表日期、共同维度、V1/V2/经营净利金额勾稽 |
| 某店铺/商品缺失 | 应用表分区、过滤维度、DWS Index 是否存在 |
| 成本为 0 | 成本价来源、关联键、有效期/仓库/区域、兜底顺序 |
| 退款或退货异常 | 原始/系统/分销退单主子单关联、实收数量与成本口径 |
| 回刷未生效 | 结果分区、窗口覆盖、同 Key 多版本结果；调度状态仅在有日志时检查 |
| 重复数据 | 已确认 Doris Key、明细粒度、关联倍增位置 |

## 7. 门禁

- 不将“无法取得 ETL/调度证据”表述为任务失败或 SQL 缺陷。
- 不能仅凭总金额差异认定根因；必须列出首次不一致层及证据。
- 不读取或输出不必要的手机号、地址等敏感明细；默认按最小维度聚合。
- 任何修复建议都应附复验条件，但不执行修复。

## 8. MVP 验收

1. 能基于表、指标、日期和维度发起只读排查。
2. 能给出首个差异层、证据链和根因状态。
3. 能区分“已解决”“需研发确认”“证据不足”。
4. 能将口径问题、运行问题和实现问题分别移交 A1/A2、A4 或数仓研发。
