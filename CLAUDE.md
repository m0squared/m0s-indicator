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
node bin/cli.js install --layout inline      # Skip the arrow-key layout picker (rows|inline)
node bin/cli.js uninstall      # Remove from all agents + delete ~/.m0squared/ (aliases: remove, u)
node bin/cli.js update         # Re-copy Python files AND re-wire every installed agent
```

No build step — this is plain Node.js with zero runtime dependencies (no bundler, no transpilation). No test framework and no linter; `npm test` just runs `--help`.

**These commands mutate the real home directory** (`~/.claude/settings.json`, `~/.codex/`, `~/.gemini/`, `~/.m0squared/`). `uninstall` without `--agent` deletes `~/.m0squared/` including the user's `config.json`. To test safely, point `HOME` (Linux/macOS) or `USERPROFILE` (Windows) at a throwaway directory containing empty `.claude/`, `.codex/`, `.gemini/` folders; detection only needs those dirs to exist.

### Testing the Windows path from WSL

Windows Node and Python are reachable from WSL, so the native-Windows behaviour can be exercised without leaving WSL: write a `.ps1` under `%LOCALAPPDATA%\Temp`, set `$env:USERPROFILE` to a fake profile, run `node <repo>\bin\cli.js install --layout rows`, then feed a payload to the written command via `powershell -Command "<cmd>"` and `"C:\Program Files\Git\bin\bash.exe" -c "<cmd>"` — those are the two shells Claude Code uses on Windows (Git Bash when installed, PowerShell otherwise).

### Testing the HUD renderer without installing

Pipe a fake Claude Code statusLine payload straight into the repo copy:

```bash
echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":42},"rate_limits":{"five_hour":{"used_percentage":30,"resets_at":'$(($(date +%s)+7200))'}}}' | python3 core/indicator.py
```

The script still reads the *installed* `~/.m0squared/config.json` (layout, plan override, etc.) plus `~/.claude.json` and `~/.claude/settings.json` — the repo-root `config.json` is not read by `core/indicator.py` (only by the legacy `token_indicator.py`, which loads it from its own directory). To test the hooks, pipe `{"transcript_path": "..."}` into `core/hooks/*-hook.py`; they write `~/.m0squared/{agent}-state.json`.

`core/indicator.py` uses `float | None` annotations evaluated at definition time, so it needs **Python ≥ 3.10**.

### Releasing

Versions are bumped with `npm version patch` (produces the bare `1.0.x` commits + tags), then `npm publish`. Other commits follow conventional-commit style (`feat(inline): …`, `style(rows): …`, `docs(readme): …`).

A `postinstall` script auto-runs the install flow on **global** npm installs only (`npm_config_global` check in `src/commands/postinstall.js`). It exits 1 (failing the npm install) when no Python ≥ 3.10 is found. There is no TTY in that context, so the layout picker silently defaults to `rows`.

### Python requirement and resolution (`src/python.js`)

The HUD is a Python script, so `install`, `update` and `postinstall` all refuse to proceed unless `findPython()` locates an interpreter ≥ 3.10 (`MIN_VERSION`). It **executes** candidates rather than checking PATH, because on Windows `python3` is frequently a Microsoft Store stub that exits silently. Candidates: Windows `py -3` → `python` → `python3`; elsewhere `python3` → `python`. The first one that satisfies the floor wins, and its **bare launcher name** (not the absolute interpreter path) is written into agent configs as `py -3 "C:/Users/x/.m0squared/indicator.py"`:

- Forward slashes because Git Bash strips unquoted backslashes (verified: the old `python3 C:\Users\…` form fails under Git Bash).
- Bare name because PowerShell treats a command string that *starts* with a quoted path as a string expression, not a command.
- Quoted path so profiles with spaces work.

Changing `MIN_VERSION` is only safe if `core/*.py` stays compatible (`indicator.py` uses `float | None` annotations → 3.10).

## Architecture

### Two-language system

The project is split between **Node.js** (installer/CLI) and **Python** (the actual HUD runtime):

- **Node.js** (`bin/`, `src/`) — CLI that installs/uninstalls the HUD into agent configs
- **Python** (`core/`) — Scripts copied to `~/.m0squared/` at install time, then invoked by the agents at runtime. Changes to `core/*.py` only take effect after running `update`, since agents execute the *copies* in `~/.m0squared/`, not the repo files.

### Install flow

`src/commands/install.js` orchestrates the install:
1. `requirePython()` — aborts with install instructions if no Python ≥ 3.10 (see above)
2. Calls `src/detect.js` to check which agents are present (checks for `~/.claude`, `~/.codex`, `~/.gemini` dirs and a pure-Node PATH lookup of the CLI commands — no `which`, so it works on Windows)
3. Builds the list of agents that are detected but not yet installed. **If that list is empty it returns early — no files are copied.** Re-running `install` therefore does not refresh the Python files; that is what `update` is for.
4. `copyCoreFiles()` copies `core/indicator.py` → `~/.m0squared/indicator.py` and `core/hooks/*.py` → `~/.m0squared/hooks/`
5. Copies `config.default.json` → `~/.m0squared/config.json` (only if not already present, so user edits survive)
6. Arrow-key layout picker (`src/layout-picker.js`: raw-mode readline, live preview of `rows` vs `inline`, ↑/↓/j/k/1/2, Enter) unless `--layout` was passed or there is no TTY (→ `rows`). Merges just the `layout` key into the installed config.
7. Calls each agent module's `install(installDir)` to wire up agent-specific config

`update` re-copies the Python files **and re-runs `install()` for every agent that reports `isInstalled()`**, so the command strings get re-resolved (this is how a pre-1.1 Windows install with a literal `python3` gets repaired). It never touches `config.json`. New config keys therefore never reach existing users' configs — every key read in Python must have an in-code default (`config.get(key, default)`).

### Per-agent integration

Each agent in `src/agents/` exports `isInstalled()`, `install(installDir)`, and `uninstall()`, returning `{ ok, error? }`. Detection of "our" entries in agent config files is done by checking for the string `m0squared` in the command path. The agent registry (`AGENTS` map) is duplicated in `bin/cli.js`, `src/commands/install.js`, and `src/commands/uninstall.js` — adding an agent means touching all three plus `src/detect.js`, `src/ui.js`, and `scripts/install.sh`.

- **Claude Code** (`src/agents/claude-code.js`): Writes `statusLine` key into `~/.claude/settings.json` (`python3 ~/.m0squared/indicator.py`), overwriting any existing statusLine. Claude Code pipes JSON session data to the script via stdin.
- **Codex** (`src/agents/codex.js`): Adds a `PostToolUse` hook under the `*` matcher in `~/.codex/hooks.json` and enables `codex_hooks = true` under `[features]` in `~/.codex/config.toml` (string-patched, not TOML-parsed). `PostToolUse` is an object keyed by matcher, and `isInstalled()` scans every matcher's list.
- **Gemini** (`src/agents/gemini.js`): Pushes an `AfterTool` entry (`matcher: '.*'`, hook named `m0squared-tracker`) into `hooks` in `~/.gemini/settings.json`.

`scripts/install.sh` (the curl installer, Linux/macOS only) is an independent bash/Python reimplementation of all of the above, and downloads `core/` files from the **`main` branch** on GitHub — so pushes to `main` reach curl users immediately, without an npm release. Keep it in sync when changing agent wiring (it enforces the same Python ≥ 3.10 floor but always writes `python3`). It is excluded from the npm package.

### Python runtime

- **`core/indicator.py`** — Main HUD renderer. Reads JSON from stdin (Claude Code mode) or falls back to reading `~/.m0squared/{agent}-state.json` (Codex first, then Gemini). All failures are swallowed — on bad input it prints nothing rather than erroring into the status bar. Because of that, the scripts force `sys.stdout`/`sys.stdin` to UTF-8 at import time: on Windows a piped stdout defaults to cp1252, `↺ █ ░ │` raise `UnicodeEncodeError`, and the swallowed exception used to produce an empty status line (the "installs fine, shows nothing" bug). Two layouts, selected by config `layout`:
  - `rows` (default) — line 1: `[Plan]` badge, model `(effort)`, and on the right the 5h-window elapsed/reset time (pro/max) or else email/username; blank line; line 2: quota bar `│` context bar.
  - `inline` — single line: model · plan · username `│` quota bar with reset time only `│` context bar. This branch is self-contained inside `render()` and does not use `build_bars()`; changes to bar rendering must be made in both places.

  The quota bar shows *remaining* (drains, green→red as it empties); the context bar shows *used* (fills, green→red as it fills) — hence the separate `color_remaining`/`color_used`. For Claude Code only, it also reads `~/.claude.json` (`oauthAccount` → plan tier, email) and `~/.claude/settings.json` (`effortLevel` fallback).
- **`core/hooks/codex-hook.py`** / **`gemini-hook.py`** — Read `transcript_path` from the hook's stdin JSON, sum token usage over the JSONL transcript, and write a state file shaped like a Claude Code statusLine payload (`_agent`, `context_window.used_percentage`, `cost`). "Context %" for these agents is total tokens ÷ `session_token_limit` from config, not a real context-window measurement. The Codex hook must print `{"continue": true}`; the Gemini hook just exits 0.
- **`token_indicator.py`** — Standalone legacy version of the indicator (Claude Code only). Kept for reference; not shipped.

### Configuration

`~/.m0squared/config.json` (installed from `config.default.json`):

| Key | Default | Meaning |
|---|---|---|
| `plan` | `"auto"` | `auto`, `pro`, `max`, `payg`, `free` |
| `layout` | `"rows"` | `rows` or `inline` |
| `bar_width` | `20` | Quota bar width; context bar is 75% of it (min 10) |
| `username` / `email` | `""` | Override `$USER` / the `~/.claude.json` account email |
| `show_email` | `true` | `rows` layout fallback identity: email vs username |
| `show_effort` | `true` | Append `(effort)` after the model name |
| `codex.session_token_limit`, `gemini.session_token_limit` | `100000` | Denominator for those agents' context bar |

Plan auto-detection (`detect_plan`): config override → `organizationType`/`organizationRateLimitTier` in `~/.claude.json` containing `max` or `pro` → `rate_limits` present ⇒ pro → `cost.total_cost_usd > 0` ⇒ payg → free.

### Docs vs. reality

- `assets/config.svg`, `assets/install.svg` and `assets/usage.svg` predate the `layout`/`show_*`/`email` keys, the layout picker and the `--layout` flag.
- README images are standalone SVGs in `assets/` referenced by absolute `github.com/.../raw/main/` URLs (so they render on npm); HUD appearance changes may warrant updating `assets/demo.svg`.
- The installer banner/tips call the product "M0²"; the brand is M0² and the product is "M0² Indicator" (see `brag-output-*/`).

### Line endings

Most files are committed with CRLF (Windows checkout, no `core.autocrlf`). `.gitattributes` forces `*.sh` and `*.py` to LF: a CRLF `scripts/install.sh` made the published `curl … | bash` installer fail with `syntax error near unexpected token $'{\r'`, and CRLF corrupts `#!` lines. When editing from WSL, don't let a tool silently rewrite a CRLF file as LF — the diff becomes a whole-file rewrite. Check with `file <path>` and compare against `git diff --stat --ignore-cr-at-eol`.

