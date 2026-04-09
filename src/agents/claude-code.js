'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();
const CLAUDE_DIR = path.join(HOME, '.claude');
const SETTINGS_PATH = path.join(CLAUDE_DIR, 'settings.json');

function isInstalled() {
  try {
    if (!fs.existsSync(SETTINGS_PATH)) return false;
    const s = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    return !!(s.statusLine && s.statusLine.command && s.statusLine.command.includes('m0squared'));
  } catch {
    return false;
  }
}

function install(installDir) {
  const scriptPath = path.join(installDir, 'indicator.py');

  // Ensure ~/.claude exists
  fs.mkdirSync(CLAUDE_DIR, { recursive: true });

  // Read or init settings.json
  let settings = {};
  if (fs.existsSync(SETTINGS_PATH)) {
    try {
      settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    } catch {
      settings = {};
    }
  }

  settings.statusLine = {
    type: 'command',
    command: `python3 ${scriptPath}`,
  };

  fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2) + '\n');
  return { ok: true };
}

function uninstall() {
  if (!fs.existsSync(SETTINGS_PATH)) return { ok: true };

  try {
    const settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8'));
    if (settings.statusLine && settings.statusLine.command &&
        settings.statusLine.command.includes('m0squared')) {
      delete settings.statusLine;
      fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2) + '\n');
    }
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

module.exports = { isInstalled, install, uninstall };
