# axure2prd

`axure2prd` is a Codex skill for converting Axure RP (`.rp`) prototype files into a single development-ready Markdown design document.

It is intended for teams that need to turn prototype content into implementable documentation, not just extract raw page text.

## What It Does

- Reads Axure files from project paths such as `doc/axure/`.
- Extracts page text, fields, actions, options, and business notes.
- Supports ZIP-based Axure RP 9/10 files and RP9 binary/gzip fallback files.
- Generates one integrated Markdown document under `doc/markdown/`.
- Structures the output as a developer-facing design document with:
  - feature scope
  - business flow
  - page goals
  - form fields
  - list/table fields
  - page actions
  - business rules
  - validation and exception rules
  - data model suggestions
  - API suggestions
  - open questions

## Skill Trigger

Use this skill when the user asks to:

- interpret or parse Axure prototypes
- extract design information from `doc/axure`
- generate PRD or development design documents
- convert prototype text into functional requirements
- output Markdown into `doc/markdown`

## Typical Usage

From a project root:

```bash
python3 scripts/axure_parser.py doc/axure/MSA.rp \
  -o doc/markdown \
  --dev-design \
  --filename MSA.md
```

When using the installed Codex skill directly:

```bash
python3 ~/.codex/skills/axure2prd/scripts/axure_parser.py doc/axure/<prototype>.rp \
  -o doc/markdown \
  --dev-design \
  --filename <prototype>.md
```

## Output Principle

The default output should be a single development design document. Avoid leaving multiple page-level Markdown files unless the user explicitly requests that format.

The generated document should be reviewed and refined so it reads like an implementation guide, not a raw field dump.

## Files

```text
axure2prd/
├── SKILL.md
├── README.md
├── LICENSE
└── scripts/
    └── axure_parser.py
```

## Validation

```bash
python3 -m py_compile scripts/axure_parser.py
```

For installed skill validation:

```bash
python3 -m py_compile ~/.codex/skills/axure2prd/scripts/axure_parser.py
```

