---
name: github-skills-sync
description: Sync local Codex and Qoder skills/configuration to GitHub through chezmoi. Use whenever any skill, Codex config, or Qoder config is created, edited, installed, removed, or updated; when the user asks to upload skills/config to GitHub; or when Codex finishes modifying files under ~/.codex/skills, ~/.qoderwork/skills, or selected config files and should merge shared skills by name, add safe config to chezmoi, commit, and push the source repo.
---

# GitHub Skills Sync

Keep local Codex/Qoder skills and safe tool configuration files managed by chezmoi and pushed to a GitHub repository after changes.

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
- Never commit `~/.codex/auth.json`, `~/.qoderwork/.auth`, session history, sqlite databases, logs, caches, generated images, plugin caches, projects, todos, or temporary directories.
- Codex config sync is intentionally allowlisted: `config.toml`, `AGENTS.md`, `.codex-global-state.json`, `chrome-native-hosts-v2.json`, and `automations/*/automation.toml`.
- Qoder config sync is intentionally allowlisted: `.qoder.json`, `.config.json`, `mcp-adaptor.config`, `commands/create-command.md`, and `permission-match-for-bash/safe-alias-scripts/safe_rm.sh`.
- Skills are stored together in the chezmoi source repository under `shared_skills/<skill-name>/`. If the same skill exists in both Codex and Qoder, the directory with the newest file modification time wins.
- Run `scripts/sync_shared_skills.sh --apply-to-endpoints` to mirror `shared_skills` back into both `~/.codex/skills` and `~/.qoderwork/skills`.
- By default, keep `.system/` excluded because those are bundled system skills, not user-maintained skills.
- If the user explicitly wants bundled system skills included too, run the script with `--include-system`.
- If pushing fails because no remote exists or authentication is missing, leave the local commit intact and tell the user what remote or login step is needed.

## Script

Use `scripts/sync_skills_to_github.sh` for the whole operation. The script initializes chezmoi if needed, merges skills by name into `shared_skills`, mirrors them to both tools, adds allowlisted Codex/Qoder config files into chezmoi source state, commits source changes, and pushes when a remote is configured.
