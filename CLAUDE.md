# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**m0squared-indicator** is an npm package (`m0squared-indicator`) that installs a token usage HUD (heads-up display) into AI agent CLIs. It supports Claude Code, Codex CLI, and Gemini CLI.

Published via `npx m0squared <command>`. Entry point: `bin/cli.js`.

## Commands

```bash
node bin/cli.js --help         # Verify CLI works
node bin/cli.js agents         # Check agent detection
node bin/cli.js install        # Run install flow
node bin/cli.js install --agent claude-code  # Install for one agent only
```

No build step — this is plain Node.js (no bundler, no transpilation). No test framework; `npm test` just runs `--help`.

## Architecture

### Two-language system

The project is split between **Node.js** (installer/CLI) and **Python** (the actual HUD runtime):

- **Node.js** (`bin/`, `src/`) — CLI that installs/uninstalls the HUD into agent configs
- **Python** (`core/`) — Scripts copied to `~/.m0squared/` at install time, then invoked by the agents at runtime

### Install flow

`src/commands/install.js` orchestrates the install:
1. Calls `src/detect.js` to check which agents are present (checks for `~/.claude`, `~/.codex`, `~/.gemini` dirs and CLI commands)
2. Copies `core/indicator.py` → `~/.m0squared/indicator.py`
3. Copies `core/hooks/codex-hook.py` and `gemini-hook.py` → `~/.m0squared/hooks/`
4. Copies `config.default.json` → `~/.m0squared/config.json` (only if not already present)
5. Calls each agent module's `install(installDir)` to wire up agent-specific config

### Per-agent integration

Each agent in `src/agents/` has `isInstalled()`, `install(installDir)`, and `uninstall()`:

- **Claude Code** (`src/agents/claude-code.js`): Writes `statusLine` key into `~/.claude/settings.json`. Claude Code calls `indicator.py` via stdin (passes JSON data directly).
- **Codex** (`src/agents/codex.js`): Adds a `PostToolUse` hook to `~/.codex/hooks.json` and enables `codex_hooks = true` in `~/.codex/config.toml`. The hook script runs after each tool call.
- **Gemini** (`src/agents/gemini.js`): Similar hook-based approach into `~/.gemini/`.

### Python runtime

- **`core/indicator.py`** — Main HUD renderer. Reads JSON from stdin (Claude Code mode) or falls back to reading `~/.m0squared/{agent}-state.json` (Codex/Gemini mode). Renders ANSI-colored progress bars.
- **`core/hooks/codex-hook.py`** — Codex PostToolUse hook: reads the JSONL transcript, sums token usage, writes state to `~/.m0squared/codex-state.json`.
- **`core/hooks/gemini-hook.py`** — Same pattern for Gemini.
- **`token_indicator.py`** — Standalone legacy/alternative version of the indicator (Claude Code only, reads from stdin). Kept for reference; `core/indicator.py` is the deployed version.

### Configuration

`~/.m0squared/config.json` (installed from `config.default.json`):
```json
{
  "plan": "auto",          // "auto", "pro", "max", "payg", "free"
  "bar_width": 20,
  "codex": { "session_token_limit": 100000 },
  "gemini": { "session_token_limit": 100000 }
}
```

Plan auto-detection: if `rate_limits` present → pro; if `cost.total_cost_usd > 0` → payg; else → free.

### Publishing

`package.json` `files` field controls what ships: `bin/`, `src/`, `core/`, `config.default.json`, `LICENSE`. The `config.json` (local dev override) and `scripts/` are excluded via `.npmignore`.
