'use strict';

const pkg = require('../package.json');

const R = '\x1b[0m';
const BOLD = '\x1b[1m';
const DIM = '\x1b[2m';
const GREEN = '\x1b[32m';
const CYAN = '\x1b[36m';
const YELLOW = '\x1b[33m';
const RED = '\x1b[31m';
const WHITE = '\x1b[37m';

const AGENT_COLORS = {
  'claude-code': CYAN,
  'codex': '\x1b[35m',   // magenta
  'gemini': '\x1b[34m',  // blue
};

function banner() {
  console.log(`
${BOLD}${WHITE}  ███╗   ███╗ ██████╗${R}${BOLD}${CYAN} ══╗${R}
${BOLD}${WHITE}  ████╗ ████║██╔═══██╗${R}${BOLD}${CYAN}╔═╝${R}
${BOLD}${WHITE}  ██╔████╔██║██║   ██║${R}${BOLD}${CYAN}╚══${R}  ${DIM}Universal AI Agent HUD${R}
${BOLD}${WHITE}  ██║╚██╔╝██║╚██████╔╝${R}      ${DIM}v${pkg.version}  by haddad med${R}
${BOLD}${WHITE}  ╚═╝  ╚═╝  ╚═════╝${R}
`);
}

function section(text) {
  console.log(`  ${DIM}${text}${R}`);
}

function agentLine(name, status, detail = '') {
  const c = AGENT_COLORS[name] || WHITE;
  const label = name.padEnd(14);
  if (status === 'found') {
    console.log(`  ${GREEN}✓${R}  ${BOLD}${c}${label}${R}  ${DIM}detected${R}  ${detail}`);
  } else if (status === 'missing') {
    console.log(`  ${DIM}✗  ${label}  not found${R}`);
  } else if (status === 'installing') {
    process.stdout.write(`  ${YELLOW}→${R}  ${BOLD}${c}${label}${R}  `);
  } else if (status === 'done') {
    console.log(`${GREEN}done${R}`);
  } else if (status === 'error') {
    console.log(`${RED}failed — ${detail}${R}`);
  } else if (status === 'skip') {
    console.log(`  ${DIM}⊘  ${label}  already installed${R}`);
  }
}

function success(text) {
  console.log(`\n  ${GREEN}${BOLD}✓${R}  ${text}\n`);
}

function error(text) {
  console.log(`\n  ${RED}${BOLD}✗${R}  ${text}\n`);
}

function info(text) {
  console.log(`  ${CYAN}i${R}  ${text}`);
}

function tip(text) {
  console.log(`  ${DIM}${text}${R}`);
}

function showHelp() {
  banner();
  console.log(`  ${BOLD}Usage:${R}  npx m0squared-indicator <command>\n`);
  console.log(`  ${BOLD}Commands:${R}`);
  console.log(`    ${CYAN}install${R}     Install M0² for all detected AI agents`);
  console.log(`    ${CYAN}uninstall${R}   Remove M0² from all agents`);
  console.log(`    ${CYAN}update${R}      Refresh the HUD files and agent wiring`);
  console.log(`    ${CYAN}agents${R}      Show requirements, supported agents and their status`);
  console.log(`\n  ${BOLD}Options:${R}`);
  console.log(`    ${CYAN}--agent${R}     Target a specific agent (claude-code, codex, gemini)`);
  console.log(`    ${CYAN}--layout${R}    Skip the picker: rows | inline`);
  console.log(`\n  ${BOLD}Requires:${R}  Node.js 16+ and Python 3.10+ on your PATH`);
  console.log(`  ${DIM}Works on macOS, Linux, WSL and native Windows (PowerShell / Git Bash).${R}`);
  console.log(`\n  ${DIM}Examples:${R}`);
  console.log(`    npx m0squared-indicator install`);
  console.log(`    npx m0squared-indicator install --agent claude-code --layout inline\n`);
}

module.exports = { banner, section, agentLine, success, error, info, tip, showHelp, BOLD, DIM, GREEN, CYAN, YELLOW, RED, R };
