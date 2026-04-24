'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ui = require('../ui');
const { getInstallDir } = require('../detect');

module.exports = async function update() {
  ui.banner();
  ui.section('Updating M0²…\n');

  const installDir = getInstallDir();

  if (!fs.existsSync(installDir)) {
    ui.error('M0² is not installed. Run "npx m0squared install" first.');
    return;
  }

  // Copy fresh indicator.py
  try {
    const src = path.join(__dirname, '../../core/indicator.py');
    const dst = path.join(installDir, 'indicator.py');
    fs.copyFileSync(src, dst);
    fs.chmodSync(dst, '755');

    // Copy hook scripts
    for (const hookFile of ['codex-hook.py', 'gemini-hook.py']) {
      const hookSrc = path.join(__dirname, '../../core/hooks', hookFile);
      const hookDst = path.join(installDir, 'hooks', hookFile);
      if (fs.existsSync(hookSrc)) {
        fs.mkdirSync(path.dirname(hookDst), { recursive: true });
        fs.copyFileSync(hookSrc, hookDst);
        fs.chmodSync(hookDst, '755');
      }
    }

    ui.success('M0² updated to the latest version.');
    ui.tip('Restart your AI agents to apply the update.');
    console.log();
  } catch (e) {
    ui.error(`Update failed: ${e.message}`);
  }
};
