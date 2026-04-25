#!/usr/bin/env python3
"""
LED test utility for Gavel — visually verify all LED patterns with Pico connected.

Usage:
  python3 hooks/test_leds.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from find_device import find_pico_port
from pico import send_to_pico

HOLD = 3  # seconds to hold permission states

STEPS = [
    # (payload, label, what to expect)
    (
        {"type": "permission", "category": "readonly"},
        "readonly",
        "NeoPixel: BLUE       | Discrete: center LED dim",
    ),
    (
        {"type": "permission", "category": "write"},
        "write",
        "NeoPixel: YELLOW     | Discrete: two LEDs dim",
    ),
    (
        {"type": "permission", "category": "network"},
        "network",
        "NeoPixel: ORANGE blink | Discrete: blink",
    ),
    (
        {"type": "permission", "category": "destructive"},
        "destructive",
        "NeoPixel: RED        | Discrete: all bright",
    ),
    (
        {"type": "notification", "level": "info"},
        "notify info",
        "All LEDs: 1 slow flash",
    ),
    (
        {"type": "notification", "level": "warn"},
        "notify warn",
        "All LEDs: 3 medium flashes",
    ),
    (
        {"type": "notification", "level": "error"},
        "notify error",
        "LED 3 only: 5 fast red flashes",
    ),
    (
        {"type": "idle"},
        "idle",
        "All LEDs off",
    ),
]

# ── Preflight ─────────────────────────────────────────────────
print("=" * 58)
print("Gavel LED Test")
print("=" * 58)

port = find_pico_port()
if not port:
    print("ERROR: Pico not found. Plug it in and try again.")
    sys.exit(1)

print(f"Pico found: {port}")
print()

# ── Run steps ─────────────────────────────────────────────────
for payload, label, expected in STEPS:
    is_notification = payload.get("type") == "notification"
    is_idle         = payload.get("type") == "idle"

    print(f"  [{label}]")
    print(f"    Expect: {expected}")

    send_to_pico("test", payload)

    if is_notification or is_idle:
        time.sleep(1.5)  # wait for flash animation to finish
    else:
        time.sleep(HOLD)

    print()

print("Done.")
