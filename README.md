<div align="center">

<pre>
╭──────────────────────────────────────────────────────────────╮
│  🔴 🟡 🟢   ~/workspace — claude-code                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│    ███╗   ███╗ ██████╗ ══╗                                  │
│    ████╗ ████║██╔═══██╗╔═╝                                  │
│    ██╔████╔██║██║   ██║╚══   Universal AI Agent HUD         │
│    ██║╚██╔╝██║╚██████╔╝      v1.0.1  by haddad med          │
│    ╚═╝  ╚═╝  ╚═════╝                                       │
│                                                              │
├────────────────────────────── HUD preview ───────────────────┤
│                                                              │
│  [Pro]  claude-sonnet-4-5                      haddad med    │
│  Quota  [████████████░░░░░░░░] 62%  1h 40m / 5h  ↺ 3h 20m  │
│         [████░░░░░░░░░░░░░░░░] 18%  Ctx                     │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
</pre>

**Real-time token usage HUD for AI coding agents.**

[![npm](https://img.shields.io/npm/v/m0squared-indicator?color=00d4ff&label=npm&labelColor=0d1117&style=flat-square)](https://www.npmjs.com/package/m0squared-indicator)
[![downloads](https://img.shields.io/npm/dm/m0squared-indicator?color=00d4ff&label=downloads&labelColor=0d1117&style=flat-square)](https://www.npmjs.com/package/m0squared-indicator)
[![license](https://img.shields.io/badge/license-personal%20use-f59e0b?labelColor=0d1117&style=flat-square)](#license)
[![built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-7c3aed?labelColor=0d1117&style=flat-square)](https://claude.ai/code)

```bash
npx m0squared-indicator install
```

</div>

---

M0² installs a live HUD into your AI coding agent — quota remaining, context window usage, cost, and reset timer. Updated after every response. No dashboard. No guessing.

> *Start full. Watch it drain. Know when to stop.*

---

## The HUD

<pre>
  <b>── Pro · Max ─────────────────────────────────────────────</b>

  [Pro]  claude-sonnet-4-5                          haddad med
  Quota  [████████████░░░░░░░░] 62%  1h 40m / 5h 00m  ↺ 3h 20m
         [████░░░░░░░░░░░░░░░░] 18%  Ctx

  <b>── PAYG (API key) ────────────────────────────────────────</b>

  [PAYG]  claude-opus-4-5
  Cost  $0.0241  │  Ctx  [████████░░░░░░░░░░░░] 33%

  <b>── Free ──────────────────────────────────────────────────</b>

  [Free]  Ctx  [████░░░░░░░░░░░░░░░░░░░░] 14%
</pre>

**Quota** starts full and drains as your 5-hour limit is consumed.  
**Ctx** starts empty and fills as the conversation grows.  
Colors shift **green → yellow → red** as limits approach.

---

## Agents

| Agent | Integration |
|---|---|
| **Claude Code** | Native `statusLine` hook — live in the status bar |
| **Codex CLI** | `PostToolUse` hook — tracks every tool call |
| **Gemini CLI** | `AfterTool` hook — tracks every response |

---

## Install

```bash
# recommended — no install needed, just run
npx m0squared-indicator install

# npm
npm install -g m0squared-indicator && m0squared-indicator install

# pip
pip install m0squared-indicator && m0squared-indicator install

# curl (Linux / macOS)
curl -sSL https://raw.githubusercontent.com/m0squared/m0s-indicator/main/scripts/install.sh | bash

# PowerShell (Windows)
irm https://raw.githubusercontent.com/m0squared/m0s-indicator/main/scripts/install.ps1 | iex
```

Restart your agent after install to activate the HUD.

---

## Configure

Config file at `~/.m0squared/config.json` — created automatically on first install:

```json
{
  "plan":      "auto",
  "bar_width":  20,
  "username":   "",
  "codex":  { "session_token_limit": 100000 },
  "gemini": { "session_token_limit": 100000 }
}
```

| Key | Values | Default |
|---|---|---|
| `plan` | `auto` `pro` `max` `payg` `free` | `auto` |
| `bar_width` | integer | `20` |
| `username` | string | system `$USER` |

Plan is auto-detected from the agent's live response data. Set `"plan": "max"` manually if you're on Max.

---

## Commands

```
m0squared-indicator install             install for all detected agents
m0squared-indicator install --agent X   target one agent (claude-code, codex, gemini)
m0squared-indicator uninstall           remove from all agents
m0squared-indicator update              update to latest version
m0squared-indicator agents              list detected agents and status
m0squared-indicator status              print current HUD output
```

---

## Why M0²?

Built out of frustration — hitting the Claude Code token limit mid-session, with zero warning and no way to know how close you were.

M0² was born from a simple idea: *your tools should tell you when you're running out of fuel.*

> **Built by a Claude Code lover, with Claude Code.**  
> *— haddad med / morius*

---

## License

© 2026 morius (M-zero-Squared / haddad med). All rights reserved.

Free for personal use. No redistribution or commercial use without written permission.  
See [LICENSE](./LICENSE) for full terms.

---

<div align="center">

Made with ❤️ by **haddad med** · [github.com/m0squared](https://github.com/m0squared)

*If M0² saved your session — give it a ⭐*

</div>
