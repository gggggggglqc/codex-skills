# 数仓 Agent 团队资产库

本目录保存团队可共享、可版本追溯的数仓产品资产；钉钉文档是原始需求与协作阅读入口，Git 保存结构化规则、变更记录与 Agent 协作契约。

## 目录

- `skills/`：数仓 Agent 的调用入口说明。实际可安装技能仍由仓库根目录 `dot_skills/` 管理。
- `agents/`：A1–A6 角色说明与输入输出契约。
- `catalog/`：ODS、DWD、DWS、DIM、应用层表资产与字段说明。
- `governance/`：版本规则、变更单、血缘、待确认事项与核对记录。
- `sources/`：来源登记、钉钉原文链接、DDL 与派生产品说明。
- `templates/`：需求分析、研发设计、核对报告与版本变更模板。

## 使用约定

1. 原始 Excel、钉钉文档不整份复制到 Git；在 `sources/register.yaml` 登记正式链接和 Sheet/单元格定位。
2. 每次需求形成一份变更单，状态依次为“需求设计 → 开发中 → 已上线”。
3. 文档版本仅标红本版本变更；删除项先以红色删除线保留，下一版本再移除。
4. 任何规则、字段或结论都应能回溯到来源、版本和变更单。

团队克隆后从 [TEAM-ACCESS.md](TEAM-ACCESS.md) 开始；当前来源与资产范围见 `sources/register.yaml` 和 `governance/knowledge-base-manifest.md`。
