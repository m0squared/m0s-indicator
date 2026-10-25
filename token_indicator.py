#!/usr/bin/env python3
"""
Claude Code Token Usage Indicator
Status line decorator for Claude Code — shows subscription plan badge and usage bars.

Install:
  1. Add to ~/.claude/settings.json:
       "statusLine": {
         "type": "command",
         "command": "python3 /path/to/token_indicator.py"
       }
  2. Edit config.json to set your plan ("auto", "pro", "max", "payg", "free")

GitHub: https://github.com/your-username/claude-code-indicator
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except Exception:
            pass
    return {}


def bar(pct: float | None, width: int = 20) -> str:
    """Unicode progress bar. Full = high usage (empty = low usage)."""
    if pct is None:
        return "[" + "?" * width + "]"
    filled = min(width, max(0, round(width * pct / 100)))
    empty  = width - filled
    return "[" + "█" * filled + "░" * empty + "]"


def color(pct: float | None) -> str:
    if pct is None:
        return DIM
    if pct >= 80:
        return RED
    if pct >= 50:
        return YELLOW
    return GREEN


def fmt_pct(pct: float | None) -> str:
    return f"{pct:.0f}%" if pct is not None else "?%"


def time_until(unix_ts: int | float) -> str:
    remaining = unix_ts - datetime.now(timezone.utc).timestamp()
    if remaining <= 0:
        return "resetting…"
    h = int(remaining // 3600)
    m = int((remaining % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"


def detect_plan(data: dict, config: dict) -> str:
    """
    Determine which plan badge to show.
    Priority: config file → auto-detect from JSON.
    """
    user_plan = config.get("plan", "auto").lower()
    if user_plan != "auto":
        return user_plan

    # Auto-detect
    if data.get("rate_limits"):
        return "pro"   # could be max — user should set config.json to "max"

    cost = (data.get("cost") or {}).get("total_cost_usd", 0)
    if cost and cost > 0:
        return "payg"

    return "free"


# ── Badge renderers ───────────────────────────────────────────────────────────

BADGE_STYLE = {
    "pro":  (CYAN,   "Pro"),
    "max":  (BOLD,   "Max"),
    "payg": (YELLOW, "PAYG"),
    "free": (DIM,    "Free"),
}


def badge(plan: str) -> str:
    c, label = BADGE_STYLE.get(plan, (DIM, plan.upper()))
    return f"{BOLD}{c}[{label}]{RESET}"


def render_subscription_bar(rate_limits: dict, width: int) -> str:
    five = rate_limits.get("five_hour", {})
    pct      = five.get("used_percentage")
    resets   = five.get("resets_at")

    c  = color(pct)
    b  = bar(pct, width)
    p  = fmt_pct(pct)
    rt = f" {DIM}↺ {time_until(resets)}{RESET}" if resets else ""

    return f"🔋 {c}{b} {p}{RESET}{rt}"


def render_context_bar(ctx: dict, width: int) -> str:
    pct = ctx.get("used_percentage")
    c = color(pct)
    b = bar(pct, width)
    p = fmt_pct(pct)
    return f"📝 {c}{b} {p}{RESET}"


def render_cost(cost: dict) -> str:
    usd = cost.get("total_cost_usd", 0) or 0
    return f"💸 {YELLOW}${usd:.4f}{RESET}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except Exception:
        return

    config    = load_config()
    plan      = detect_plan(data, config)
    width     = int(config.get("bar_width", 20))
    ctx       = data.get("context_window") or {}
    rate      = data.get("rate_limits")
    cost_obj  = data.get("cost") or {}

    parts: list[str] = [badge(plan)]

    if plan in ("pro", "max") and rate:
        parts.append(render_subscription_bar(rate, width))
    elif plan == "payg":
        parts.append(render_cost(cost_obj))

    if ctx.get("used_percentage") is not None:
        parts.append(render_context_bar(ctx, width))

    print("  ".join(parts))


if __name__ == "__main__":
    main()
