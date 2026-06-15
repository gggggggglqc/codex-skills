---
name: database-config
description: Manage local database connection profiles safely for Codex and Qoder. Use when creating, organizing, auditing, or using database credentials, DB profiles, MySQL, Doris, ERP database access, read-only query scripts, or when replacing hardcoded database secrets with local configuration.
---

# Database Config

## Purpose

Use this skill whenever a task needs database credentials or database access configuration.

The rule is simple:

- Real credentials live only in `~/.config/db-profiles/*.env`.
- Skills and GitHub may contain profile names, schemas, examples, and scripts.
- Skills and GitHub must not contain real passwords, tokens, private keys, or connection secrets.

## Profile Names

Current local profile names:

- `erp-mysql`: ERP/FMS MySQL read-only profile.
- `doris`: Doris warehouse read-only profile.
- `wms-mysql`: WMS/JLS MySQL read-only profile.

For the redacted inventory, see `references/profile-inventory.md`.

## How To Use

Use `scripts/load_db_profile.py` to inspect a profile without exposing secrets:

```bash
python3 ~/.codex/skills/database-config/scripts/load_db_profile.py --profile erp-mysql
```

Use `scripts/check_db_connection.py` for a read-only smoke test:

```bash
python3 ~/.codex/skills/database-config/scripts/check_db_connection.py --profile doris
```

When writing or patching scripts:

1. Read the profile from `~/.config/db-profiles/<profile>.env`.
2. Allow environment variables to override local profile fields.
3. Keep `DB_PASSWORD` out of logs, errors, commits, and final responses.
4. Prefer read-only queries. Never run writes unless the user explicitly asks and the profile is known to allow it.

## Required Fields

Each profile file should contain:

```bash
DB_TYPE=mysql
DB_HOST=example.internal
DB_PORT=3306
DB_USER=readonly_user
DB_PASSWORD=$LOCAL_ONLY_SECRET
DB_NAME=database_name
DB_CHARSET=utf8mb4
DB_READONLY=1
```

## Sync Rule

This skill may be synced to GitHub. The files under `~/.config/db-profiles/` must remain local-only.

Before syncing skills/configuration, run a secret scan and remove hardcoded database secrets from skill files.
