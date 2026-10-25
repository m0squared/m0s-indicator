'use strict';

// Locate a usable Python interpreter once, at install time, and produce the
// command string the agents will run at runtime.
//
// Why probe instead of hard-coding "python3":
//  - On Windows `python3` is often a Microsoft Store stub that exits silently.
//  - python.org installs register `py` (launcher) and `python`, not `python3`.
//  - core/indicator.py needs Python >= 3.10 (PEP 604 `X | None` annotations).
//
// The command we write into agent configs uses the *bare* launcher name
// (e.g. `py -3`), not the absolute interpreter path: Claude Code on Windows
// runs the status line through Git Bash when present and PowerShell otherwise,
// and PowerShell treats a command that starts with a quoted path as a string
// expression, not a command. A bare name works in bash, cmd and PowerShell.

const { spawnSync } = require('child_process');

const MIN_VERSION = [3, 10];
const IS_WIN = process.platform === 'win32';

const CANDIDATES = IS_WIN
  ? [['py', '-3'], ['python'], ['python3']]
  : [['python3'], ['python']];

const PROBE = 'import sys;print(sys.version_info[0],sys.version_info[1],sys.executable)';

function probe(argv) {
  const res = spawnSync(argv[0], [...argv.slice(1), '-c', PROBE], {
    encoding: 'utf8',
    timeout: 8000,
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (res.error || res.status !== 0 || !res.stdout) return null;
  const [maj, min, ...rest] = res.stdout.trim().split(' ');
  const version = [Number(maj), Number(min)];
  if (!Number.isInteger(version[0]) || !Number.isInteger(version[1])) return null;
  return { argv, version, executable: rest.join(' ') };
}

let cached;

// Returns { argv, version, executable } for the first interpreter that meets
// MIN_VERSION, or { argv:null, found:[...] } describing what was found instead.
function findPython() {
  if (cached) return cached;
  const found = [];
  for (const argv of CANDIDATES) {
    const p = probe(argv);
    if (!p) continue;
    found.push(p);
    if (p.version[0] > MIN_VERSION[0] ||
        (p.version[0] === MIN_VERSION[0] && p.version[1] >= MIN_VERSION[1])) {
      cached = { ...p, found };
      return cached;
    }
  }
  cached = { argv: null, found };
  return cached;
}

// Forward slashes work in bash, cmd and PowerShell; backslashes are eaten by
// Git Bash as escape characters.
function toPortablePath(p) {
  return p.replace(/\\/g, '/');
}

function commandFor(scriptPath, python = findPython()) {
  if (!python.argv) throw new Error('No suitable Python interpreter found');
  return `${python.argv.join(' ')} "${toPortablePath(scriptPath)}"`;
}

function requirementMessage(python = findPython()) {
  const need = `Python ${MIN_VERSION.join('.')}+`;
  const lines = [];
  if (python.found.length) {
    const seen = python.found.map(p => `${p.argv.join(' ')} → ${p.version.join('.')}`).join(', ');
    lines.push(`${need} is required, but only found: ${seen}.`);
  } else {
    lines.push(`${need} is required, but no Python interpreter was found on your PATH.`);
  }
  if (IS_WIN) {
    lines.push('Install it from https://www.python.org/downloads/windows/ (tick "Add python.exe to PATH")');
    lines.push('or run:  winget install Python.Python.3.12');
  } else if (process.platform === 'darwin') {
    lines.push('Install it with:  brew install python3');
  } else {
    lines.push('Install it with your package manager, e.g.:  sudo apt install python3');
  }
  lines.push('Then open a new terminal and run the install again.');
  return lines;
}

module.exports = { MIN_VERSION, findPython, commandFor, toPortablePath, requirementMessage };
