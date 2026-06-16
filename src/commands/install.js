'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

const ui = require('../ui');
const { detectAll, getInstallDir } = require('../detect');

// Ask the user once which HUD layout they want. Falls back to "rows" when
// there's no TTY (e.g. the global-install postinstall hook).
function promptLayout() {
  return new Promise((resolve) => {
    if (!process.stdin.isTTY || !process.stdout.isTTY) return resolve('rows');

    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    ui.section('Choose HUD layout:\n');
    console.log(`    ${ui.CYAN}1${ui.R}  rows    ${ui.DIM}identity on one line, bars on the next (default)${ui.R}`);
    console.log(`    ${ui.CYAN}2${ui.R}  inline  ${ui.DIM}everything on a single compact line${ui.R}\n`);
    rl.question(`  ${ui.DIM}Select [1/2] (default 1): ${ui.R}`, (answer) => {
      rl.close();
      const a = (answer || '').trim().toLowerCase();
      resolve(a === '2' || a === 'inline' ? 'inline' : 'rows');
    });
  });
}

// Merge a chosen layout into the installed config.json without clobbering
// any other user edits.
function writeLayout(installDir, layout) {
  const configDst = path.join(installDir, 'config.json');
  let cfg = {};
  if (fs.existsSync(configDst)) {
    try { cfg = JSON.parse(fs.readFileSync(configDst, 'utf8')); } catch { cfg = {}; }
  } else {
    try {
      cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '../../config.default.json'), 'utf8'));
    } catch { cfg = {}; }
  }
  cfg.layout = layout;
  fs.writeFileSync(configDst, JSON.stringify(cfg, null, 2) + '\n');
}

const AGENTS = {
  'claude-code': require('../agents/claude-code'),
  'codex': require('../agents/codex'),
  'gemini': require('../agents/gemini'),
};

const AGENT_LABELS = {
  'claude-code': 'Claude Code',
  'codex': 'Codex CLI',
  'gemini': 'Gemini CLI',
};

module.exports = async function install(opts = {}) {
  ui.banner();

  const installDir = getInstallDir();
  const targetAgent = opts.agent || null;

  // Detect agents
  ui.section('Scanning for AI agents…\n');
  const detected = detectAll();

  const toInstall = [];

  for (const [name, agent] of Object.entries(AGENTS)) {
    if (targetAgent && name !== targetAgent) continue;

    if (!detected[name]) {
      ui.agentLine(name, 'missing');
    } else if (agent.isInstalled()) {
      ui.agentLine(name, 'skip');
    } else {
      ui.agentLine(name, 'found');
      toInstall.push(name);
    }
  }

  if (toInstall.length === 0) {
    console.log();
    ui.info('Nothing to install — all detected agents already have M0².');
    ui.tip('Run "npx m0squared update" to update to the latest version.');
    console.log();
    return;
  }

  // Copy core files
  console.log();
  ui.section('Installing core files…');

  fs.mkdirSync(path.join(installDir, 'hooks'), { recursive: true });

  // Copy indicator.py
  const indicatorSrc = path.join(__dirname, '../../core/indicator.py');
  const indicatorDst = path.join(installDir, 'indicator.py');
  fs.copyFileSync(indicatorSrc, indicatorDst);
  fs.chmodSync(indicatorDst, '755');

  // Copy hook scripts
  for (const hookFile of ['codex-hook.py', 'gemini-hook.py']) {
    const src = path.join(__dirname, '../../core/hooks', hookFile);
    const dst = path.join(installDir, 'hooks', hookFile);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, dst);
      fs.chmodSync(dst, '755');
    }
  }

  // Write default config if not exists
  const configDst = path.join(installDir, 'config.json');
  if (!fs.existsSync(configDst)) {
    const configSrc = path.join(__dirname, '../../config.default.json');
    fs.copyFileSync(configSrc, configDst);
  }

  // Let the user pick their HUD layout, then persist it into config.json.
  console.log();
  const layout = await promptLayout();
  writeLayout(installDir, layout);

  // Install per agent
  console.log();
  ui.section(`Installing for: ${toInstall.map(n => AGENT_LABELS[n]).join(', ')}\n`);

  let anyFailed = false;

  for (const name of toInstall) {
    ui.agentLine(name, 'installing');
    try {
      const result = AGENTS[name].install(installDir);
      if (result.ok) {
        ui.agentLine(name, 'done');
      } else {
        ui.agentLine(name, 'error', result.error || 'unknown error');
        anyFailed = true;
      }
    } catch (e) {
      ui.agentLine(name, 'error', e.message);
      anyFailed = true;
    }
  }

  console.log();

  if (!anyFailed) {
    ui.success('M0² installed successfully!');
    ui.tip('Restart your AI agent to see the HUD.');
    ui.tip(`Config file: ${path.join(installDir, 'config.json')}`);
    console.log();
  } else {
    ui.error('Some agents failed to install. Check the errors above.');
  }
};
