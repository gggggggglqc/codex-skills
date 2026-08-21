---
name: data-product-requirement-lifecycle
description: 管理数据产品需求从设计到上线的闭环。适用于生成 PRD、定位需改文档、维护需求状态、关联禅道、准备验收和上线后版本回写。
---

# 数据产品需求闭环 Agent（A6）

先读取 `~/data-warehouse-agent/agents/data-product-requirement-lifecycle-agent.md`、`~/data-warehouse-agent/templates/data-product-change.md`、相关影响分析和产品来源。

状态只允许按“需求设计 → 开发中 → 已上线”推进。评审证据前不得标记开发中；发布和验收证据前不得标记已上线。输出必须列出本次变更内容、需修改的钉钉文档位置、受影响资产、验收标准、计划上线条件与待确认事项。

先在 Git 生成 PRD/变更单草稿。写入禅道或钉钉前，必须取得用户对具体目标和内容的明确授权，并确认连接能力可用。
