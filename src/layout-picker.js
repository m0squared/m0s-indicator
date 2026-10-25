'use strict';

const readline = require('readline');
const ui = require('./ui');

const { BOLD, DIM, GREEN, CYAN, YELLOW, R } = ui;
const MAG = '\x1b[35m';

// What each layout looks like, using the same glyphs core/indicator.py prints.
const PREVIEWS = {
  rows: [
    `${BOLD}${MAG}[Max]${R}  ${DIM}Opus 4.8 (high)${R}   ${DIM}1h 52m / 5h 00m  ↺ 3h 07m${R}`,
    ``,
    `Quota ${GREEN}[████████████░░░░░░░░] 62%${R}  ${DIM}│${R}  Ctx ${GREEN}[███░░░░░░░░░░░░] 18%${R}`,
  ],
  inline: [
    `${DIM}Opus 4.8 (high)${R}  ${DIM}·${R}  ${BOLD}${MAG}Max${R}  ${DIM}·${R}  ${DIM}you${R}  ${DIM}│${R}  Quota ${GREEN}[████████████░░░░░░░░] 62%${R}  ${DIM}↺ 3h 07m${R}  ${DIM}│${R}  Ctx ${GREEN}[███░░░░░░░░░░░░] 18%${R}`,
  ],
};

const OPTIONS = [
  { id: 'rows',   label: 'rows',   hint: 'two lines — identity on top, bars below (default)' },
  { id: 'inline', label: 'inline', hint: 'one compact line' },
];

function render(selected) {
  const out = [];
  out.push(`  ${DIM}Choose the HUD layout  ${R}${DIM}(↑/↓ to move, Enter to confirm)${R}`);
  out.push('');
  OPTIONS.forEach((opt, i) => {
    const on = i === selected;
    const marker = on ? `${CYAN}❯${R}` : ' ';
    const name = on ? `${BOLD}${CYAN}${opt.label.padEnd(7)}${R}` : `${opt.label.padEnd(7)}`;
    out.push(`  ${marker} ${name} ${DIM}${opt.hint}${R}`);
    const box = on ? CYAN : DIM;
    out.push(`      ${box}┌${'─'.repeat(70)}${R}`);
    for (const line of PREVIEWS[opt.id]) out.push(`      ${box}│${R}  ${line}`);
    out.push(`      ${box}└${'─'.repeat(70)}${R}`);
    out.push('');
  });
  return out;
}

// Interactive arrow-key picker. Resolves to 'rows' | 'inline'.
// Falls back to the default when there is no TTY (postinstall, CI, pipes).
function pickLayout(defaultLayout = 'rows') {
  if (!process.stdin.isTTY || !process.stdout.isTTY) return Promise.resolve(defaultLayout);

  return new Promise((resolve) => {
    let selected = Math.max(0, OPTIONS.findIndex(o => o.id === defaultLayout));
    let lines = 0;

    const draw = () => {
      if (lines) {
        readline.moveCursor(process.stdout, 0, -lines);
        readline.clearScreenDown(process.stdout);
      }
      const block = render(selected);
      process.stdout.write(block.join('\n') + '\n');
      lines = block.length;
    };

    readline.emitKeypressEvents(process.stdin);
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdout.write('\x1b[?25l'); // hide cursor

    const finish = (value) => {
      process.stdin.setRawMode(false);
      process.stdin.pause();
      process.stdin.removeListener('keypress', onKey);
      process.stdout.write('\x1b[?25h');
      if (value === null) {
        process.stdout.write('\n');
        process.exit(130);
      }
      readline.moveCursor(process.stdout, 0, -lines);
      readline.clearScreenDown(process.stdout);
      console.log(`  ${GREEN}✓${R}  Layout: ${BOLD}${value}${R}\n`);
      resolve(value);
    };

    const onKey = (str, key) => {
      if (!key) return;
      if (key.ctrl && key.name === 'c') return finish(null);
      if (key.name === 'up' || key.name === 'k' || str === '1') selected = 0;
      else if (key.name === 'down' || key.name === 'j' || str === '2') selected = OPTIONS.length - 1;
      else if (key.name === 'return' || key.name === 'space') return finish(OPTIONS[selected].id);
      else return;
      draw();
    };

    process.stdin.on('keypress', onKey);
    draw();
  });
}

module.exports = { pickLayout, OPTIONS, PREVIEWS };
