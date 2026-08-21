# 数仓 Agent 技能入口

本仓库的可安装技能由根目录 `dot_skills/` 维护；本目录记录数仓 Agent 的技能编排说明，避免复制同一份技能实现。

| Skill | 对应 Agent | 用途 |
| --- | --- | --- |
| `data-warehouse-collaboration` | 总入口 | 识别任务并路由至专用 Agent |
| `data-warehouse-document-versioning` | A1 | 文档、版本与来源登记 |
| `data-warehouse-metric-impact` | A2 | 指标口径和影响分析 |
| `data-warehouse-engineering-design` | A3 | 数仓研发设计 |
| `data-warehouse-quality-operations` | A4 | 质量、调度与回刷核查 |
| `data-warehouse-diagnosis` | A5 | 数据异常与血缘诊断 |
| `data-product-requirement-lifecycle` | A6 | PRD、文档状态与上线闭环 |

团队安装与调用方式见 [INSTALL.md](../INSTALL.md)。
