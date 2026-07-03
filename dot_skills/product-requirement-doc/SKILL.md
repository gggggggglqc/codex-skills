---
name: product-requirement-doc
description: Generate concise Chinese product requirement documents from code, requirement notes, screenshots, prototypes, or investigation findings. Use when the user asks to do requirement research, summarize code changes into product requirements, output Word PRD/docx, draft ZenTao stories, create ZenTao requirements after confirmation, or follow the user's fixed format for 修改功能点, 历史数据处理, 产品设计, 前后端关注点, 测试关注点, 日志, 权限, 风险.
---

# Product Requirement Doc

Use this skill to turn messy inputs into a concise product requirement document and, after user confirmation, a ZenTao requirement.

## Core Rules

1. Investigate before drafting. Read supplied code, notes, screenshots, prototypes, or links first. Mark unknowns as `待确认`; do not invent business rules.
2. Produce a confirmation draft before any write operation. Do not create or update ZenTao until the user explicitly confirms.
3. Keep the requirement concise and implementation-oriented. Prefer clear rules, scope, field changes, edge cases, and acceptance points over long background prose.
4. Put the actual requirement content only in `3.产品设计：` when drafting a ZenTao requirement.
5. Separate frontend and backend impact. Prefix the ZenTao title with `【前端】`, `【后端】`, or `【前端+后端】`.
6. The title must briefly list each functional change point, separated by `；`.
7. When creating or updating ZenTao, preserve formatting by submitting the requirement body as HTML, not plain Markdown or plain text. Use headings for the fixed sections and ordered lists for numbered requirement items.

## Workflow

1. Collect inputs:
   - Code path, branch, commit, interface, page, SQL, or class names.
   - Requirement notes and desired behavior.
   - ZenTao product info: `productID`, or product name to look up.
   - Priority details if available: affected users, frequency, operation cost, urgency, value, latest launch time.
2. Inspect evidence:
   - For code, read relevant files and infer only what the code supports.
   - For unclear scope, ask focused questions or mark `待确认`.
3. Draft the requirement for user confirmation:
   - Provide the ZenTao title.
   - Provide the ZenTao body using the fixed template.
   - Optionally generate a Word `.docx` when requested.
4. After confirmation:
   - If the user asks for ZenTao creation, use `zentao-api`.
   - Create a Story unless the user specifies Epic or Requirement.
   - Pass `productID`, `title`, `grade`, `pri`, and HTML-formatted `spec`.

## ZenTao Formatting Rule

When publishing to ZenTao, convert the fixed template to HTML before submission so the page keeps readable structure:

- Top-level sections `1.需求背景：` through `10.潜在风险` use `<h3>...</h3>`.
- `一.修改功能点` and each `（n）修改功能点` use `<h4>...</h4>`.
- Numbered items under each function point use `<ol><li>...</li></ol>`.
- Blank non-product-design sections may be submitted as empty headings, but do not fill them with `无` or `待确认` unless the user asks.
- Do not submit Markdown markers such as `###`, `-`, or raw line breaks only; old ZenTao may display them as one compressed paragraph.

## Word Output Format

When the user asks for Word output, create a `.docx` using this structure:

```text
一.修改功能点

（1）修改功能点
1.新增……
2.调整……
3.删除……

（2）修改功能点
1.新增……
2.调整……
3.删除……

二.历史数据处理方法
1.历史数据范围：……
2.处理方式：……
3.执行时机：……
4.校验方法：……
```

Rules:
- Use one `（n）修改功能点` block per functional change.
- Inside each block, list only applicable items. If `新增`, `调整`, or `删除` has no content, omit that line.
- Keep wording short enough for developers and testers to act on.

## ZenTao Title Format

Use:

```text
【后端】功能点1；功能点2
【前端】功能点1；功能点2
【前端+后端】功能点1；功能点2
```

Examples:

```text
【后端】销售业务日志移除工厂数据；合并推送无匹配分组策略时跳过数据
【前端+后端】新增批量导入入口；调整导入结果展示；删除旧版校验提示
```

## ZenTao Body Template

Use this exact section order:

```text
1.需求背景：

（1）现状：

（2）诉求/期望：


2.优先级判定因素

（0）影响人数：

（1）使用频次（天级/周级/月级）：

（2）单次操作成本：

（3）紧急程度（一般/紧急/很紧急）：

（4）需求价值（降本/增效/流程化/规范化）：

（5）最晚上线时间：


3.产品设计：

一.修改功能点

（1）修改功能点
1.新增……
2.调整……
3.删除……

二.历史数据处理方法
1.历史数据范围：……
2.处理方式：……
3.执行时机：……
4.校验方法：……


4.后端关注点：


5.前端关注点：


6.测试关注点：


7.日志需求：


8.历史数据处理：


9.权限管理：


10.潜在风险
```

Default handling:
- Put all requirement content under `3.产品设计：`.
- Keep all other sections empty unless the user explicitly asks to fill them.
- Do not write `无`, `待确认`, summaries, or references in non-product-design sections by default.

## Confirmation Checklist

Before asking the user to confirm, check:

- Title prefix matches impact scope.
- Title lists all functional change points briefly.
- Each functional change is split into its own `（n）修改功能点`.
- Each functional change contains only applicable `新增/调整/删除` lines.
- Historical data handling is present.
- Non-product-design sections are left empty unless the user explicitly asks to fill them.
- No ZenTao write has been performed yet.

For more examples and wording guidance, see `references/examples.md` only when the task needs examples.
