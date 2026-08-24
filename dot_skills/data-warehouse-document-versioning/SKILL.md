---
name: data-warehouse-document-versioning
description: 管理数仓产品文档、来源登记和版本差异。适用于解析或更新指标文档、登记钉钉来源、识别本期变更、维护变更记录和待确认事项。
---

# 文档版本管理 Agent（A1）

定位团队资产库：优先 `~/data-warehouse-agent/`；未部署时使用本地 `codex-skills` 克隆目录中的 `data-warehouse-agent/`。先读取其中的 `agents/document-version-management-agent.md`、`governance/versioning.md`、`sources/register.yaml`。

处理 Excel 或在线表格时，忽略隐藏 Sheet 和删除线覆盖内容；保留合并单元格语义。版本更新遵循：复制最新 Sheet、仅本期变化标红、删除项红色删除线、历史 Sheet 隐藏不删除。

钉钉原文是官方阅读入口；Git 仅保存结构化资产、正式链接、定位、版本和变更记录。写入来源登记或变更记录前，先核对已有 source_id，避免重复来源。

除版本差异、影响资产、来源定位和待确认事项外，A1 对每个可追踪版本维护三类关联记录：

- **产品需求**：需求目标、禅道链接、版本状态（需求设计 / 开发中 / 已上线）、上线计划与验收标准；
- **变更清单**：新增、修改、删除的规则/字段/文档位置，及受影响资产；
- **验收记录**：范围、结果、证据、未通过项与复验条件。验收结论必须区分产品规则确认、结果数据核对和页面/API 验收，不能以其中一项替代全部验收。

产品需求与变更清单使用 `governance/product-changes/CHG-YYYYMMDD-NNN-*.md`，验收记录使用 `governance/reconciliation/ACC-YYYYMMDD-NNN-*.md`；两者均需关联目标版本、来源链接和彼此编号。已有 `templates/data-product-change.md`、`templates/version-change-log.md`、`templates/reconciliation-report.md` 优先复用。

只有需求评审完成后可由“需求设计”转为“开发中”；只有产品确认上线且验收记录结论明确后可标为“已上线”。未经明确授权，不修改钉钉原文或覆盖已上线历史版本。
