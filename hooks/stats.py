#!/usr/bin/env python3
"""
Gavel decision stats — summarize ~/.claude/gavel/decisions.jsonl

Usage:
  python3 hooks/stats.py
"""
import json
import os
from collections import Counter
from datetime import datetime

DECISIONS_LOG = os.path.expanduser("~/.claude/gavel/decisions.jsonl")

LABELS = {
    "allow_once":   "Allow Once   ",
    "always_allow": "Always Allow ",
    "reject":       "Reject       ",
}

# ── Load ──────────────────────────────────────────────────────
if not os.path.exists(DECISIONS_LOG):
    print("No decisions logged yet. Press some buttons during a Claude Code session.")
    raise SystemExit

events = []
with open(DECISIONS_LOG) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

if not events:
    print("decisions.jsonl exists but is empty.")
    raise SystemExit

# ── Compute ───────────────────────────────────────────────────
counts  = Counter(e["button"] for e in events)
total   = len(events)
first   = events[0]["ts"][:19].replace("T", " ")
last    = events[-1]["ts"][:19].replace("T", " ")
reject  = counts.get("reject", 0)
rate    = reject / total * 100 if total else 0

# ── Display ───────────────────────────────────────────────────
print("=" * 42)
print("Gavel Decision Stats")
print("=" * 42)
for key, label in LABELS.items():
    n = counts.get(key, 0)
    bar = "█" * n
    print(f"  {label} {n:>4}  {bar}")
print()
print(f"  Total       {total:>4}")
print(f"  Reject rate {rate:>3.0f}%")
print()
print(f"  First  {first}")
print(f"  Last   {last}")
print("=" * 42)
