---
name: srm-ops-product-ordering-report
description: SRM srm-ops 商品版运营订货报表全流程知识技能。用于回答或整理商品运营订货报表、商品订货策略、货品订货策略、运营预估日销、再订货点、采购建议、采购申请、采购前调拨、内部/外部供应商差异、库存周转指标、业务培训 PPT 口径等问题。明确排除物料版订货规则，除非用户显式要求物料版本。
version: 1.0.0
---

# SRM 商品运营订货报表

## Core Rule

Default to the 商品版 rules. Do not answer with 物料采购 / 物料运营订货 logic unless the user explicitly asks for it.

Use business language first. Code names, table names, and method names are supporting evidence, not the main answer, unless the user asks for source details.

## Source Priority

1. Use local source code first: `/Users/liuqingchen/工作/代码/srm-ops`.
2. If settlement, cost, or return-price behavior is involved, also inspect `/Users/liuqingchen/工作/代码/fms-cost` and `/Users/liuqingchen/工作/代码/erp-cost` when available.
3. If a previously created PPT, image, or sheet is the artifact being edited, inspect that file directly before changing it.

## Workflow

1. Classify the user request:
   - Business explanation, training PPT, field formula, strategy effect, trigger timing, transfer logic, status/permission, or source-code investigation.
2. Load only the needed reference:
   - For full process, formulas, strategy effects, and PPT wording, read `references/business-flow.md`.
   - For code tracing, entry points, and known source paths, read `references/code-map.md`.
3. Verify against code when the user asks "是否", "有没有限制", "影响什么", "公式是什么", or provides a specific order/report id.
4. Answer in the user's expected style:
   - For business users: explain in terms of inventory, demand, safety stock, arrival cycle, transfer, and purchase decision.
   - For product/QA: include status, trigger point, condition, result, and edge cases.
   - For engineers: include source file paths and method names after the conclusion.

## Output Standards

- Start with the conclusion.
- Separate "participates in calculation" from "display-only / filter-only" fields.
- State trigger timing: scheduled report calculation, manual report execution, report-to-apply creation, submit-before-transfer calculation, audit, and convert-to-order when relevant.
- For strategy explanations, cover both 商品订货策略 and 货品订货策略, including how thresholds and values affect the final purchase suggestion.
- For PPT output, avoid code-field translation. Use training-friendly wording and diagrams:
  - Why we calculate.
  - What data participates.
  - How strategy changes the result.
  - What happens before creating采购申请.
  - What happens after提交/审核/转单.
- Mention uncertainty explicitly when a dependent service is not in the local workspace.

## Guardrails

- Do not mix 商品版 and 物料版 transfer logic. 商品版采购前调拨 is same-warehouse, cross-owner transfer; material logic can be cross-warehouse.
- Do not call report-created purchase applications "reversible to report row" unless verified. The report id is not persisted on `sub_purchase_apply`; report rows may be cleaned after 30 days.
- Do not say view permission is status-restricted for purchase applications. Search can filter by status, but detail/list viewing is not inherently blocked by status in `srm-ops`.
- Do not over-explain Java fields in training material. Convert them into business terms.

---

## 版本管理（遵循数仓文档管理规范v1.0）

> 来源：[数仓文档管理规范v1.0](https://alidocs.dingtalk.com/i/nodes/QOG9lyrgJP3PAm3kuvy0z6E3VzN67Mw4)

### 版本说明

| 版本号 | 版本内容 | 上线状态 | 上线时间 | 维护人 | 备注 |
|--------|----------|----------|----------|--------|------|
| V1.0.0 | 初始版本，录入核心规则与核对流程 | 已上线 | 2026-07-06 | QoderWork | 按数仓文档管理规范v1.0补充版本管理章节 |

### 版本更新规则

1. **版本号**：与禅道版本号保持一致（如 V1.0.0、V1.1.0、V2.0.0）
2. **Sheet 命名**：指标说明按"版本号 + 简述"格式（如 `V1.1.0 口径调整`）
3. **变更标识**：本期新增或修改内容使用**红色字体**标识；删除内容使用~~画线~~处理
4. **历史版本**：只隐藏不删除，便于追溯
5. **额外说明**：绑定版本号，格式为 `【V1.x.0 额外说明】`
6. **更新流程**：复制上一版本 → 修改本期内容（标红）→ 更新版本说明 → 检查额外说明 → 隐藏历史版本 → 上线后更新状态