### Publishing

`package.json` `files` field controls what ships: `bin/`, `src/`, `core/`, `config.default.json`, `LICENSE`. The repo-root `config.json`, `token_indicator.py`, `scripts/`, and `assets/` are excluded via `.npmignore`.

Quirk: `package.json` lists `m0squared-indicator` (the package itself) as a dependency — a self-dependency that pulls the published version into `node_modules`. Don't confuse `node_modules/m0squared-indicator/` with the repo source.

## Untracked tooling folders

`.agents/`, `.claude/`, `.bob/`, `.aider-desk/`, `skills-lock.json` (installed agent skills), `brag/` (a clone of the skill's repo), `brag-output*/` (rendered launch videos + their Hyperframes source) and `video/` are git-ignored working material, not part of the package.

## video/ — Remotion demo video (separate subproject, untracked)

`video/` is a standalone Remotion project (`m0squared-video`) that renders the LinkedIn demo video. It has its own `package.json` and is not part of the npm package.

```bash
cd video
npm run start    # Remotion studio at localhost:3333
npm run render   # Render M0SquaredVideo composition to out/m0squared.mp4
```

Caveat: its npm scripts use Windows path separators (`node_modules\.bin\remotion`); on Linux/WSL invoke `npx remotion ...` directly instead. `video/src/Root.tsx` registers two compositions — `M0SquaredVideo` (current V2) and `M0SquaredVideoV1` (original) — composed of scenes in `video/src/scenes/`.
