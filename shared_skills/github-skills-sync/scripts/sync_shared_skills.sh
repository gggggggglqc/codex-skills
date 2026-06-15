#!/usr/bin/env bash
set -euo pipefail

CODEX_SKILLS="${CODEX_SKILLS:-$HOME/.codex/skills}"
QODER_SKILLS="${QODER_SKILLS:-$HOME/.qoderwork/skills}"
SOURCE_DIR="${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi}"
SHARED_SKILLS_DIR="${SHARED_SKILLS_DIR:-$SOURCE_DIR/shared_skills}"
APPLY_TO_ENDPOINTS=0

usage() {
  cat <<'EOF'
Usage: sync_shared_skills.sh [--apply-to-endpoints]

Merge Codex and Qoder skills into one shared_skills directory by skill name.
If a skill exists in both tools, the directory with the newest file mtime wins.
With --apply-to-endpoints, mirror shared_skills back into both ~/.codex/skills
and ~/.qoderwork/skills so both tools can use the same skill set.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply-to-endpoints)
      APPLY_TO_ENDPOINTS=1
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

latest_mtime() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    echo 0
    return
  fi
  find "$dir" -type f \
    -not -path '*/.git/*' \
    -not -name '*.log' \
    -not -name '*.err.log' \
    -not -name '.env' \
    -not -name '.env.*' \
    -not -name '*.pyc' \
    -not -name '.DS_Store' \
    -exec stat -f '%m' {} + 2>/dev/null | sort -n | tail -1
}

copy_skill() {
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  rsync -a --delete \
    --exclude '.git/' \
    --exclude '.system/' \
    --exclude '.temp/' \
    --exclude '*.log' \
    --exclude '*.err.log' \
    --exclude '.env' \
    --exclude '.env.*' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    "$src/" "$dst/"
}

mkdir -p "$SHARED_SKILLS_DIR"

tmp_names="$(mktemp)"
trap 'rm -f "$tmp_names"' EXIT

if [[ -d "$CODEX_SKILLS" ]]; then
  find "$CODEX_SKILLS" -mindepth 1 -maxdepth 1 -type d \
    -not -name '.git' \
    -not -name '.system' \
    -print | while IFS= read -r dir; do basename "$dir"; done >> "$tmp_names"
fi

if [[ -d "$QODER_SKILLS" ]]; then
  find "$QODER_SKILLS" -mindepth 1 -maxdepth 1 -type d \
    -not -name '.temp' \
    -print | while IFS= read -r dir; do basename "$dir"; done >> "$tmp_names"
fi

sort -u "$tmp_names" | while IFS= read -r skill_name; do
  [[ -n "$skill_name" ]] || continue
  codex_dir="$CODEX_SKILLS/$skill_name"
  qoder_dir="$QODER_SKILLS/$skill_name"
  codex_mtime="$(latest_mtime "$codex_dir")"
  qoder_mtime="$(latest_mtime "$qoder_dir")"

  if [[ "$qoder_mtime" -gt "$codex_mtime" ]]; then
    source_dir="$qoder_dir"
  else
    source_dir="$codex_dir"
  fi

  if [[ -d "$source_dir" ]]; then
    copy_skill "$source_dir" "$SHARED_SKILLS_DIR/$skill_name"
  fi
done

if [[ "$APPLY_TO_ENDPOINTS" -eq 1 ]]; then
  find "$SHARED_SKILLS_DIR" -mindepth 1 -maxdepth 1 -type d -print | while IFS= read -r shared_dir; do
    skill_name="$(basename "$shared_dir")"
    copy_skill "$shared_dir" "$CODEX_SKILLS/$skill_name"
    copy_skill "$shared_dir" "$QODER_SKILLS/$skill_name"
  done
fi
