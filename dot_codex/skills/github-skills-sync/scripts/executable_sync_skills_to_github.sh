#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CODEX_HOME_DIR="$(cd "${SKILLS_ROOT}/.." && pwd)"
CHEZMOI_BIN="${CHEZMOI_BIN:-$HOME/.local/bin/chezmoi}"
SOURCE_DIR="${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi}"
REMOTE_URL=""
BRANCH="main"
MESSAGE=""
INCLUDE_SYSTEM=0

usage() {
  cat <<'EOF'
Usage: sync_skills_to_github.sh [--remote URL] [--branch NAME] [--message TEXT] [--include-system]

Adds ~/.codex/skills and safe ~/.codex config files to chezmoi source state, commits changes, and pushes
the chezmoi source repository to the configured GitHub remote when available.
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

cd "$SKILLS_ROOT"
find . -type f \
  -not -path './.git/*' \
  -not -name '*.log' \
  -not -name '*.err.log' \
  -not -name '.env' \
  -not -name '.env.*' \
  -not -path './__pycache__/*' \
  -not -name '*.pyc' \
  -not -name '.DS_Store' \
  -print | while IFS= read -r path; do
    path="${path#./}"
    case "$path" in
      .system/*)
        if [[ "$INCLUDE_SYSTEM" -eq 1 ]]; then
          "$CHEZMOI_BIN" add "$SKILLS_ROOT/$path"
        fi
        ;;
      *)
        "$CHEZMOI_BIN" add "$SKILLS_ROOT/$path"
        ;;
    esac
  done

add_if_exists() {
  local target="$1"
  if [[ -f "$target" ]]; then
    "$CHEZMOI_BIN" add "$target"
  fi
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

cd "$SOURCE_DIR"
git add dot_codex

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
