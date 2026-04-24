#!/usr/bin/env python3
# © 2026 morius (M-zero-Squared). All rights reserved.
# https://github.com/m0squared/m0s-indicator
"""
M0² — Universal AI Agent HUD
Reads JSON from Claude Code's statusLine hook (stdin) or state files (Codex/Gemini).
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

M0SQ_DIR    = Path.home() / ".m0squared"
CONFIG_FILE  = M0SQ_DIR / "config.json"

# ── ANSI ──────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
SEP    = f"  {DIM}│{RESET}  "
DOT    = f"  {DIM}·{RESET}  "

# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def bar(pct: float | None, width: int) -> str:
    """Filled from left = amount present (use for remaining/used)."""
    if pct is None:
        return "[" + "─" * width + "]"
    filled = min(width, max(0, round(width * pct / 100)))
    return "[" + "█" * filled + "░" * (width - filled) + "]"

def color_remaining(pct: float | None) -> str:
    """Green = plenty left  →  Red = almost empty."""
    if pct is None: return DIM
    if pct < 20:    return RED
    if pct < 50:    return YELLOW
    return GREEN

def color_used(pct: float | None) -> str:
    """Green = little used  →  Red = almost full."""
    if pct is None: return DIM
    if pct >= 80:   return RED
    if pct >= 50:   return YELLOW
    return GREEN

def fmt_pct(pct: float | None) -> str:
    return f"{pct:.0f}%" if pct is not None else "─%"

def time_until(ts: float) -> str:
    s = ts - datetime.now(timezone.utc).timestamp()
    if s <= 0: return "resetting…"
    h, m = int(s // 3600), int((s % 3600) // 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def time_used_of_window(resets_at: float, window_hours: int = 5) -> str:
    """Returns 'Xh XXm / Yh 00m' showing time elapsed in the current window."""
    now   = datetime.now(timezone.utc).timestamp()
    rem_s = max(0.0, resets_at - now)
    win_s = window_hours * 3600
    used_s = max(0.0, win_s - rem_s)
    uh, um = int(used_s // 3600), int((used_s % 3600) // 60)
    return f"{uh}h {um:02d}m / {window_hours}h 00m"

BADGES = {
    "pro":  (CYAN,    "Pro"),
    "max":  ("\033[95m", "Max"),
    "payg": (YELLOW,  "PAYG"),
    "free": (DIM,     "Free"),
}

def badge(plan: str) -> str:
    c, label = BADGES.get(plan, (DIM, plan.upper()))
    return f"{BOLD}{c}[{label}]{RESET}"

AGENT_BADGES = {
    "codex":  f"\033[35mCodex{RESET}",
    "gemini": f"\033[34mGemini{RESET}",
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

def get_username(config: dict) -> str:
    return (config.get("username")
            or os.environ.get("USER")
            or os.environ.get("USERNAME")
            or "")

# ── Render ────────────────────────────────────────────────────────────────────

def render(data: dict, config: dict) -> None:
    plan       = detect_plan(data, config)
    width      = int(config.get("bar_width", 20))
    ctx        = data.get("context_window") or {}
    rate       = data.get("rate_limits")
    cost_obj   = data.get("cost") or {}
    model_info = data.get("model") or {}
    agent      = data.get("_agent", "claude-code")

    username   = get_username(config)
    model_name = model_info.get("display_name") or model_info.get("id", "")

    # ── Identity segment: "Sonnet 4.6 · Pro · alice" ─────────────────────
    id_parts = []

    if agent != "claude-code":
        id_parts.append(AGENT_BADGES.get(agent, agent))

    if model_name:
        id_parts.append(f"{DIM}{model_name}{RESET}")

    c, label = BADGES.get(plan, (DIM, plan.upper()))
    id_parts.append(f"{BOLD}{c}{label}{RESET}")

    if username:
        id_parts.append(f"{DIM}{username}{RESET}")

    parts = [DOT.join(id_parts)]

    # ── Subscription quota bar (starts FULL, drains to empty) ────────────
    if plan in ("pro", "max") and rate:
        five       = rate.get("five_hour", {})
        used_pct   = five.get("used_percentage")
        resets_at  = five.get("resets_at")

        remaining_pct = (100.0 - used_pct) if used_pct is not None else None

        c  = color_remaining(remaining_pct)
        b  = bar(remaining_pct, width)
        p  = fmt_pct(remaining_pct)

        time_str  = time_used_of_window(resets_at) if resets_at else ""
        reset_str = f"{DIM}↺ {time_until(resets_at)}{RESET}" if resets_at else ""

        quota_line = f"Quota {c}{b} {p}{RESET}"
        if time_str:
            quota_line += f"  {DIM}{time_str}{RESET}"
        if reset_str:
            quota_line += f"  {reset_str}"

        parts.append(quota_line)

    # ── PAYG cost ─────────────────────────────────────────────────────────
    elif plan == "payg":
        usd = float(cost_obj.get("total_cost_usd", 0) or 0)
        parts.append(f"Cost {YELLOW}${usd:.4f}{RESET}")

    # ── Context window bar (starts EMPTY, fills as conversation grows) ────
    ctx_pct = ctx.get("used_percentage")
    if ctx_pct is not None:
        c = color_used(ctx_pct)
        b = bar(ctx_pct, max(10, int(width * 0.75)))
        p = fmt_pct(ctx_pct)
        parts.append(f"Ctx {c}{b} {p}{RESET}")

    print(SEP.join(parts))

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    config = load_config()

    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                data = json.loads(raw)
                render(data, config)
                return
            except Exception:
                pass

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
