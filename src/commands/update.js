'use strict';

const fs = require('fs');

const ui = require('../ui');
const { getInstallDir } = require('../detect');
const { copyCoreFiles, requirePython, AGENTS } = require('./install');

// Refresh the Python runtime and rewrite each installed agent's command so an
// older install (e.g. one that hard-coded `python3`) picks up the new
// interpreter resolution. Agent install() is idempotent; config.json is left alone.
module.exports = async function update() {
  ui.banner();
  ui.section('Updating M0²…\n');

  const installDir = getInstallDir();

  if (!fs.existsSync(installDir)) {
    ui.error('M0² is not installed. Run "npx m0squared-indicator install" first.');
    process.exitCode = 1;
    return;
  }

  if (!requirePython()) return;
  console.log();

  try {
    copyCoreFiles(installDir);
  } catch (e) {
    ui.error(`Update failed: ${e.message}`);
    process.exitCode = 1;
    return;
  }

  let refreshed = 0;
  for (const [name, agent] of Object.entries(AGENTS)) {
    if (!agent.isInstalled()) continue;
    ui.agentLine(name, 'installing');
    try {
      const result = agent.install(installDir);
      if (result.ok) { ui.agentLine(name, 'done'); refreshed++; }
      else ui.agentLine(name, 'error', result.error || 'unknown error');
    } catch (e) {
      ui.agentLine(name, 'error', e.message);
    }
  }

  ui.success(`M0² updated (${refreshed} agent${refreshed === 1 ? '' : 's'} refreshed).`);
  ui.tip('Restart your AI agents to apply the update.');
  console.log();
};
