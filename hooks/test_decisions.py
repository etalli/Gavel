#!/usr/bin/env python3
"""
Decision logging end-to-end test for Gavel.

Simulates a permission prompt, waits for a button press, then verifies
the decision was written to ~/.claude/gavel/decisions.jsonl.

Usage:
  python3 hooks/test_decisions.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from find_device import find_pico_port
from pico import send_to_pico, DECISIONS_LOG

# ── Preflight ─────────────────────────────────────────────────
print("=" * 52)
print("Gavel Decision Logging Test")
print("=" * 52)

port = find_pico_port()
if not port:
    print("ERROR: Device not found. Plug it in and try again.")
    sys.exit(1)

print(f"Device found: {port}")
print()

# ── Record log size before test ───────────────────────────────
before = 0
if os.path.exists(DECISIONS_LOG):
    with open(DECISIONS_LOG) as f:
        before = sum(1 for _ in f)

# ── Step 1: light up permission LEDs ─────────────────────────
send_to_pico("test", {"type": "permission", "category": "destructive"})
print("Permission LEDs are on (red).")
print()
print(">>> Press any button on the device now <<<")
print()
input("    (press Enter here after pressing the device button)")
print()

# ── Step 2: send idle — triggers serial buffer read ──────────
send_to_pico("test", {"type": "idle"})
time.sleep(0.2)  # let the log write settle

# ── Step 3: check decisions.jsonl ────────────────────────────
if not os.path.exists(DECISIONS_LOG):
    print("FAIL: decisions.jsonl was not created.")
    sys.exit(1)

with open(DECISIONS_LOG) as f:
    lines = [l.strip() for l in f if l.strip()]

after = len(lines)

if after <= before:
    print("FAIL: no new entry was written to decisions.jsonl.")
    print("      Make sure you pressed a button on the device (not Enter).")
    sys.exit(1)

last = json.loads(lines[-1])
print(f"PASS: decision logged →  button={last['button']}  ts={last['ts']}")
print()
print(f"Log: {DECISIONS_LOG}")
