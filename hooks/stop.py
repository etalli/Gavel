#!/usr/bin/env python3
"""
Claude Code hook: Stop event
Turns off all LEDs when the Claude Code session ends.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pico import send_to_pico


def main():
    send_to_pico("Stop", {"type": "idle"})


if __name__ == "__main__":
    main()
