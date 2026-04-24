'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();
const CODEX_DIR = path.join(HOME, '.codex');
const CONFIG_PATH = path.join(CODEX_DIR, 'config.toml');
const HOOKS_PATH = path.join(CODEX_DIR, 'hooks.json');

function isInstalled() {
  try {
    if (!fs.existsSync(HOOKS_PATH)) return false;
    const h = JSON.parse(fs.readFileSync(HOOKS_PATH, 'utf8'));
    const postHooks = h.PostToolUse || [];
    return postHooks.some(h => JSON.stringify(h).includes('m0squared'));
  } catch {
    return false;
  }
}

function install(installDir) {
  const hookScript = path.join(installDir, 'hooks', 'codex-hook.py');

  fs.mkdirSync(CODEX_DIR, { recursive: true });

  // Enable hooks in config.toml
  let toml = '';
  if (fs.existsSync(CONFIG_PATH)) {
    toml = fs.readFileSync(CONFIG_PATH, 'utf8');
  }

  if (!toml.includes('[features]')) {
    toml += '\n[features]\ncodex_hooks = true\n';
  } else if (!toml.includes('codex_hooks')) {
    toml = toml.replace('[features]', '[features]\ncodex_hooks = true');
  }

  fs.writeFileSync(CONFIG_PATH, toml);

  // Add PostToolUse hook to hooks.json
  let hooks = {};
  if (fs.existsSync(HOOKS_PATH)) {
    try {
      hooks = JSON.parse(fs.readFileSync(HOOKS_PATH, 'utf8'));
    } catch {
      hooks = {};
    }
  }

  if (!hooks.PostToolUse) hooks.PostToolUse = {};
  if (!hooks.PostToolUse['*']) hooks.PostToolUse['*'] = [];

  // Remove any existing m0squared hook
  hooks.PostToolUse['*'] = hooks.PostToolUse['*'].filter(
    h => !JSON.stringify(h).includes('m0squared')
  );

  hooks.PostToolUse['*'].push({
    command: `python3 ${hookScript}`,
    timeout: 5,
    statusMessage: 'M0² tracking tokens…',
  });

  fs.writeFileSync(HOOKS_PATH, JSON.stringify(hooks, null, 2) + '\n');
  return { ok: true };
}

function uninstall() {
  if (!fs.existsSync(HOOKS_PATH)) return { ok: true };

  try {
    const hooks = JSON.parse(fs.readFileSync(HOOKS_PATH, 'utf8'));
    if (hooks.PostToolUse && hooks.PostToolUse['*']) {
      hooks.PostToolUse['*'] = hooks.PostToolUse['*'].filter(
        h => !JSON.stringify(h).includes('m0squared')
      );
    }
    fs.writeFileSync(HOOKS_PATH, JSON.stringify(hooks, null, 2) + '\n');
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

module.exports = { isInstalled, install, uninstall };
