# Gavel Architecture

## System Overview

```
[Physical Device]               [Mac]
  Button 1 (Allow Once)   ──►  sends '1' to terminal
  Button 2 (Always Allow) ──►  sends '2' to terminal
  Button 3 (Reject)       ──►  sends '3' to terminal
  NeoPixel / LEDs         ◄──  Claude Code hooks → serial/USB → device
```

The device has two independent roles over a single USB cable:

1. **Input** — registers as a USB HID keyboard. When Claude Code shows a
   permission prompt, pressing a physical button sends the matching keypress.
   No special Claude Code configuration is required for this half.

2. **Output** — Claude Code's hooks system runs a Python script on the Mac
   for events like `PreToolUse`, `PostToolUse`, `Notification`, and `Stop`.
   Each script opens a serial connection to the device and sends a small JSON
   message that drives the LEDs.

---

## Two Core Integrations

### 1. Button Input → USB HID Keyboard

The device enumerates as a standard USB keyboard. Claude Code's interactive
permission prompts accept:

| Key | Meaning       |
|-----|---------------|
| `1` | Allow Once    |
| `2` | Always Allow  |
| `3` | Reject        |

Pressing a physical button triggers the corresponding keypress via the
`adafruit_hid` CircuitPython library. The terminal (and Claude Code) receive
it exactly as if the user had typed it.

### 2. Notifications → Physical Feedback via Claude Code Hooks

Claude Code supports shell hooks that fire on lifecycle events. The hooks in
`.claude/settings.json` call Python scripts in `hooks/` which write JSON
over the device's serial port:

| Hook event   | Script         | Device response              |
|--------------|----------------|------------------------------|
| PreToolUse   | pre_tool.py    | Solid white (waiting state)  |
| PostToolUse  | post_tool.py   | All LEDs off (idle)          |
| Notification | notify.py      | Flash pattern based on level |
| Stop         | stop.py        | All LEDs off (session ended) |

Notification flash patterns:

| Level | Pattern                              |
|-------|--------------------------------------|
| info  | Single slow white flash              |
| warn  | Three orange flashes                 |
| error | Five fast red flashes                |

---

## Hardware

### Primary Target: Waveshare RP2040 Zero

| Component       | Part                        | Notes                                  |
|-----------------|-----------------------------|----------------------------------------|
| Microcontroller | Waveshare RP2040 Zero       | RP2040, CircuitPython firmware         |
| Buttons (×3)    | 6×6mm tactile switch        | Internal pull-up, active low, GP2/3/4  |
| Reset button    | 6×6mm tactile switch        | RESET pin to GND, no resistor          |
| LED output      | Built-in RGB NeoPixel       | GP16 (WS2812), color-coded per event   |
| Connection      | USB-C cable                 | Powers the board + HID + serial        |

### Also Supported (Auto-Detected)

| Board                  | LED output                    |
|------------------------|-------------------------------|
| Raspberry Pi Pico      | 3× discrete LEDs (GP10/11/12) |
| Seeed XIAO RP2040      | Built-in RGB NeoPixel         |

Board type is detected automatically at runtime via `board.board_id` — no
manual configuration needed.

See `hardware/wiring.md` for full pin assignments.

---

## File Layout

```
270_Gavel/
├── CLAUDE.md                          ← Project instructions for Claude Code
├── README.md                          ← Project overview and setup guide
├── install.sh                         ← Installs hooks to ~/.claude/gavel/
├── .claude/
│   └── settings.json                  ← Claude Code hook configuration
├── firmware/
│   ├── boot.py                        ← Enables USB CDC console + data ports at startup
│   ├── code.py                        ← Button + LED + serial logic (main firmware)
│   ├── test_leds.py                   ← LED test script
│   └── requirements.txt               ← CircuitPython libs (adafruit_hid, neopixel)
├── hooks/
│   ├── find_device.py                 ← Locates the device's data serial port on macOS
│   ├── pico.py                        ← Shared serial send helper + logging
│   ├── pre_tool.py                    ← Fires on PreToolUse — signals waiting state
│   ├── post_tool.py                   ← Fires on PostToolUse — signals idle state
│   ├── notify.py                      ← Fires on Notification — drives flash pattern
│   ├── stop.py                        ← Fires on Stop — clears LEDs at session end
│   ├── test_hooks.py                  ← Hook test runner (no hardware needed)
│   └── requirements.txt               ← pip dependency: pyserial
├── hardware/
│   ├── HW.md                          ← Hardware design notes
│   ├── PCB/                           ← KiCad PCB project files
│   └── wiring.md                      ← GPIO pin assignments and wiring diagrams
└── docs/
    ├── Architecture.md                ← This file
    ├── behavior.md                    ← Detailed firmware behavior reference
    ├── ROADMAP.md                     ← Planned features by phase
    ├── index.html                     ← Project landing page
    ├── styles.css                     ← Landing page styles
    ├── Gavel.key                      ← Keynote presentation
    └── images/                        ← Icon files (SVG source + PNG exports)
```

---

## Setup Steps

1. Install CircuitPython on the board from circuitpython.org
2. Copy `firmware/boot.py` and `firmware/code.py` to the `CIRCUITPY` drive
3. Copy `adafruit_hid/` (all boards) and `neopixel.mpy` (RP2040 Zero) to `CIRCUITPY/lib/`
4. **Power cycle** the board (unplug and replug USB) so `boot.py` takes effect
5. Install the Mac-side dependency: `pip3 install pyserial`
6. Wire buttons per `hardware/wiring.md`
7. Run `./install.sh --deploy` to install hooks to `~/.claude/gavel/`
   and register them in `~/.claude/settings.json`
