'use strict';

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
${BOLD}${WHITE}  ██║╚██╔╝██║╚██████╔╝${R}      ${DIM}v1.0.1  by haddad med${R}
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
  console.log(`  ${BOLD}Usage:${R}  npx m0squared <command>\n`);
  console.log(`  ${BOLD}Commands:${R}`);
  console.log(`    ${CYAN}install${R}     Install M0² for all detected AI agents`);
  console.log(`    ${CYAN}uninstall${R}   Remove M0² from all agents`);
  console.log(`    ${CYAN}update${R}      Update to the latest version`);
  console.log(`    ${CYAN}status${R}      Show current token usage in terminal`);
  console.log(`    ${CYAN}agents${R}      List supported agents and their status`);
  console.log(`\n  ${BOLD}Options:${R}`);
  console.log(`    ${CYAN}--agent${R}     Target a specific agent (claude-code, codex, gemini)`);
  console.log(`\n  ${DIM}Examples:${R}`);
  console.log(`    npx m0squared install`);
  console.log(`    npx m0squared install --agent claude-code`);
  console.log(`    npx m0squared status\n`);
}

module.exports = { banner, section, agentLine, success, error, info, tip, showHelp, BOLD, DIM, GREEN, CYAN, YELLOW, RED, R };
