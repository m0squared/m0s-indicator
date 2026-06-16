#!/usr/bin/env python3
# © 2026 morius (M-zero-Squared). All rights reserved.
# https://github.com/m0squared/m0s-indicator
"""
M0² — Universal AI Agent HUD
Reads JSON from Claude Code's statusLine hook (stdin) or state files (Codex/Gemini).

Layouts (config "layout"):
  "rows"    — two lines: identity row, then quota + context together   (default)
  "inline"  — single dot/pipe-separated line
  "stacked" — identity, quota and context each on their own row
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

M0SQ_DIR    = Path.home() / ".m0squared"
CONFIG_FILE  = M0SQ_DIR / "config.json"

# Claude Code account / settings (source of plan tier, email, effort)
CLAUDE_JSON     = Path.home() / ".claude.json"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"

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

def load_claude_account() -> dict:
    """oauthAccount block from ~/.claude.json — plan tier, email, org info."""
    try:
        return json.loads(CLAUDE_JSON.read_text()).get("oauthAccount") or {}
    except Exception:
        return {}

def load_claude_settings() -> dict:
    try:
        return json.loads(CLAUDE_SETTINGS.read_text())
    except Exception:
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

def detect_plan(data: dict, config: dict, account: dict) -> str:
    user_plan = config.get("plan", "auto").lower()
    if user_plan != "auto":
        return user_plan

    # Real subscription tier comes from the Claude account, not rate_limits.
    org_type = (account.get("organizationType") or "").lower()
    tier     = (account.get("organizationRateLimitTier") or "").lower()
    if "max" in org_type or "max" in tier:
        return "max"
    if "pro" in org_type or "pro" in tier:
        return "pro"

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

def get_email(config: dict, account: dict) -> str:
    return config.get("email") or account.get("emailAddress") or ""

def get_effort(data: dict, settings: dict) -> str:
    """Reasoning effort — from the statusline payload if present, else settings.json."""
    model = data.get("model") or {}
    return str(data.get("effortLevel")
               or model.get("effortLevel")
               or settings.get("effortLevel")
               or "")

# ── Render ────────────────────────────────────────────────────────────────────

def build_bars(plan: str, rate, cost_obj: dict, ctx: dict, width: int) -> list[str]:
    bars = []

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
        bars.append(quota_line)

    # ── PAYG cost ─────────────────────────────────────────────────────────
    elif plan == "payg":
        usd = float(cost_obj.get("total_cost_usd", 0) or 0)
        bars.append(f"Cost {YELLOW}${usd:.4f}{RESET}")

    # ── Context window bar (starts EMPTY, fills as conversation grows) ────
    ctx_pct = ctx.get("used_percentage")
    if ctx_pct is not None:
        c = color_used(ctx_pct)
        b = bar(ctx_pct, max(10, int(width * 0.75)))
        p = fmt_pct(ctx_pct)
        bars.append(f"Ctx {c}{b} {p}{RESET}")

    return bars

def render(data: dict, config: dict) -> None:
    agent      = data.get("_agent", "claude-code")
    is_claude  = agent == "claude-code"
    account    = load_claude_account()  if is_claude else {}
    settings   = load_claude_settings() if is_claude else {}

    plan       = detect_plan(data, config, account)
    layout     = (config.get("layout") or "rows").lower()
    width      = int(config.get("bar_width", 20))
    ctx        = data.get("context_window") or {}
    rate       = data.get("rate_limits")
    cost_obj   = data.get("cost") or {}
    model_info = data.get("model") or {}
    model_name = model_info.get("display_name") or model_info.get("id", "")

    effort     = get_effort(data, settings) if config.get("show_effort", True) else ""
    email      = get_email(config, account)
    username   = get_username(config)
    ident      = email if (config.get("show_email", True) and email) else username

    # Model segment: "Opus 4.8 (medium)"
    model_seg = ""
    if model_name:
        model_seg = f"{DIM}{model_name}{RESET}"
        if effort:
            model_seg += f" {DIM}({effort}){RESET}"

    bars = build_bars(plan, rate, cost_obj, ctx, width)

    # ── Inline: single dot/pipe-separated line ───────────────────────────
    if layout == "inline":
        id_parts = []
        if not is_claude:
            id_parts.append(AGENT_BADGES.get(agent, agent))
        if model_seg:
            id_parts.append(model_seg)
        c, label = BADGES.get(plan, (DIM, plan.upper()))
        id_parts.append(f"{BOLD}{c}{label}{RESET}")
        if ident:
            id_parts.append(f"{DIM}{ident}{RESET}")

        print(SEP.join([DOT.join(id_parts), *bars]))
        return

    # ── Rows (default) / stacked: identity row + bar row(s) ──────────────
    id_left = []
    if not is_claude:
        id_left.append(AGENT_BADGES.get(agent, agent))
    id_left.append(badge(plan))
    if model_seg:
        id_left.append(model_seg)

    id_right = f"{DIM}{ident}{RESET}" if ident else ""
    line1 = f"{'  '.join(id_left)}   {id_right}".rstrip()

    if layout == "stacked":
        bar_lines = [b for b in bars if b.strip()]      # quota and context each on own row
    else:                                                # "rows": quota + context together
        joined = SEP.join(bars)
        bar_lines = [joined] if joined.strip() else []

    print("\n".join([line1, *bar_lines] if line1.strip() else bar_lines))

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
