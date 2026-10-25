#!/usr/bin/env node
'use strict';

// © 2026 morius (M-zero-Squared). All rights reserved.
// Free for personal use. No redistribution without permission.
// https://github.com/m0squared/m0s-indicator

const args = process.argv.slice(2);
const ui = require('../src/ui');

// Parse --agent / --layout flags (both `--flag value` and `--flag=value`)
function flag(name) {
  const eq = args.find(a => a.startsWith(`--${name}=`));
  if (eq) return eq.slice(name.length + 3);
  const i = args.indexOf(`--${name}`);
  return i !== -1 && args[i + 1] ? args[i + 1] : null;
}
const agentFlag = flag('agent');
const layoutFlag = flag('layout');

const command = args.find(a => !a.startsWith('-') && a !== agentFlag && a !== layoutFlag);

const opts = { agent: agentFlag, layout: layoutFlag };

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
    const python = require('../src/python');
    const AGENTS = {
      'claude-code': require('../src/agents/claude-code'),
      'codex': require('../src/agents/codex'),
      'gemini': require('../src/agents/gemini'),
    };
    ui.banner();
    const py = python.findPython();
    ui.section('Requirements:\n');
    if (py.argv) ui.info(`Python ${py.version.join('.')}  ${ui.DIM}(${py.argv.join(' ')})${ui.R}`);
    else { ui.error('Python not found'); for (const l of python.requirementMessage(py)) ui.tip(l); }
    console.log();
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
    console.log(`m0squared-indicator v${pkg.version}`);
    break;
  }

  case '--help':
  case '-h':
  case 'help':
  default:
    ui.showHelp();
    break;
}
