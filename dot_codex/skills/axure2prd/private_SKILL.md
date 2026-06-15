---
name: axure2prd
description: Convert Axure RP prototype files (.rp) into a single development-ready Markdown design document. Use when the user asks to interpret Axure files, extract design information from doc/axure, generate PRD or development design docs, turn prototype text into functional requirements, or output Markdown under doc/markdown. This skill should produce structured page specs, fields, actions, business rules, validation, data model suggestions, API suggestions, and open questions rather than raw field dumps.
---

# Axure To Development Design Document

Convert Axure RP (`.rp`) prototype files into one readable Markdown document for developers.

Default output is a **single integrated development design document**, not one raw Markdown file per page.

## Core Workflow

1. Locate the input `.rp` file. If the user does not specify a path, check `doc/axure/`.
2. Generate a single development design document into `doc/markdown/`.
3. Review the generated Markdown and refine it so it is usable by developers:
   - organize by function and prototype order
   - describe page goals, fields, actions, business rules, validation, status changes, and edge cases
   - add data model and API suggestions when the prototype implies them
   - mark uncertain or missing information as待确认问题
4. Ensure `doc/markdown/` contains the intended final Markdown file. Do not leave split per-page `.md` files unless the user explicitly asks for them.

## Default Command

Resolve `scripts/axure_parser.py` relative to this skill directory. In a project that also vendors the skill, the local script path may work; otherwise run the installed script by absolute path.

```bash
python3 <skill-dir>/scripts/axure_parser.py doc/axure/<prototype>.rp \
  -o doc/markdown \
  --dev-design \
  --filename <prototype>.md
```

For the current repo shape, this usually means:

```bash
python3 scripts/axure_parser.py doc/axure/MSA.rp -o doc/markdown --dev-design --filename MSA.md
```

## Output Standard

The final Markdown should be directly useful for implementation. Include these sections when applicable:

- 文档说明
- 功能范围
- 业务主流程
- 角色和权限
- 通用枚举和配置
- 每个功能页面的页面目标、字段、列表、操作、业务规则、开发落点
- 报告/分析类页面的填写项、结果项、公式和判定规则
- 数据模型建议
- 接口建议
- 校验和异常处理
- 待确认问题

## Do Not

- Do not stop at raw text extraction or field listing.
- Do not generate many page-level Markdown files unless requested.
- Do not invent confirmed requirements. If a rule is inferred, label it as开发建议 or待确认.
- Do not overwrite a curated design document with a lower-quality automatic draft without reviewing it.

## Parser Capabilities

`scripts/axure_parser.py` supports:

- Axure RP 10+ ZIP/JSON projects
- Axure RP 9 ZIP/XML projects
- RP9 binary/gzip fallback files that are not ZIP archives
- raw single-file extraction with `--single-file`
- development design document generation with `--dev-design`

## Useful Options

| Option | Description |
| --- | --- |
| `--output`, `-o` | Output directory |
| `--dev-design` | Generate one structured development design document |
| `--filename` | Output Markdown filename |
| `--single-file` | Generate one raw extraction file |
| `--images-dir` | Subdirectory for extracted images |
| `--keep-temp` | Keep temporary extraction directory for debugging ZIP-based files |

## Quality Check

Before finishing:

```bash
python3 -m py_compile scripts/axure_parser.py
find doc/markdown -maxdepth 1 -type f -name '*.md' -print
```

Open the final Markdown and confirm it reads like a design document with implementable behavior, not a prototype text dump.
