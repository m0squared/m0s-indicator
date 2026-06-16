# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**m0squared-indicator** is an npm package that installs a token usage HUD (heads-up display) into AI agent CLIs. It supports Claude Code, Codex CLI, and Gemini CLI.

The installed bin is `m0squared-indicator` (per `package.json` `bin`), entry point `bin/cli.js`. Note: user-facing tips in `src/ui.js` and command output say `npx m0squared` — that shorter name is not what the bin field registers.

## Commands

```bash
node bin/cli.js --help         # Show help (also the default for unknown commands)
node bin/cli.js agents         # Check agent detection + install status
node bin/cli.js install        # Run install flow (alias: i)
node bin/cli.js install --agent claude-code  # Install for one agent only
node bin/cli.js uninstall      # Remove from all agents (aliases: remove, u)
node bin/cli.js update         # Re-copy Python files to ~/.m0squared/
```

No build step — this is plain Node.js with zero runtime dependencies (no bundler, no transpilation). No test framework; `npm test` just runs `--help`.

A `postinstall` script auto-runs the install flow on **global** npm installs only (`npm_config_global` check in `src/commands/postinstall.js`).

## Architecture

### Two-language system

The project is split between **Node.js** (installer/CLI) and **Python** (the actual HUD runtime):

- **Node.js** (`bin/`, `src/`) — CLI that installs/uninstalls the HUD into agent configs
- **Python** (`core/`) — Scripts copied to `~/.m0squared/` at install time, then invoked by the agents at runtime. Changes to `core/*.py` only take effect for users after re-running install/update, since agents execute the *copies* in `~/.m0squared/`, not the repo files.

### Install flow

`src/commands/install.js` orchestrates the install:
1. Calls `src/detect.js` to check which agents are present (checks for `~/.claude`, `~/.codex`, `~/.gemini` dirs and CLI commands via `which`)
2. Copies `core/indicator.py` → `~/.m0squared/indicator.py`
3. Copies `core/hooks/codex-hook.py` and `gemini-hook.py` → `~/.m0squared/hooks/`
4. Copies `config.default.json` → `~/.m0squared/config.json` (only if not already present, so user edits survive updates)
5. Calls each agent module's `install(installDir)` to wire up agent-specific config

Agents already installed are skipped (idempotent re-runs).

### Per-agent integration

Each agent in `src/agents/` exports `isInstalled()`, `install(installDir)`, and `uninstall()`. Detection of "our" entries in agent config files is done by checking for the string `m0squared` in the command path.

- **Claude Code** (`src/agents/claude-code.js`): Writes `statusLine` key into `~/.claude/settings.json` (`python3 ~/.m0squared/indicator.py`). Claude Code pipes JSON session data to the script via stdin.
- **Codex** (`src/agents/codex.js`): Adds a `PostToolUse` hook under the `*` matcher in `~/.codex/hooks.json` and enables `codex_hooks = true` under `[features]` in `~/.codex/config.toml`. The hook script runs after each tool call.
- **Gemini** (`src/agents/gemini.js`): Similar hook-based approach into `~/.gemini/`.

### Python runtime

- **`core/indicator.py`** — Main HUD renderer. Reads JSON from stdin (Claude Code mode) or falls back to reading `~/.m0squared/{agent}-state.json` (Codex/Gemini mode). Renders a single ANSI-colored line: identity segment (agent badge · model · plan badge · username), then a quota bar (pro/max, from `rate_limits.five_hour`) or cost (payg), then a context-window bar.
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

Plan auto-detection (in `core/indicator.py`): if `rate_limits` present → pro; if `cost.total_cost_usd > 0` → payg; else → free. An optional `username` key overrides the `$USER` shown in the HUD.

### Publishing

`package.json` `files` field controls what ships: `bin/`, `src/`, `core/`, `config.default.json`, `LICENSE`. The `config.json` (local dev override) and `scripts/` are excluded via `.npmignore`.

Quirk: `package.json` lists `m0squared-indicator` (the package itself) as a dependency — a self-dependency that pulls the published version into `node_modules`. Don't confuse `node_modules/m0squared-indicator/` with the repo source.

## video/ — Remotion demo video (separate subproject, untracked)

`video/` is a standalone Remotion project (`m0squared-video`) that renders the LinkedIn demo video. It has its own `package.json` and is not part of the npm package.

```bash
cd video
npm run start    # Remotion studio at localhost:3333
npm run render   # Render M0SquaredVideo composition to out/m0squared.mp4
```

Caveat: its npm scripts use Windows path separators (`node_modules\.bin\remotion`); on Linux/WSL invoke `npx remotion ...` directly instead. `video/src/Root.tsx` registers two compositions — `M0SquaredVideo` (current V2) and `M0SquaredVideoV1` (original) — composed of scenes in `video/src/scenes/`.
