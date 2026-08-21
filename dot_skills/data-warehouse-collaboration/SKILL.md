---
name: data-warehouse-collaboration
description: 数仓与数据应用团队的总协作入口。用于将需求、口径、研发设计、质量核查、数据排查和版本上线路由至正确的专用 Agent，并要求所有结论可追溯。
---

# 数仓 Agent 协作入口

定位团队资产库：优先 `~/data-warehouse-agent/`；未部署时使用本地 `codex-skills` 克隆目录中的 `data-warehouse-agent/`。先读取其 `agents/agent-contracts.md` 和 `governance/open-items.md`。资产库不存在时，说明缺失条件，不凭记忆补全。

按请求路由：

- 文档、版本、来源、Sheet 变更 → `data-warehouse-document-versioning`。
- 指标公式、影响范围、验收口径 → `data-warehouse-metric-impact`。
- 分层、DDL、SQL 骨架、刷新策略 → `data-warehouse-engineering-design`。
- 日巡检、回刷、分区、勾稽 → `data-warehouse-quality-operations`。
- 报表差异、数据缺失、成本异常、血缘定位 → `data-warehouse-diagnosis`。
- PRD、禅道、文档状态、上线回写 → `data-product-requirement-lifecycle`。

所有输出至少说明：资产 ID、适用版本、确认状态、来源证据。存在空缺时单列“待确认事项”；没有则明确写“无”。不得发布任务、修改生产数据或把未确认规则当作结论。
