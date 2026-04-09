'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const HOME = os.homedir();

function commandExists(cmd) {
  try {
    execSync(`which ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function detectClaudeCode() {
  const hasDir = fs.existsSync(path.join(HOME, '.claude'));
  const hasCmd = commandExists('claude');
  return hasDir || hasCmd;
}

function detectCodex() {
  const hasDir = fs.existsSync(path.join(HOME, '.codex'));
  const hasCmd = commandExists('codex');
  return hasDir || hasCmd;
}

function detectGemini() {
  const hasDir = fs.existsSync(path.join(HOME, '.gemini'));
  const hasCmd = commandExists('gemini');
  return hasDir || hasCmd;
}

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

module.exports = { detectAll, detectClaudeCode, detectCodex, detectGemini, getInstallDir };
