#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CODEX_HOME_DIR="${CODEX_HOME_DIR:-$HOME/.codex}"
CURRENT_CODEX_SKILLS="${CURRENT_CODEX_SKILLS:-$HOME/.skills}"
QODER_HOME_DIR="${QODER_HOME_DIR:-$HOME/.qoderwork}"
CHEZMOI_BIN="${CHEZMOI_BIN:-$HOME/.local/bin/chezmoi}"
SOURCE_DIR="${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi}"
REMOTE_URL=""
BRANCH="main"
MESSAGE=""
INCLUDE_SYSTEM=0

usage() {
  cat <<'EOF'
Usage: sync_skills_to_github.sh [--remote URL] [--branch NAME] [--message TEXT] [--include-system]

Adds safe Codex/Qoder config files and shared skills to chezmoi source state,
commits changes, and pushes the chezmoi source repository to the configured
GitHub remote when available.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE_URL="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --message)
      MESSAGE="${2:-}"
      shift 2
      ;;
    --include-system)
      INCLUDE_SYSTEM=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -x "$CHEZMOI_BIN" ]]; then
  echo "chezmoi not found at $CHEZMOI_BIN. Install chezmoi first." >&2
  exit 1
fi

if [[ ! -d "$SOURCE_DIR/.git" ]]; then
  "$CHEZMOI_BIN" init
fi

cd "$SOURCE_DIR"

if ! git config user.name >/dev/null; then
  git config user.name "Codex Skills Sync"
fi

if ! git config user.email >/dev/null; then
  git config user.email "codex-skills-sync@users.noreply.github.com"
fi

if [[ -n "$REMOTE_URL" ]]; then
  if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REMOTE_URL"
  else
    git remote add origin "$REMOTE_URL"
  fi
fi

bash "$SCRIPT_DIR/sync_shared_skills.sh" --apply-to-endpoints

add_if_exists() {
  local target="$1"
  if [[ -f "$target" ]]; then
    "$CHEZMOI_BIN" add "$target"
  fi
}

sanitize_qoder_mcp_adaptor() {
  local target="$SOURCE_DIR/dot_qoderwork/private_mcp-adaptor.config"
  if [[ ! -f "$target" ]]; then
    return
  fi
  python3 - "$target" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
data = json.loads(path.read_text())
if "token" in data and data["token"]:
    data["token"] = "__REDACTED__"
headers = data.get("headers")
if isinstance(headers, dict):
    for key in list(headers):
        if key.lower() in {"x-api-key", "authorization", "token"} and headers[key]:
            headers[key] = "__REDACTED__"
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY
}

prune_source_tree() {
  local root="$1"
  shift
  if [[ ! -d "$root" ]]; then
    return
  fi
  find "$root" "$@" -exec rm -rf {} +
}

add_if_exists "$CODEX_HOME_DIR/config.toml"
add_if_exists "$CODEX_HOME_DIR/AGENTS.md"
add_if_exists "$CODEX_HOME_DIR/.codex-global-state.json"
add_if_exists "$CODEX_HOME_DIR/chrome-native-hosts-v2.json"

if [[ -d "$CODEX_HOME_DIR/automations" ]]; then
  find "$CODEX_HOME_DIR/automations" -path '*/automation.toml' -type f -print | while IFS= read -r automation_file; do
    "$CHEZMOI_BIN" add "$automation_file"
  done
fi

add_if_exists "$QODER_HOME_DIR/.qoder.json"
add_if_exists "$QODER_HOME_DIR/.config.json"
add_if_exists "$QODER_HOME_DIR/mcp-adaptor.config"
add_if_exists "$QODER_HOME_DIR/commands/create-command.md"
add_if_exists "$QODER_HOME_DIR/permission-match-for-bash/safe-alias-scripts/safe_rm.sh"

