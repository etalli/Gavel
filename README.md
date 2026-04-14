# Gavel

<img src="docs/icon-128.png" alt="Gavel icon" align="right"/>

A physical controller for [Claude Code](https://claude.ai/code).

**Why "Gavel"?** A judge's gavel delivers verdicts — allow or reject. This device does the same: when Claude Code asks for permission to run a tool, you press a physical button to rule on it. The name reflects the device's core role as the human decision point in the loop.

---

## What it does

- **Input** — Three physical buttons answer Claude Code's permission prompts (`1` Allow Once / `2` Always Allow / `3` Reject) without touching the keyboard.
- **Output** — LEDs light up in response to Claude Code hook events, giving real-time feedback on what Claude is doing.

---

## Hardware

Two boards are supported:

| Board | LED output | Config |
|-------|-----------|--------|
| Raspberry Pi Pico | 3× discrete LEDs (GP10/GP11/GP12) | `USE_NEOPIXEL = False` |
| Waveshare RP2040 Zero | Built-in RGB NeoPixel (GP16) | `USE_NEOPIXEL = True` |

Both use the same GPIO pins for buttons (GP2/GP3/GP4). See [`hardware/wiring.md`](hardware/wiring.md) for full pin assignments.

---

## How it works

The microcontroller runs two independent roles over a single USB cable:

1. **USB HID keyboard** — pressing a button sends the matching keypress to the terminal. Claude Code receives it exactly as if the user typed it. No special Claude Code configuration needed.

2. **Serial listener** — Claude Code hooks call Python scripts on the Mac side, which send small JSON messages over the microcontroller's USB serial port to control the LEDs.

| Hook | LED response |
|---|---|
| `PreToolUse` | All LEDs solid on |
| `PostToolUse` | All LEDs off |
| `Notification` (info) | Single slow flash |
| `Notification` (warn) | Three medium flashes |
| `Notification` (error) | Five fast flashes (red only) |

---

## Setup

1. Install [CircuitPython](https://circuitpython.org) on your board
2. Copy `firmware/boot.py`, `firmware/code.py`, and the `adafruit_hid` library to the `CIRCUITPY` drive
3. Install the Mac-side dependency: `pip3 install pyserial`
4. Wire buttons and LEDs per [`hardware/wiring.md`](hardware/wiring.md)
5. Hooks are registered in `~/.claude/settings.json` and activate automatically in every Claude Code session

Or use the install script:

```bash
./install.sh
```

Use `--deploy` to install hooks to `~/.claude/gavel/` — a stable location independent of the project folder path:

```bash
./install.sh --deploy
```

This is recommended if you plan to move or rename the project folder.

---

## Troubleshooting

**LEDs do not respond when running hook scripts manually from the terminal**

```
No module named 'serial'
```

`pyserial` may not be installed for the `python3` used in your terminal session. Fix with:

```bash
pip3 install pyserial
```

Note: Claude Code hooks may use a different Python environment that already has `pyserial` installed, so hooks can work in a Claude Code session even when manual terminal tests fail.
