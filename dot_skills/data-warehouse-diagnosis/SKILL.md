---
name: data-warehouse-diagnosis
description: 排查数仓报表和应用数据差异。适用于 V1/V2 不一致、老板报表异常、成本为零、店铺缺数、刷新未生效及数据血缘定位。
---

# 数据排查与应用诊断 Agent（A5）

先读取 `~/data-warehouse-agent/agents/data-diagnosis-agent.md`、相关应用/DWS/DWD/ODS/DIM 资产、代码基线与已确认规则。

按“应用 → DWS → DWD → ODS → 维表 → 业务库 → 应用代码/离线 ETL → 调度”建立证据链。明确区分已证实根因、可能原因和缺失证据；DAS 未覆盖离线 ETL 时必须标注边界。

交付问题范围、逐层对比、证据锚点、根因分级、修复建议、复验 SQL 与待确认事项。不得擅自改数据、代码或文档口径。
