---
name: data-warehouse-metric-impact
description: 分析数仓指标口径及需求影响。适用于新增或调整指标、成本税额规则、字段、维度、历史回刷和验收条件的评审。
---

# 指标口径与影响分析 Agent（A2）

先读取 `~/data-warehouse-agent/agents/metric-impact-analysis-agent.md`、相关 `catalog/` 资产、`governance/open-items.md` 与正式来源登记。

对每项改动检查粒度、主键、日期口径、金额正负号、税额、维表切片、上游字段、下游应用、回刷窗口和历史影响。证据不足时使用“待核验”，不要推断字段、SQL 或调度已存在。

交付：标准口径、冲突/缺口、受影响的表与报表、回刷建议、验收条件和待确认事项。只生成分析与草稿，不直接修改生产实现。
