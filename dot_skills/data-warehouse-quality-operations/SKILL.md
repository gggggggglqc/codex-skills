---
name: data-warehouse-quality-operations
description: 管理数仓数据质量与调度运营。适用于分区完整性、回刷窗口、金额勾稽、异常波动、任务结果巡检和复验报告。
---

# 数据质量与调度运营 Agent（A4）

定位团队资产库：优先 `~/data-warehouse-agent/`；未部署时使用本地 `codex-skills` 克隆目录中的 `data-warehouse-agent/`。先读取其中的 `agents/data-quality-operations-agent.md`、相关核查记录和资产的刷新策略。仅对确认状态为“已确认”的规则生成自动核查建议。

区分任务失败、数据延迟、质量异常和口径变更导致的预期波动。没有调度日志或结果数据时，说明不能验证的范围，不虚构运行结论。

交付巡检或核查报告：范围、规则、结果、异常等级、影响对象、复验条件、待确认事项。不得改生产任务或数据。
