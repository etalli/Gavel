# Gavel Architecture

## System Overview

```
[Physical Device]               [Mac]
  Button 1 (Allow Once)   ──►  sends 'y' + Enter to terminal
  Button 2 (Always Allow) ──►  sends 'a' + Enter to terminal
  Button 3 (Reject)       ──►  sends 'n' + Enter to terminal
  LED / Display           ◄──  Claude Code hooks → serial/USB → device
```

The device has two independent roles:

1. **Input** — registers as a USB HID keyboard. When Claude Code shows a
   permission prompt, pressing a physical button sends the matching keypress.
   No special Claude Code configuration is required for this half.

2. **Output** — Claude Code's hooks system runs a Python script on the Mac
   for events like `PreToolUse`, `PostToolUse`, and `Notification`. Each
   script opens a serial connection to the Pico and sends a small JSON
   message that drives the LEDs.

---

## Two Core Integrations

### 1. Button Input → USB HID Keyboard

The Pico enumerates as a standard USB keyboard. Claude Code's interactive
permission prompts accept:

| Key       | Meaning       |
|-----------|---------------|
| `y` Enter | Allow Once    |
| `a` Enter | Always Allow  |
| `n` Enter | Reject        |

Pressing a physical button triggers the corresponding keypress via the
`adafruit_hid` CircuitPython library. The terminal (and Claude Code) receive
it exactly as if the user had typed it.

### 2. Notifications → Physical Feedback via Claude Code Hooks

Claude Code supports shell hooks that fire on lifecycle events. The hooks in
`.claude/settings.json` call Python scripts in `hooks/` which write JSON
over the Pico's serial port:

| Hook event   | Script         | Device response              |
|--------------|----------------|------------------------------|
| PreToolUse   | pre_tool.py    | All three LEDs solid on      |
| PostToolUse  | post_tool.py   | All LEDs off (idle)          |
| Notification | notify.py      | Flash pattern based on level |

Notification flash patterns:

| Level | Pattern                        |
|-------|--------------------------------|
| info  | Single slow flash (all LEDs)   |
| warn  | Three medium flashes (all LEDs)|
| error | Five fast red flashes (reject LED only) |

---

## Hardware

| Component         | Part                  | Notes                            |
|-------------------|-----------------------|----------------------------------|
| Microcontroller   | Raspberry Pi Pico     | RP2040, CircuitPython firmware   |
| Buttons (×3)      | 6×6mm tactile switch  | Internal pull-up, active low     |
| LEDs (×3)         | 5mm — 2× green, 1× red | 220Ω resistor in series each   |
| Connection to Mac | USB Micro-B cable     | Powers the Pico + HID + serial   |
| Enclosure         | ~100×60×30mm box      | 3D-printed or ABS project box   |

See `hardware/wiring.md` for pin assignments and `hardware/bom.csv` for the
full parts list.

---

## File Layout

```
270_Gavel/
├── Architecture.md                ← This file
├── icon.svg                       ← Project icon (source)
├── icon-16.png                    ← PNG exports
├── icon-32.png
├── icon-128.png
├── icon-512.png
├── install.sh                     ← Copies firmware to CIRCUITPY drive
├── .claude/
│   └── settings.json              ← Claude Code hook configuration
├── firmware/
│   ├── boot.py                    ← Enables USB CDC console + data ports at startup
│   ├── code.py                    ← Button + LED + serial logic
│   └── requirements.txt           ← CircuitPython libs (adafruit_hid)
├── hooks/
│   ├── find_device.py             ← Locates the Pico's data serial port on macOS (usbmodem*3)
│   ├── pre_tool.py                ← Fires on PreToolUse — signals waiting state
│   ├── post_tool.py               ← Fires on PostToolUse — signals idle state
│   ├── notify.py                  ← Fires on Notification — drives flash pattern
│   ├── test_hooks.py              ← Hook test runner (no hardware needed)
│   └── requirements.txt           ← pip dependency: pyserial
└── hardware/
    ├── bom.csv                    ← Bill of materials
    └── wiring.md                  ← GPIO pin assignments and wiring diagrams
```

---

## Setup Steps

1. Install CircuitPython on the Pico from circuitpython.org
2. Copy `firmware/boot.py`, `firmware/code.py`, and the `adafruit_hid`
   library folder to the Pico's `CIRCUITPY` drive
3. Install the Mac-side dependency: `pip3 install pyserial`
4. Wire buttons and LEDs per `hardware/wiring.md`
5. Hooks are registered globally in `~/.claude/settings.json` — they activate
   automatically in every Claude Code session
