#!/usr/bin/env python3
# © 2026 morius (M-zero-Squared). All rights reserved.
# https://github.com/m0squared/m0squared
"""
M0² Codex CLI Hook — PostToolUse
Reads the session transcript, calculates token usage,
and writes state to ~/.m0squared/codex-state.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

M0SQ_DIR   = Path.home() / ".m0squared"
STATE_FILE  = M0SQ_DIR / "codex-state.json"
CONFIG_FILE = M0SQ_DIR / "config.json"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}

def sum_tokens_from_transcript(transcript_path: str) -> dict:
    """Sum all token usage from a JSONL transcript."""
    total = {"input_tokens": 0, "output_tokens": 0,
             "cache_read": 0, "cache_create": 0}
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    usage = (entry.get("message") or {}).get("usage") or \
                            entry.get("usage") or {}
                    total["input_tokens"]  += usage.get("input_tokens", 0)
                    total["output_tokens"] += usage.get("output_tokens", 0)
                    total["cache_read"]    += usage.get("cache_read_input_tokens", 0)
                    total["cache_create"]  += usage.get("cache_creation_input_tokens", 0)
                except Exception:
                    pass
    except Exception:
        pass
    return total

def main() -> None:
    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    transcript_path = hook_input.get("transcript_path", "")
    config = load_config()

    token_limit = (config.get("codex") or {}).get("session_token_limit", 100000)

    tokens = sum_tokens_from_transcript(transcript_path)
    total_used = tokens["input_tokens"] + tokens["output_tokens"]
    pct = min(100.0, (total_used / token_limit) * 100) if token_limit > 0 else 0

    M0SQ_DIR.mkdir(parents=True, exist_ok=True)

    state = {
        "_agent": "codex",
        "_updated": datetime.now(timezone.utc).isoformat(),
        "context_window": {
            "used_percentage": round(pct, 1),
            "total_input_tokens": tokens["input_tokens"],
            "total_output_tokens": tokens["output_tokens"],
        },
        "cost": {
            "total_cost_usd": 0
        },
    }

    STATE_FILE.write_text(json.dumps(state, indent=2))

    # Allow hook to continue (don't block)
    print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
