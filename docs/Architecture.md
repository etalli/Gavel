# Gavel Architecture

## System Overview

```
[Physical Device]               [Mac]
  Button 1 (Allow Once)   ──►  sends '1' to terminal
  Button 2 (Always Allow) ──►  sends '2' to terminal
  Button 3 (Reject)       ──►  sends '3' to terminal
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
| Reset button (×1) | 6×6mm tactile switch  | RUN pin to GND, no resistor      |
| LEDs (×3)         | 5mm — 2× green, 1× red | 220Ω resistor in series each   |
| Connection to Mac | USB Micro-B cable     | Powers the Pico + HID + serial   |
| Enclosure         | ~100×60×30mm box      | Panel-mount buttons and LEDs     |

See `hardware/wiring.md` for pin assignments and `hardware/bom.csv` for the
full parts list.

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
│   ├── code.py                        ← Button + LED + serial logic
│   ├── test_leds.py                   ← LED test script
│   └── requirements.txt               ← CircuitPython libs (adafruit_hid)
├── hooks/
│   ├── find_device.py                 ← Locates the Pico's data serial port on macOS
│   ├── pico.py                        ← Shared serial send helper
│   ├── pre_tool.py                    ← Fires on PreToolUse — signals waiting state
│   ├── post_tool.py                   ← Fires on PostToolUse — signals idle state
│   ├── notify.py                      ← Fires on Notification — drives flash pattern
│   ├── test_hooks.py                  ← Hook test runner (no hardware needed)
│   └── requirements.txt               ← pip dependency: pyserial
├── hardware/
│   ├── bom.csv                        ← Bill of materials
│   └── wiring.md                      ← GPIO pin assignments and wiring diagrams
└── docs/
    ├── Architecture.md                ← This file
    ├── ROADMAP.md                     ← Planned features by phase
    ├── index.html                     ← Project landing page
    ├── styles.css                     ← Landing page styles
    ├── Gavel.key                      ← Keynote presentation
    └── icon.svg / icon-*.png          ← Project icons
```

---

## Setup Steps

1. Install CircuitPython on the Pico from circuitpython.org
2. Copy `firmware/boot.py`, `firmware/code.py`, and the `adafruit_hid`
   library folder to the Pico's `CIRCUITPY` drive
3. Install the Mac-side dependency: `pip3 install pyserial`
4. Wire buttons and LEDs per `hardware/wiring.md`
5. Run `./install.sh --deploy` to install hooks to `~/.claude/gavel/`
   and register them in `~/.claude/settings.json`
