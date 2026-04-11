# Gavel

<img src="docs/icon-128.png" alt="Gavel icon" align="right"/>

A physical controller for [Claude Code](https://claude.ai/code).

**Why "Gavel"?** A judge's gavel delivers verdicts — allow or reject. This device does the same: when Claude Code asks for permission to run a tool, you press a physical button to rule on it. The name reflects the device's core role as the human decision point in the loop.

---

## What it does

- **Input** — Three physical buttons answer Claude Code's permission prompts (`y` Allow Once / `a` Always Allow / `n` Reject) without touching the keyboard.
- **Output** — LEDs light up in response to Claude Code hook events, giving real-time feedback on what Claude is doing.

---

## Hardware

Three buttons and three LEDs connected to a USB microcontroller. See [`hardware/wiring.md`](hardware/wiring.md) for pin assignments and [`hardware/bom.csv`](hardware/bom.csv) for the parts list.

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
