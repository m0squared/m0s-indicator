'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();
const IS_WIN = process.platform === 'win32';

// Pure-Node PATH lookup: `which` doesn't exist on Windows and shelling out
// isn't needed to check whether a command is installed.
function commandExists(cmd) {
  const dirs = (process.env.PATH || '').split(path.delimiter).filter(Boolean);
  const exts = IS_WIN
    ? (process.env.PATHEXT || '.EXE;.CMD;.BAT;.COM').split(';').map(e => e.toLowerCase())
    : [''];
  for (const dir of dirs) {
    for (const ext of exts) {
      const candidate = path.join(dir, cmd + ext);
      try {
        const st = fs.statSync(candidate);
        if (st.isFile()) return true;
      } catch { /* keep looking */ }
    }
  }
  return false;
}

function detectAgent(dirName, cmd) {
  return fs.existsSync(path.join(HOME, dirName)) || commandExists(cmd);
}

function detectClaudeCode() { return detectAgent('.claude', 'claude'); }
function detectCodex()      { return detectAgent('.codex', 'codex'); }
function detectGemini()     { return detectAgent('.gemini', 'gemini'); }

function detectAll() {
  return {
    'claude-code': detectClaudeCode(),
    'codex': detectCodex(),
    'gemini': detectGemini(),
  };
}

function getInstallDir() {
  return path.join(HOME, '.m0squared');
}

module.exports = { detectAll, detectClaudeCode, detectCodex, detectGemini, getInstallDir, commandExists };
