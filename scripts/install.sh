#!/usr/bin/env bash
# M0² — Universal AI Agent HUD
# Curl installer: curl -sSL https://raw.githubusercontent.com/m0squared/m0squared/main/scripts/install.sh | bash
# © 2026 morius (M-zero-Squared). All rights reserved.

set -euo pipefail

REPO="m0squared/m0s-indicator"
BRANCH="main"
RAW="https://raw.githubusercontent.com/${REPO}/${BRANCH}"
INSTALL_DIR="${HOME}/.m0squared"

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
DIM="\033[2m"
R="\033[0m"

banner() {
  echo ""
  echo -e "${BOLD}  M0²${R}  Universal AI Agent HUD"
  echo -e "  ${DIM}curl installer  by morius${R}"
  echo ""
}

info()    { echo -e "  ${CYAN}→${R}  $1"; }
success() { echo -e "  ${GREEN}✓${R}  $1"; }
warn()    { echo -e "  ${YELLOW}!${R}  $1"; }
die()     { echo -e "  ${RED}✗${R}  $1"; exit 1; }

# Check dependencies
check_deps() {
  command -v python3 >/dev/null 2>&1 || die "python3 is required but not found."
  command -v curl    >/dev/null 2>&1 || die "curl is required but not found."
}

# Download a file
download() {
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  curl -sSfL "$url" -o "$dest" || die "Failed to download: $url"
}

# Patch JSON file with a key=value (using python3)
patch_json() {
  local file="$1" key="$2" value="$3"
  python3 - "$file" "$key" "$value" <<'PYEOF'
import sys, json
file, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(file) as f:
        data = json.load(f)
except Exception:
    data = {}
# Set nested key using dot notation
keys = key.split('.')
d = data
for k in keys[:-1]:
    if k not in d or not isinstance(d[k], dict):
        d[k] = {}
    d = d[k]
d[keys[-1]] = json.loads(value)
with open(file, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYEOF
}

# Detect installed agents
detect_agents() {
  AGENTS=()
  [ -d "${HOME}/.claude" ] || command -v claude >/dev/null 2>&1 && AGENTS+=("claude-code")
  [ -d "${HOME}/.codex"  ] || command -v codex  >/dev/null 2>&1 && AGENTS+=("codex")
  [ -d "${HOME}/.gemini" ] || command -v gemini >/dev/null 2>&1 && AGENTS+=("gemini")
}

# Install Claude Code integration
install_claude_code() {
  local settings="${HOME}/.claude/settings.json"
  mkdir -p "${HOME}/.claude"
  patch_json "$settings" "statusLine" \
    "{\"type\":\"command\",\"command\":\"python3 ${INSTALL_DIR}/indicator.py\"}"
  success "Claude Code"
}

# Install Codex CLI integration
install_codex() {
  local cfg="${HOME}/.codex/config.toml"
  local hooks="${HOME}/.codex/hooks.json"
  mkdir -p "${HOME}/.codex"

  # Enable hooks in config.toml
  if [ ! -f "$cfg" ] || ! grep -q "codex_hooks" "$cfg"; then
    echo -e "\n[features]\ncodex_hooks = true" >> "$cfg"
  fi

  # Add PostToolUse hook
  python3 - "$hooks" "${INSTALL_DIR}/hooks/codex-hook.py" <<'PYEOF'
import sys, json
hooks_file, script = sys.argv[1], sys.argv[2]
try:
    with open(hooks_file) as f:
        hooks = json.load(f)
except Exception:
    hooks = {}
if "PostToolUse" not in hooks:
    hooks["PostToolUse"] = {}
if "*" not in hooks["PostToolUse"]:
    hooks["PostToolUse"]["*"] = []
hooks["PostToolUse"]["*"] = [h for h in hooks["PostToolUse"]["*"]
                               if "m0squared" not in json.dumps(h)]
hooks["PostToolUse"]["*"].append({
    "command": f"python3 {script}",
    "timeout": 5
})
with open(hooks_file, 'w') as f:
    json.dump(hooks, f, indent=2)
    f.write('\n')
PYEOF
  success "Codex CLI"
}

# Install Gemini CLI integration
install_gemini() {
  local settings="${HOME}/.gemini/settings.json"
  mkdir -p "${HOME}/.gemini"

  python3 - "$settings" "${INSTALL_DIR}/hooks/gemini-hook.py" <<'PYEOF'
import sys, json
settings_file, script = sys.argv[1], sys.argv[2]
try:
    with open(settings_file) as f:
        settings = json.load(f)
except Exception:
    settings = {}
if "hooks" not in settings:
    settings["hooks"] = {}
if "AfterTool" not in settings["hooks"]:
    settings["hooks"]["AfterTool"] = []
settings["hooks"]["AfterTool"] = [e for e in settings["hooks"]["AfterTool"]
                                   if "m0squared" not in json.dumps(e)]
settings["hooks"]["AfterTool"].append({
    "matcher": ".*",
    "hooks": [{"name": "m0squared-tracker", "type": "command",
               "command": f"python3 {script}", "timeout": 5000}]
})
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
PYEOF
  success "Gemini CLI"
}

# ── Main ──────────────────────────────────────────────────────────────────────

banner
check_deps

info "Downloading core files…"
mkdir -p "${INSTALL_DIR}/hooks"

download "${RAW}/core/indicator.py"        "${INSTALL_DIR}/indicator.py"
download "${RAW}/core/hooks/codex-hook.py" "${INSTALL_DIR}/hooks/codex-hook.py"
download "${RAW}/core/hooks/gemini-hook.py" "${INSTALL_DIR}/hooks/gemini-hook.py"
download "${RAW}/config.default.json"      "${INSTALL_DIR}/config.json.default"

chmod +x "${INSTALL_DIR}/indicator.py"
chmod +x "${INSTALL_DIR}/hooks/codex-hook.py"
chmod +x "${INSTALL_DIR}/hooks/gemini-hook.py"

# Write default config if not exists
if [ ! -f "${INSTALL_DIR}/config.json" ]; then
  cp "${INSTALL_DIR}/config.json.default" "${INSTALL_DIR}/config.json"
fi

echo ""
info "Scanning for AI agents…"
echo ""

detect_agents

if [ ${#AGENTS[@]} -eq 0 ]; then
  warn "No AI agents detected. Install Claude Code, Codex CLI, or Gemini CLI first."
  echo ""
  exit 0
fi

for agent in "${AGENTS[@]}"; do
  case "$agent" in
    claude-code) install_claude_code ;;
    codex)       install_codex       ;;
    gemini)      install_gemini      ;;
  esac
done

echo ""
echo -e "  ${BOLD}${GREEN}M0² installed!${R}"
echo -e "  ${DIM}Restart your AI agent to see the HUD.${R}"
echo -e "  ${DIM}Config: ${INSTALL_DIR}/config.json${R}"
echo ""
