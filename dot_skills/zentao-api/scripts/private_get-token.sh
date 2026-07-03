#!/usr/bin/env bash
# 获取禅道 API 调用所需的 URL、token/session 和用户名，按优先级：缓存文件 > 环境变量 > 账号密码登录。
# 用法：eval "$(bash get-token.sh)"  → 新版设置 ZENTAO_URL、ZENTAO_TOKEN、ZENTAO_ACCOUNT；老版设置 ZENTAO_AUTH_MODE=legacy 和 session 变量
# 依赖：curl, node
# 缓存文件 ~/.zentao-token.json 保存 token 或老版 session、url、account，下次可免密直接使用。
# 注：v2 token 永久有效；老版禅道会输出 session 变量。如需切换账号/服务器，删除缓存文件后重新运行即可。

set -euo pipefail

CACHE_FILE="${HOME}/.zentao-token.json"

# 输出新版 token 三元组（KEY=VALUE 格式，可直接 eval）并退出
output_and_exit() {
  local url="$1" token="$2" account="$3"
  echo "ZENTAO_URL=${url}"
  echo "ZENTAO_TOKEN=${token}"
  echo "ZENTAO_ACCOUNT=${account}"
  exit 0
}

# 老版禅道没有 v2 token 登录，输出 session 三元组
output_legacy_and_exit() {
  local url="$1" session_name="$2" session_id="$3" account="$4"
  echo "ZENTAO_URL=${url}"
  echo "ZENTAO_AUTH_MODE=legacy"
  echo "ZENTAO_SESSION_NAME=${session_name}"
  echo "ZENTAO_SESSION_ID=${session_id}"
  echo "ZENTAO_ACCOUNT=${account}"
  exit 0
}

# ── 1. 优先：从缓存文件读取 url、token/session、account（单次 node 调用）────────────
if [[ -f "$CACHE_FILE" ]]; then
  _cache_url='' _cache_token='' _cache_account='' _cache_auth_mode='' _cache_session_name='' _cache_session_id=''
  {
    IFS= read -r _cache_url
    IFS= read -r _cache_token
    IFS= read -r _cache_account
    IFS= read -r _cache_auth_mode
    IFS= read -r _cache_session_name
    IFS= read -r _cache_session_id
  } < <(node -e "
try {
  const d = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'));
  process.stdout.write(
    (d.url||'') + '\n' +
    (d.token||'') + '\n' +
    (d.account||'') + '\n' +
    (d.authMode||'') + '\n' +
    (d.sessionName||'') + '\n' +
    (d.sessionID||'') + '\n'
  );
} catch(e) { process.stdout.write('\n\n\n\n\n\n'); }
" "$CACHE_FILE" 2>/dev/null || printf '\n\n\n\n\n\n')

  # 用缓存补全缺失的环境变量
  [[ -z "${ZENTAO_URL:-}"     && -n "$_cache_url"     ]] && ZENTAO_URL="$_cache_url"
  [[ -z "${ZENTAO_ACCOUNT:-}" && -n "$_cache_account" ]] && ZENTAO_ACCOUNT="$_cache_account"

  # 缓存 token 有效且 url/account 均匹配，直接输出三元组（无需密码）
  if [[ -n "$_cache_token" \
     && "${ZENTAO_URL:-}" == "$_cache_url" \
     && ( -z "${ZENTAO_ACCOUNT:-}" || "${ZENTAO_ACCOUNT:-}" == "$_cache_account" ) ]]; then
    output_and_exit "$_cache_url" "$_cache_token" "$_cache_account"
  fi

  # 老版禅道缓存有效时，直接输出 session（无需再次要求账号密码）
  if [[ "$_cache_auth_mode" == "legacy" \
     && -n "$_cache_session_name" \
     && -n "$_cache_session_id" \
     && "${ZENTAO_URL:-}" == "$_cache_url" \
     && ( -z "${ZENTAO_ACCOUNT:-}" || "${ZENTAO_ACCOUNT:-}" == "$_cache_account" ) ]]; then
    output_legacy_and_exit "$_cache_url" "$_cache_session_name" "$_cache_session_id" "$_cache_account"
  fi
fi

# ── 2. 其次：从环境变量读取 token（仍需 ZENTAO_URL）────────────────────────
if [[ -n "${ZENTAO_TOKEN:-}" ]]; then
  if [[ -z "${ZENTAO_URL:-}" ]]; then
    echo "错误：设置了 ZENTAO_TOKEN 但缺少 ZENTAO_URL，请同时提供服务器地址。" >&2
    exit 1
  fi
  # 写入缓存，方便下次无需环境变量直接使用
  node - "$CACHE_FILE" "${ZENTAO_TOKEN}" "${ZENTAO_URL}" "${ZENTAO_ACCOUNT:-}" <<'JSEOF'
const [,, cachePath, token, url, account] = process.argv;
const fs = require('fs');
fs.writeFileSync(cachePath, JSON.stringify({ token, url, account }, null, 2));
JSEOF
  output_and_exit "${ZENTAO_URL}" "${ZENTAO_TOKEN}" "${ZENTAO_ACCOUNT:-}"
fi

# ── 3. 再次：用账号密码重新登录（需 ZENTAO_URL、ZENTAO_ACCOUNT、ZENTAO_PASSWORD）
if [[ -z "${ZENTAO_URL:-}" || -z "${ZENTAO_ACCOUNT:-}" || -z "${ZENTAO_PASSWORD:-}" ]]; then
  echo "错误：Token 获取失败。请通过以下任一方式提供鉴权信息：" >&2
  echo "  · 缓存文件 ~/.zentao-token.json（含 url、token 或 legacy session、account 字段）" >&2
  echo "  · 环境变量 ZENTAO_TOKEN + ZENTAO_URL（直接提供 token 和服务器地址）" >&2
  echo "  · 环境变量 ZENTAO_URL、ZENTAO_ACCOUNT、ZENTAO_PASSWORD（账号密码登录）" >&2
  exit 1
fi

RESPONSE=$(curl -s -X POST "${ZENTAO_URL}/api.php/v2/users/login" \
  -H "Content-Type: application/json" \
  -d "{\"account\": \"${ZENTAO_ACCOUNT}\", \"password\": \"${ZENTAO_PASSWORD}\"}")

TOKEN=$(echo "$RESPONSE" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(chunks.join(''));
    const token = (data.data && data.data.token) || data.token || '';
    process.stdout.write(token);
  } catch (e) {
    process.stdout.write('');
  }
});
")

