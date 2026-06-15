---
name: github-skills-sync
description: Sync the local Codex skills directory to GitHub through chezmoi. Use whenever any skill is created, edited, installed, removed, or updated; when the user asks to upload skills to GitHub; or when Codex finishes modifying files under ~/.codex/skills and should add them to chezmoi, commit, and push the source repo.
---

# GitHub Skills Sync

Keep local Codex skills managed by chezmoi and pushed to a GitHub repository after skill changes.

## Workflow

1. Run the sync script after any skill creation, update, install, or deletion:

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
- By default, keep `.system/` excluded because those are bundled system skills, not user-maintained skills.
- If the user explicitly wants bundled system skills included too, run the script with `--include-system`.
- If pushing fails because no remote exists or authentication is missing, leave the local commit intact and tell the user what remote or login step is needed.

## Script

Use `scripts/sync_skills_to_github.sh` for the whole operation. The script initializes chezmoi if needed, adds the tracked skill files into chezmoi source state, commits source changes, and pushes when a remote is configured.
