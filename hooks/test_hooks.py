#!/usr/bin/env python3
"""
Test runner for Gavel hooks — no hardware needed.

Simulates what Claude Code sends to each hook script and checks the log.

Usage:
  cd /Users/k2/Library/CloudStorage/Dropbox/MyProjects/270_CCKN  # folder not yet renamed
  python3 hooks/test_hooks.py
"""
import json
import os
import subprocess
import sys
import time

HOOKS_DIR = os.path.dirname(__file__)
LOG_FILE  = os.path.join(HOOKS_DIR, "hook.log")
PYTHON    = sys.executable

# Clear the log before the test run
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

CASES = [
    # (script, stdin payload, description)
    (
        "pre_tool.py",
        {"tool_name": "Bash", "tool_input": {"command": "ls"}},
        "PreToolUse — Bash tool",
    ),
    (
        "post_tool.py",
        {"tool_name": "Bash", "tool_response": "file1.txt"},
        "PostToolUse — Bash tool",
    ),
    (
        "notify.py",
        {"message": "Task completed successfully"},
        "Notification — info level",
    ),
    (
        "notify.py",
        {"message": "Build failed with error"},
        "Notification — error level",
    ),
    (
        "notify.py",
        {"message": "Warning: deprecated API used"},
        "Notification — warn level",
    ),
]

print("=" * 60)
print("Gavel Hook Test")
print("=" * 60)

passed = 0
failed = 0

for script, stdin_data, description in CASES:
    script_path = os.path.join(HOOKS_DIR, script)
    stdin_bytes = json.dumps(stdin_data).encode()

    result = subprocess.run(
        [PYTHON, script_path],
        input=stdin_bytes,
        capture_output=True,
        timeout=5,
    )

    status = "PASS" if result.returncode == 0 else "FAIL"
    if result.returncode == 0:
        passed += 1
    else:
        failed += 1

    print(f"  [{status}] {description}")
    if result.returncode != 0:
        print(f"         stderr: {result.stderr.decode().strip()}")

print()
print(f"Results: {passed} passed, {failed} failed")
print()

# Show the log
if os.path.exists(LOG_FILE):
    print("── hook.log ──────────────────────────────────────────")
    with open(LOG_FILE) as f:
        print(f.read().rstrip())
    print("──────────────────────────────────────────────────────")
else:
    print("ERROR: hook.log was not created — hooks may not be logging correctly.")
    sys.exit(1)

sys.exit(0 if failed == 0 else 1)