if [[ -z "$TOKEN" ]]; then
  LOGIN_ERRMSG=$(echo "$RESPONSE" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(chunks.join(''));
    process.stdout.write(String(data.errmsg || data.message || ''));
  } catch (e) {
    process.stdout.write('');
  }
});
")

  # 老版禅道 12.x 常见响应：{\"errcode\":401,\"errmsg\":\"缺少code参数\"}
  # 该实例不能用 v2 token 登录，改用 api-getsessionid.json + user-login.json。
  SESSION_RESPONSE=$(curl -s "${ZENTAO_URL}/api-getsessionid.json")
  SESSION_NAME=$(echo "$SESSION_RESPONSE" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const raw = JSON.parse(chunks.join(''));
    const data = typeof raw.data === 'string' ? JSON.parse(raw.data) : raw.data;
    process.stdout.write(data.sessionName || '');
  } catch (e) {
    process.stdout.write('');
  }
});
")
  SESSION_ID=$(echo "$SESSION_RESPONSE" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const raw = JSON.parse(chunks.join(''));
    const data = typeof raw.data === 'string' ? JSON.parse(raw.data) : raw.data;
    process.stdout.write(data.sessionID || '');
  } catch (e) {
    process.stdout.write('');
  }
});
")

  if [[ -n "$SESSION_NAME" && -n "$SESSION_ID" ]]; then
    ENCODED_ACCOUNT=$(node -e "process.stdout.write(encodeURIComponent(process.argv[1]))" "$ZENTAO_ACCOUNT")
    ENCODED_PASSWORD=$(node -e "process.stdout.write(encodeURIComponent(process.argv[1]))" "$ZENTAO_PASSWORD")
    LEGACY_LOGIN_RESPONSE=$(curl -s "${ZENTAO_URL}/user-login.json?${SESSION_NAME}=${SESSION_ID}&account=${ENCODED_ACCOUNT}&password=${ENCODED_PASSWORD}")
    LEGACY_STATUS=$(echo "$LEGACY_LOGIN_RESPONSE" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(chunks.join(''));
    process.stdout.write(String(data.status || ''));
  } catch (e) {
    process.stdout.write('');
  }
});
")
    if [[ "$LEGACY_STATUS" == "success" ]]; then
      node - "$CACHE_FILE" "$ZENTAO_URL" "$ZENTAO_ACCOUNT" "$SESSION_NAME" "$SESSION_ID" <<'JSEOF'
const [,, cachePath, url, account, sessionName, sessionID] = process.argv;
const fs = require('fs');
fs.writeFileSync(cachePath, JSON.stringify({ authMode: 'legacy', url, account, sessionName, sessionID }, null, 2));
JSEOF
      output_legacy_and_exit "$ZENTAO_URL" "$SESSION_NAME" "$SESSION_ID" "$ZENTAO_ACCOUNT"
    fi
  fi

  echo "登录失败，服务器响应：$RESPONSE" >&2
  [[ -n "$LOGIN_ERRMSG" ]] && echo "错误信息：$LOGIN_ERRMSG" >&2
  echo "错误：登录失败，请查看上方错误信息" >&2
  exit 1
fi

# ── 4. 缓存：写入 token、url、account ────────────────────────────────────────
node - "$CACHE_FILE" "$TOKEN" "$ZENTAO_URL" "$ZENTAO_ACCOUNT" <<'JSEOF'
const [,, cachePath, token, url, account] = process.argv;
const fs = require('fs');
fs.writeFileSync(cachePath, JSON.stringify({ token, url, account }, null, 2));
JSEOF

output_and_exit "$ZENTAO_URL" "$TOKEN" "$ZENTAO_ACCOUNT"
