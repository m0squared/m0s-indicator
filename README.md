<div align="center">

<img src="https://github.com/m0squared/m0s-indicator/raw/main/assets/header.svg" alt="M0² — Universal AI Agent HUD" width="740">

### **M0²** — M-zero-Squared

*Real-time token usage indicator for AI coding agents*

---

[![npm](https://img.shields.io/npm/v/m0squared-indicator?color=cyan&label=npm)](https://www.npmjs.com/package/m0squared-indicator)
[![npm downloads](https://img.shields.io/npm/dm/m0squared-indicator?color=cyan&label=downloads%2Fmonth)](https://www.npmjs.com/package/m0squared-indicator)
[![npm downloads total](https://img.shields.io/npm/dt/m0squared-indicator?color=cyan&label=downloads%20total)](https://www.npmjs.com/package/m0squared-indicator)
[![license](https://img.shields.io/badge/license-MIT-green)](#license)
[![made with love](https://img.shields.io/badge/made%20with-%E2%9D%A4-red)](https://github.com/m0squared/m0s-indicator)
[![built by a Claude Code lover](https://img.shields.io/badge/built%20by-Claude%20Code%20lover-blueviolet)](https://claude.ai/code)

</div>

---

## What is M0²?

**M0²** is a live HUD that sits inside your AI coding agent and shows you exactly how much of your token quota you've consumed — in real time, right where you work.

No more getting cut off mid-task. No more opening dashboards. No more guessing.

> *Start full. Watch it drain. Know when to stop.*

<div align="center">
<img src="https://github.com/m0squared/m0s-indicator/raw/main/assets/demo.svg" alt="M0² HUD preview" width="620">
</div>

---

## Supported Agents

| Agent | Status | Integration |
|---|---|---|
| **Claude Code** | ✅ Full support | Native `statusLine` hook — live in the status bar |
| **Codex CLI** | ✅ Supported | `PostToolUse` hook — tracks every response |
| **Gemini CLI** | ✅ Supported | `AfterTool` hook — tracks every response |

> More agents coming. PRs welcome.

---

## Requirements

| | |
|---|---|
| **Node.js** | 16 or newer (for the installer) |
| **Python** | **3.10 or newer**, on your `PATH` (the HUD itself is a Python script) |
| **OS** | macOS, Linux, WSL, and native Windows (PowerShell or Git Bash) |

The installer checks for Python first and refuses to install without it — a HUD that can't run is worse than a clear error. On Windows, install Python from [python.org](https://www.python.org/downloads/windows/) (tick *"Add python.exe to PATH"*) or `winget install Python.Python.3.12`; the installer will pick `py -3`, `python` or `python3`, whichever actually works.

---

## Install

### npx *(recommended — no install needed)*
```bash
npx m0squared-indicator install
```

### npm
```bash
npm install -g m0squared-indicator
m0squared-indicator install
```

### curl *(Linux / macOS)*
```bash
curl -sSL https://raw.githubusercontent.com/m0squared/m0s-indicator/main/scripts/install.sh | bash
```

During install you pick the HUD layout with the arrow keys — **rows** (two lines) or **inline** (one line) — with a live preview of each. Use `--layout rows|inline` to skip the prompt, and `--agent claude-code|codex|gemini` to target one agent.

---

## How it works

M0² auto-detects which AI agents are installed on your machine and patches their config files silently. After a restart, the HUD appears automatically.

<div align="center">
<img src="https://github.com/m0squared/m0s-indicator/raw/main/assets/how-it-works.svg" alt="M0² install flow" width="580">
</div>

---

## Usage

<div align="center">
<img src="https://github.com/m0squared/m0s-indicator/raw/main/assets/usage.svg" alt="M0² commands" width="560">
</div>

---

## Configuration

After install, a config file is created at `~/.m0squared/config.json`:

<div align="center">
<img src="https://github.com/m0squared/m0s-indicator/raw/main/assets/config.svg" alt="M0² config.json" width="580">
</div>

| Key | Values | Description |
|---|---|---|
| `plan` | `auto` `pro` `max` `payg` `free` | Override plan auto-detection |
| `layout` | `rows` `inline` | HUD layout (chosen at install; edit here to change) |
| `bar_width` | number | Width of the quota bar (default: 20) |
| `username` / `email` | string | Override the identity shown |
| `show_email` / `show_effort` | boolean | Toggle the email and the `(effort)` suffix |
| `*.session_token_limit` | number | Token limit for Codex / Gemini sessions |

> **Auto-detection:** the plan tier is read from your Claude account (`~/.claude.json`), so Pro and Max are both detected. Set `plan` only to override.

---

## Uninstall

```bash
npx m0squared-indicator uninstall
```

This removes all hooks from your agent configs and deletes `~/.m0squared/`.

## Update

```bash
npx m0squared-indicator@latest update
```

Refreshes the HUD script and re-wires each installed agent (keeps your `config.json`).

---

## Why M0²?

Built out of pure love for [Claude Code](https://claude.ai/code) — and frustration with hitting token limits mid-session without any warning.

M0² was born from a simple idea: *your tools should tell you when you're running out of fuel.*

> **Built by a Claude Code lover, with Claude Code.**  
> *— haddad med / morius*

---

## License

MIT © 2026 [morius (M-zero-Squared / haddad med)](https://github.com/m0squared)

See [LICENSE](./LICENSE) for full terms.

---

<div align="center">

Made with ❤️ by **haddad med** · [github.com/m0squared](https://github.com/m0squared)

*If M0² saved your session — give it a ⭐*

</div>
