#!/usr/bin/env node
'use strict';

// © 2026 morius (M-zero-Squared). All rights reserved.
// Free for personal use. No redistribution without permission.
// https://github.com/m0squared/m0squared

const args = process.argv.slice(2);
const ui = require('../src/ui');

// Parse --agent flag
let agentFlag = null;
const agentIdx = args.indexOf('--agent');
if (agentIdx !== -1 && args[agentIdx + 1]) {
  agentFlag = args[agentIdx + 1];
}

const command = args.find(a => !a.startsWith('-') && a !== agentFlag);

const opts = { agent: agentFlag };

switch (command) {
  case 'install':
  case 'i':
    require('../src/commands/install')(opts).catch(e => {
      ui.error(e.message);
      process.exit(1);
    });
    break;

  case 'uninstall':
  case 'remove':
  case 'u':
    require('../src/commands/uninstall')(opts).catch(e => {
      ui.error(e.message);
      process.exit(1);
    });
    break;

  case 'update':
    require('../src/commands/update')(opts).catch(e => {
      ui.error(e.message);
      process.exit(1);
    });
    break;

  case 'agents': {
    const { detectAll } = require('../src/detect');
    const AGENTS = {
      'claude-code': require('../src/agents/claude-code'),
      'codex': require('../src/agents/codex'),
      'gemini': require('../src/agents/gemini'),
    };
    ui.banner();
    ui.section('Agent status:\n');
    const detected = detectAll();
    for (const [name, agent] of Object.entries(AGENTS)) {
      if (!detected[name]) {
        ui.agentLine(name, 'missing');
      } else if (agent.isInstalled()) {
        ui.agentLine(name, 'found', 'M0² installed');
      } else {
        ui.agentLine(name, 'found', 'M0² not installed');
      }
    }
    console.log();
    break;
  }

  case '--version':
  case '-v':
  case 'version': {
    const pkg = require('../package.json');
    console.log(`m0squared v${pkg.version}`);
    break;
  }

  case '--help':
  case '-h':
  case 'help':
  default:
    ui.showHelp();
    break;
}