if [[ -d "$CURRENT_CODEX_SKILLS" ]]; then
  find "$CURRENT_CODEX_SKILLS" -mindepth 1 -maxdepth 1 -type d \
    -not -name '.git' \
    -not -name '.temp' \
    -not -name '.system' \
    -print | while IFS= read -r skill_dir; do
      "$CHEZMOI_BIN" add "$skill_dir"
    done

  if [[ "$INCLUDE_SYSTEM" -eq 1 && -d "$CURRENT_CODEX_SKILLS/.system" ]]; then
    "$CHEZMOI_BIN" add "$CURRENT_CODEX_SKILLS/.system"
  fi
fi

cd "$SOURCE_DIR"
sanitize_qoder_mcp_adaptor
prune_source_tree "$SOURCE_DIR/dot_qoderwork" \
  \( -path '*/todos' -o -path '*/todos/*' \
  -o -path '*/plugins' -o -path '*/plugins/*' \
  -o -path '*/logs' -o -path '*/logs/*' \
  -o -path '*/cache' -o -path '*/cache/*' \
  -o -path '*/.cache' -o -path '*/.cache/*' \
  -o -path '*/projects' -o -path '*/projects/*' \
  -o -path '*/workspace' -o -path '*/workspace/*' \
  -o -path '*/shell-snapshots' -o -path '*/shell-snapshots/*' \)
prune_source_tree "$SOURCE_DIR/dot_codex" \
  \( -path '*/plugins' -o -path '*/plugins/*' \
  -o -path '*/cache' -o -path '*/cache/*' \
  -o -path '*/tmp' -o -path '*/tmp/*' \
  -o -path '*/.tmp' -o -path '*/.tmp/*' \
  -o -path '*/sessions' -o -path '*/sessions/*' \
  -o -path '*/logs' -o -path '*/logs/*' \)
prune_source_tree "$SOURCE_DIR/dot_skills" \
  \( -path '*/__pycache__' -o -path '*/__pycache__/*' \
  -o -name '*.pyc' \)
prune_source_tree "$SOURCE_DIR/dot_codex" \
  \( -path '*/__pycache__' -o -path '*/__pycache__/*' \
  -o -name '*.pyc' \)
prune_source_tree "$SOURCE_DIR/dot_qoderwork" \
  \( -path '*/__pycache__' -o -path '*/__pycache__/*' \
  -o -name '*.pyc' \)
git add .chezmoiignore dot_codex dot_qoderwork dot_skills
if [[ "$INCLUDE_SYSTEM" -ne 1 && -d dot_skills/dot_system ]]; then
  git rm -r --quiet dot_skills/dot_system
fi

python3 - <<'PY'
from pathlib import Path
import re
import sys

root = Path.cwd()
scan_roots = [root / "dot_skills", root / "dot_codex", root / "dot_qoderwork"]
patterns = [
    re.compile(r'password["\']?\s*[:=]\s*["\'][^"\']{6,}', re.I),
    re.compile(r'DB_PASSWORD=(?!\$|\*{3})([^\n]{6,})'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----'),
]
findings = []
for scan_root in scan_roots:
    if not scan_root.exists():
        continue
    for path in scan_root.rglob("*"):
        if path.name in {"sync_skills_to_github.sh", "executable_sync_skills_to_github.sh"}:
            continue
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in patterns):
                findings.append(f"{path.relative_to(root)}:{lineno}")
                break

if findings:
    print("Potential secrets detected; aborting sync:", file=sys.stderr)
    for finding in findings[:100]:
        print(f"  {finding}", file=sys.stderr)
    sys.exit(1)
PY

if git diff --cached --quiet; then
  echo "No chezmoi skill changes to commit."
else
  if [[ -z "$MESSAGE" ]]; then
    MESSAGE="Sync Codex skills via chezmoi $(date '+%Y-%m-%d %H:%M:%S')"
  fi
  git commit -m "$MESSAGE"
fi

if git remote get-url origin >/dev/null 2>&1; then
  CURRENT_BRANCH="$(git branch --show-current)"
  if [[ -z "$CURRENT_BRANCH" ]]; then
    CURRENT_BRANCH="$BRANCH"
  fi
  git push -u origin "$CURRENT_BRANCH"
else
  echo "No GitHub remote configured. Re-run with --remote git@github.com:OWNER/REPO.git"
fi
