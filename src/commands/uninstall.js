'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const ui = require('../ui');
const { getInstallDir } = require('../detect');

const AGENTS = {
  'claude-code': require('../agents/claude-code'),
  'codex': require('../agents/codex'),
  'gemini': require('../agents/gemini'),
};

module.exports = async function uninstall(opts = {}) {
  ui.banner();

  const targetAgent = opts.agent || null;

  ui.section('Removing M0² from agents…\n');

  for (const [name, agent] of Object.entries(AGENTS)) {
    if (targetAgent && name !== targetAgent) continue;

    ui.agentLine(name, 'installing');
    try {
      const result = agent.uninstall();
      if (result.ok) {
        ui.agentLine(name, 'done');
      } else {
        ui.agentLine(name, 'error', result.error || 'unknown');
      }
    } catch (e) {
      ui.agentLine(name, 'error', e.message);
    }
  }

  // Remove install directory only if uninstalling all
  if (!targetAgent) {
    const installDir = getInstallDir();
    if (fs.existsSync(installDir)) {
      fs.rmSync(installDir, { recursive: true, force: true });
    }
  }

  console.log();
  ui.success('M0² uninstalled.');
  console.log();
};
