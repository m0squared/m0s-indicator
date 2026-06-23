#!/usr/bin/env python3
# © 2026 morius (M-zero-Squared). All rights reserved.
# https://github.com/m0squared/m0s-indicator
"""
M0² — Universal AI Agent HUD
Reads JSON from Claude Code's statusLine hook (stdin) or state files (Codex/Gemini).

Layouts (config "layout"):
  "rows"   — two lines: identity row + bars row   (default)
  "inline" — single dot/pipe-separated line
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

def quota_time_block(rate) -> str:
    """'1h 52m / 5h 00m  ↺ 3h 07m' — window elapsed + time until reset."""
    five      = (rate or {}).get("five_hour", {})
    resets_at = five.get("resets_at")
    if not resets_at:
        return ""
    return (f"{DIM}{time_used_of_window(resets_at)}{RESET}"
            f"  {DIM}↺ {time_until(resets_at)}{RESET}")

def build_bars(plan: str, rate, cost_obj: dict, ctx: dict, width: int,
               with_time: bool = True) -> list[str]:
    bars = []

    # ── Subscription quota bar (starts FULL, drains to empty) ────────────
    if plan in ("pro", "max") and rate:
        five       = rate.get("five_hour", {})
        used_pct   = five.get("used_percentage")

        remaining_pct = (100.0 - used_pct) if used_pct is not None else None

        c  = color_remaining(remaining_pct)
        b  = bar(remaining_pct, width)
        p  = fmt_pct(remaining_pct)

        quota_line = f"Quota {c}{b} {p}{RESET}"
        if with_time:
            tb = quota_time_block(rate)
            if tb:
                quota_line += f"  {tb}"
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

    # ── Inline: plan · model · quota(↺ only) │ context ───────────────────
    if layout == "inline":
        c, label = BADGES.get(plan, (DIM, plan.upper()))
        parts = [f"{BOLD}{c}{label}{RESET}"]            # plan first (e.g. Max)
        if not is_claude:
            parts.append(AGENT_BADGES.get(agent, agent))
        if model_seg:
            parts.append(model_seg)

        # Quota with reset time only (no elapsed window), dot-joined.
        if plan in ("pro", "max") and rate:
            five      = rate.get("five_hour", {})
            used_pct  = five.get("used_percentage")
            resets_at = five.get("resets_at")
            rem       = (100.0 - used_pct) if used_pct is not None else None
            quota_str = f"Quota {color_remaining(rem)}{bar(rem, width)} {fmt_pct(rem)}{RESET}"
            if resets_at:
                quota_str += f"  {DIM}↺ {time_until(resets_at)}{RESET}"
            parts.append(quota_str)
        elif plan == "payg":
            usd = float(cost_obj.get("total_cost_usd", 0) or 0)
            parts.append(f"Cost {YELLOW}${usd:.4f}{RESET}")

        line = DOT.join(parts)

        # Context window, pipe-separated at the end.
        ctx_pct = ctx.get("used_percentage")
        if ctx_pct is not None:
            cb = bar(ctx_pct, max(10, int(width * 0.75)))
            line += f"{SEP}Ctx {color_used(ctx_pct)}{cb} {fmt_pct(ctx_pct)}{RESET}"

        print(line)
        return

    # ── Rows (default): identity + window time on line 1, bars on line 2 ─
    bars = build_bars(plan, rate, cost_obj, ctx, width, with_time=False)
    id_left = []
    if not is_claude:
        id_left.append(AGENT_BADGES.get(agent, agent))
    id_left.append(badge(plan))
    if model_seg:
        id_left.append(model_seg)

    # Right side: quota window time (Pro/Max), else fall back to email/username.
    time_block = quota_time_block(rate) if plan in ("pro", "max") else ""
    id_right = time_block or (f"{DIM}{ident}{RESET}" if ident else "")
    line1 = f"{'  '.join(id_left)}   {id_right}".rstrip()
    line2 = SEP.join(bars)

    # Blank line between the two rows for a little breathing room.
    print("\n\n".join(l for l in (line1, line2) if l.strip()))

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
