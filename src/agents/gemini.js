'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();
const GEMINI_DIR = path.join(HOME, '.gemini');
const SETTINGS_PATH = path.join(GEMINI_DIR, 'settings.json');

function isInstalled() {
  try {
    if (!fs.existsSync(SETTINGS_PATH)) return false;
    const s = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    const afterTool = s.hooks && s.hooks.AfterTool;
    return !!(afterTool && JSON.stringify(afterTool).includes('m0squared'));
  } catch {
    return false;
  }
}

function install(installDir) {
  const hookScript = path.join(installDir, 'hooks', 'gemini-hook.py');

  fs.mkdirSync(GEMINI_DIR, { recursive: true });

  // Read or init settings.json
  let settings = {};
  if (fs.existsSync(SETTINGS_PATH)) {
    try {
      settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    } catch {
      settings = {};
    }
  }

  if (!settings.hooks) settings.hooks = {};

  if (!settings.hooks.AfterTool) settings.hooks.AfterTool = [];

  // Remove any existing m0squared hook
  settings.hooks.AfterTool = settings.hooks.AfterTool.filter(
    entry => !JSON.stringify(entry).includes('m0squared')
  );

  settings.hooks.AfterTool.push({
    matcher: '.*',
    hooks: [
      {
        name: 'm0squared-tracker',
        type: 'command',
        command: `python3 ${hookScript}`,
        timeout: 5000,
      },
    ],
  });

  fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2) + '\n');
  return { ok: true };
}

function uninstall() {
  if (!fs.existsSync(SETTINGS_PATH)) return { ok: true };

  try {
    const settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    if (settings.hooks && settings.hooks.AfterTool) {
      settings.hooks.AfterTool = settings.hooks.AfterTool.filter(
        entry => !JSON.stringify(entry).includes('m0squared')
      );
    }
    fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2) + '\n');
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

module.exports = { isInstalled, install, uninstall };
