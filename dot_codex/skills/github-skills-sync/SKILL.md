---
name: github-skills-sync
description: Sync local Codex skills and safe Codex configuration files to GitHub through chezmoi. Use whenever any skill or Codex config is created, edited, installed, removed, or updated; when the user asks to upload skills/config to GitHub; or when Codex finishes modifying files under ~/.codex/skills or selected ~/.codex config files and should add them to chezmoi, commit, and push the source repo.
---

# GitHub Skills Sync

Keep local Codex skills and safe Codex configuration files managed by chezmoi and pushed to a GitHub repository after changes.

## Workflow

1. Run the sync script after any skill/config creation, update, install, or deletion:

```bash
bash ~/.codex/skills/github-skills-sync/scripts/sync_skills_to_github.sh
```

2. If the chezmoi source repository has not been connected to GitHub yet, provide the remote URL:

```bash
bash ~/.codex/skills/github-skills-sync/scripts/sync_skills_to_github.sh --remote git@github.com:OWNER/REPO.git
```

3. Use a clear commit message when the user gives one:

```bash
bash ~/.codex/skills/github-skills-sync/scripts/sync_skills_to_github.sh --message "Update reconciliation skills"
```

## Safety Rules

- Review `chezmoi status` and the chezmoi source `git status` before pushing when changes look unexpected.
- Do not commit runtime logs, local environment files, caches, credentials, or generated temporary output.
- Never commit `~/.codex/auth.json`, session history, sqlite databases, logs, caches, generated images, plugin caches, or temporary directories.
- Codex config sync is intentionally allowlisted: `config.toml`, `AGENTS.md`, `.codex-global-state.json`, `chrome-native-hosts-v2.json`, and `automations/*/automation.toml`.
- By default, keep `.system/` excluded because those are bundled system skills, not user-maintained skills.
- If the user explicitly wants bundled system skills included too, run the script with `--include-system`.
- If pushing fails because no remote exists or authentication is missing, leave the local commit intact and tell the user what remote or login step is needed.

## Script

Use `scripts/sync_skills_to_github.sh` for the whole operation. The script initializes chezmoi if needed, adds skill files and allowlisted Codex config files into chezmoi source state, commits source changes, and pushes when a remote is configured.
