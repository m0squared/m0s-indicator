#!/usr/bin/env python3
# © 2026 morius (M-zero-Squared). All rights reserved.
# https://github.com/m0squared/m0squared
"""
M0² — Universal AI Agent HUD
Status line script: receives JSON from stdin (Claude Code statusLine mode)
or reads state file (Codex / Gemini mode).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

M0SQ_DIR   = Path.home() / ".m0squared"
CONFIG_FILE = M0SQ_DIR / "config.json"

# ── ANSI ──────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}

# ── Rendering helpers ─────────────────────────────────────────────────────────

def bar(pct: float | None, width: int) -> str:
    if pct is None:
        return "[" + "?" * width + "]"
    filled = min(width, max(0, round(width * pct / 100)))
    return "[" + "█" * filled + "░" * (width - filled) + "]"

def color(pct: float | None) -> str:
    if pct is None: return DIM
    if pct >= 80:   return RED
    if pct >= 50:   return YELLOW
    return GREEN

def fmt_pct(pct: float | None) -> str:
    return f"{pct:.0f}%" if pct is not None else "?%"

def time_until(ts: float) -> str:
    remaining = ts - datetime.now(timezone.utc).timestamp()
    if remaining <= 0: return "resetting…"
    h = int(remaining // 3600)
    m = int((remaining % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"

BADGES = {
    "pro":  (CYAN,   "Pro"),
    "max":  (BOLD,   "Max"),
    "payg": (YELLOW, "PAYG"),
    "free": (DIM,    "Free"),
}

def badge(plan: str) -> str:
    c, label = BADGES.get(plan, (DIM, plan.upper()))
    return f"{BOLD}{c}[{label}]{RESET}"

AGENT_BADGES = {
    "claude-code": f"{CYAN}Claude{RESET}",
    "codex":       f"\033[35mCodex{RESET}",
    "gemini":      f"\033[34mGemini{RESET}",
}

def detect_plan(data: dict, config: dict) -> str:
    user_plan = config.get("plan", "auto").lower()
    if user_plan != "auto":
        return user_plan
    if data.get("rate_limits"):
        return "pro"
    cost = (data.get("cost") or {}).get("total_cost_usd", 0)
    if cost and float(cost) > 0:
        return "payg"
    return "free"

# ── Render ────────────────────────────────────────────────────────────────────

def render(data: dict, config: dict) -> None:
    plan   = detect_plan(data, config)
    width  = int(config.get("bar_width", 20))
    ctx    = data.get("context_window") or {}
    rate   = data.get("rate_limits")
    cost   = data.get("cost") or {}
    agent  = data.get("_agent", "claude-code")

    parts: list[str] = []

    # Agent badge (for multi-agent state files)
    if agent != "claude-code":
        parts.append(AGENT_BADGES.get(agent, agent))

    parts.append(badge(plan))

    # Subscription rate limit bar (Pro / Max)
    if plan in ("pro", "max") and rate:
        five   = rate.get("five_hour", {})
        pct    = five.get("used_percentage")
        resets = five.get("resets_at")
        c  = color(pct)
        b  = bar(pct, width)
        p  = fmt_pct(pct)
        rt = f" {DIM}↺ {time_until(resets)}{RESET}" if resets else ""
        parts.append(f"🔋 {c}{b} {p}{RESET}{rt}")

    # PAYG cost
    elif plan == "payg":
        usd = float(cost.get("total_cost_usd", 0) or 0)
        parts.append(f"💸 {YELLOW}${usd:.4f}{RESET}")

    # Context window bar
    ctx_pct = ctx.get("used_percentage")
    if ctx_pct is not None:
        c = color(ctx_pct)
        b = bar(ctx_pct, max(10, int(width * 0.75)))
        p = fmt_pct(ctx_pct)
        parts.append(f"📝 {c}{b} {p}{RESET}")

    if parts:
        print("  ".join(parts))

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    config = load_config()

    # Try stdin first (Claude Code statusLine mode)
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                data = json.loads(raw)
                render(data, config)
                return
            except Exception:
                pass

    # Fall back to state files (Codex / Gemini mode)
    for agent in ("codex", "gemini"):
        state_file = M0SQ_DIR / f"{agent}-state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                data.setdefault("_agent", agent)
                render(data, config)
                return
            except Exception:
                pass

if __name__ == "__main__":
    main()
