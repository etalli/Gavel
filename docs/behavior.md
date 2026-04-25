# Gavel Firmware Behavior Reference

This document explains in detail how `firmware/code.py` works — its state machine,
input handling, LED output, animation system, and serial protocol.

---

## Overview

```
                      ┌─────────────────────────────┐
                      │        firmware/code.py      │
                      │                              │
  Physical buttons ──►│  Button handler              │──► USB HID keypress (1/2/3)
                      │                              │
  Mac hook scripts ──►│  Serial reader → State FSM   │──► NeoPixel / PWM LEDs
                      │                              │
                      │  Animation tick (non-blocking)│
                      └─────────────────────────────┘
```

The firmware runs a **single tight loop** with no blocking delays in the main
path. Every periodic action (animations, timeouts) uses a timestamp comparison
rather than `time.sleep()`, so the loop stays responsive to buttons and serial
input at all times.

---

## Startup Sequence

```
1. board.board_id check  →  set USE_NEOPIXEL (True / False)
2. Keyboard + serial init
3. Button GPIO init       →  3× input with internal pull-up
4. LED init               →  NeoPixel or 3× PWM outputs
5. flash_all(times=2)     →  startup confirmation flash
6. Enter main loop
```

The startup flash (2× white blink) confirms that boot was successful and the
firmware is running. If the LEDs do not flash on power-up, `boot.py` has not
taken effect — unplug and replug USB.

---

## Board Auto-Detection

```python
USE_NEOPIXEL = board.board_id in ("waveshare_rp2040_zero", "seeeduino_xiao_rp2040")
```

`board.board_id` is a CircuitPython built-in string that identifies the
hardware at runtime. This eliminates any manual configuration. All subsequent
LED code branches on `USE_NEOPIXEL`:

- `True`  → NeoPixel path (single RGB LED on `board.NEOPIXEL`)
- `False` → PWM path (three separate LEDs on GP2 / GP3 / GP4)

---

## Config Block

All tunable parameters are grouped at the top of `code.py`:

| Constant              | Default | Purpose |
|-----------------------|---------|---------|
| `BREATH_PERIOD`       | 4.0 s   | Duration of one full NeoPixel breathing cycle |
| `BREATH_MAX`          | 125     | Peak brightness of the breathing animation (0–255) |
| `BREATH_UPDATE`       | 100 ms  | How often the breathing brightness is recalculated |
| `KNIGHT_STEP_MS`      | 1000 ms | Time each LED stays lit in the KITT sweep |
| `DEBOUNCE_MS`         | 50 ms   | Minimum time between registered button presses |
| `PERMISSION_TIMEOUT_MS` | 5000 ms | Auto-return to idle if no button is pressed |
| `KITT_DEFAULT`        | `False` | Whether KITT / breathing animation starts enabled |

---

## State Machine

The firmware has two states:

```
        serial "permission"
  IDLE ──────────────────► PERMISSION
   ▲                            │
   │  button press              │  button press
   │  serial "idle"             │  serial "idle"
   │  timeout (5 s)             │  timeout (5 s)
   └────────────────────────────┘
```

### STATE_IDLE

Default state. LEDs are off (or running an animation if `kitt_enabled` is
`True`). The device is waiting for a hook event or user interaction.

### STATE_PERMISSION

Entered when the Mac sends `{"type": "permission"}` via serial (triggered by
a `PreToolUse` hook). The LEDs light up solid white to signal "waiting for
your decision." The state records the entry timestamp for timeout tracking.

**Transitions out of STATE_PERMISSION:**

| Trigger | Action |
|---------|--------|
| Button 1 pressed | Send keycode `1`, green flash, → IDLE |
| Button 2 pressed | Send keycode `2`, blue flash, → IDLE |
| Button 3 pressed | Send keycode `3`, red flash, → IDLE |
| Serial `{"type": "idle"}` | LEDs off, → IDLE |
| 5-second timeout | LEDs off, → IDLE (safety net) |

The timeout exists because `PostToolUse` may not fire in all edge cases
(e.g., if Claude Code is interrupted). Without it, the LEDs would stay solid
white indefinitely.

---

## Button Input Handling

### Single Button Press

Buttons are **active low**: the GPIO reads `False` (0) when pressed, because
the pin is pulled up internally and the button connects it to GND.

```
  Internal pull-up (3.3V)
       │
      [R]  (internal)
       │
  GPIO pin ──── button ──── GND
```

A press is registered only if `(now - last_press) > DEBOUNCE_MS` (50 ms),
preventing multiple triggers from contact bounce.

### Button 2 + Button 3 Combo (KITT Toggle)

Pressing Button 2 and Button 3 simultaneously toggles `kitt_enabled`.

**Detection algorithm:**

```
1. Either btn2 or btn3 reads as pressed
2. Wait 40 ms  (combo window)
3. Re-read both buttons
4. If BOTH are still pressed → combo action (toggle kitt_enabled)
5. If only one is pressed    → single button action
```

The 40 ms window is chosen to be long enough for human fingers (who cannot
press both buttons at exactly the same instant) but short enough that it feels
instantaneous. The combo also has its own 500 ms cooldown (`last_combo`) to
prevent double-toggle from a single press.

---

## LED Output

### NeoPixel (RP2040 Zero / XIAO RP2040)

A single WS2812 RGB LED. All states are expressed as `(R, G, B)` tuples with
values 0–255. The `brightness=1.0` parameter in the NeoPixel constructor means
the tuple values are used directly without scaling.

| Event                | Color       | RGB            |
|----------------------|-------------|----------------|
| Waiting (permission) | White       | (255, 255, 255)|
| Allow Once pressed   | Green       | (0, 255, 0)    |
| Always Allow pressed | Blue        | (0, 0, 255)    |
| Reject pressed       | Red         | (255, 0, 0)    |
| Notification info    | White pulse | (255, 255, 255)|
| Notification warn    | Orange      | (255, 165, 0)  |
| Notification error   | Red rapid   | (255, 0, 0)    |
| Breathing (idle)     | Blue fade   | (0, 0, 0–125)  |

**`neo_flash(r, g, b, times, on_ms, off_ms)`**

A blocking helper used only for brief feedback flashes (200 ms or less total).
It is acceptable to block here because flashes are so short that no button
press or serial message will be missed.

### PWM LEDs (Raspberry Pi Pico)

Three separate LEDs driven by `pwmio.PWMOut` at 1 kHz. Duty cycle values:

| Constant | Value  | Meaning          |
|----------|--------|------------------|
| `BRIGHT` | 65535  | Full brightness  |
| `DIM`    | 8000   | Trail in KITT    |
| `OFF`    | 0      | LED off          |

Each LED maps to a button:

| LED index | GPIO  | Color | Button        |
|-----------|-------|-------|---------------|
| 0         | GP2   | Green | Allow Once    |
| 1         | GP3   | Green | Always Allow  |
| 2         | GP4   | Red   | Reject        |

---

## Animation System

Both animations run **non-blocking** using a "next fire time" variable. Each
main loop iteration checks `now >= next_time`; if true, it updates the LED and
advances the timer. If false, the check costs only one integer comparison.

This pattern means the loop never sleeps, and buttons + serial remain
responsive during animations.

### NeoPixel Breathing (RP2040 Zero idle)

A smooth sine wave modulates the blue channel:

```python
brightness = int((1 - cos(2π × t / BREATH_PERIOD)) / 2 × BREATH_MAX)
```

- At `t=0`: `cos(0) = 1` → brightness = 0 (off)
- At `t=BREATH_PERIOD/2`: `cos(π) = -1` → brightness = BREATH_MAX (peak)
- Full cycle repeats every `BREATH_PERIOD` seconds (default 4 s)

The cosine formula produces a natural ease-in / ease-out that looks organic
rather than mechanical. Updated every `BREATH_UPDATE` ms (default 100 ms,
i.e. 10 fps — smooth enough for LED dimming).

**Active only when:** `USE_NEOPIXEL AND state == IDLE AND kitt_enabled`

### KITT Night-Rider Sweep (Pico idle)

Steps through the sequence `[0, 1, 2, 1]` (left → right → left) advancing
one LED every `KNIGHT_STEP_MS` ms (default 1000 ms).

```
Step 0: LED 0 BRIGHT,  LED 1 off,  LED 2 off
Step 1: LED 0 DIM,     LED 1 BRIGHT, LED 2 off
Step 2: LED 0 off,     LED 1 DIM,  LED 2 BRIGHT
Step 3: LED 0 off,     LED 1 BRIGHT, LED 2 DIM   ← bounce back
(repeat)
```

The previous LED is left at `DIM` (duty cycle 8000) rather than `OFF` to
create a tail/trail effect. Only one step behind is remembered (`knight_prev`),
so only one trail LED is shown at a time.

**Active only when:** `NOT USE_NEOPIXEL AND state == IDLE AND kitt_enabled`

---

## Serial Protocol (Mac → Device)

The Mac hook scripts send newline-terminated JSON strings over USB CDC serial.
The firmware reads one character at a time into a buffer, extracts complete
lines at each `\n`, and parses them with `json.loads()`.

### Message Format

```json
{"type": "<event>", "level": "<level>", "tool": "<name>"}
```

| Field   | Required | Values                          |
|---------|----------|---------------------------------|
| `type`  | yes      | `"permission"`, `"notification"`, `"idle"` |
| `level` | for notification | `"info"`, `"warn"`, `"error"` |
| `tool`  | optional | tool name string from PreToolUse |

### Behavior per Message Type

**`"permission"`**
- Set `state = STATE_PERMISSION`
- Record `permission_time = now`
- Call `set_waiting_leds()` (solid white / all LEDs on)

**`"notification"`**
- Always transitions to `STATE_IDLE` after the flash
- `level == "error"` → 5× fast red flashes
- `level == "warn"`  → 3× orange flashes (NeoPixel) or 3× white flashes (Pico)
- `level == "info"`  → 1× slow white flash

**`"idle"`**
- Set `state = STATE_IDLE`
- Call `all_leds_off()`
- Reset KITT animation state (Pico only)

### Serial Buffer

```python
serial_buf = ""   # persistent across loop iterations

def read_serial_line():
    if not serial.in_waiting:
        return None
    char = serial.read(1).decode("utf-8")
    serial_buf += char
    if "\n" in serial_buf:
        line, serial_buf = serial_buf.split("\n", 1)
        return line.strip()
    return None
```

One character is read per loop iteration (if available). This keeps the loop
non-blocking — reading stops immediately if the port has no data. Complete
lines are returned only when a `\n` is received; partial lines remain in
`serial_buf` until the rest arrives.

---

## Mac-Side Hook Pipeline

```
Claude Code event
      │
      ▼
.claude/settings.json  →  calls hook script via shell
      │
      ▼
hooks/pre_tool.py (or notify.py, post_tool.py, stop.py)
      │   reads JSON from stdin (Claude Code passes event data)
      │   classifies notification level (notify.py only)
      │   checks context_window_utilization (post_tool.py only — warns if ≥ 90%)
      ▼
hooks/pico.py  →  send_to_pico(event, payload)
      │
      ▼
hooks/find_device.py  →  find_pico_port()
      │   scans /dev/tty.usbmodem* and /dev/tty.usbserial*
      │   returns the highest-sorted port (data port, not REPL console)
      ▼
pyserial  →  opens port, writes JSON + "\n", closes
      │
      ▼
firmware serial buffer  →  parsed and acted on
```

### Port Selection

CircuitPython's `usb_cdc.enable(console=True, data=True)` creates two serial
ports over one USB cable:

| Port suffix | Purpose       |
|-------------|---------------|
| Lower number (e.g. `*1`) | REPL console  |
| Higher number (e.g. `*2`) | Data port (used by hooks) |

`find_pico_port()` always picks the last (highest-sorted) port, which is
reliably the data port.

### Notification Level Classification

`notify.py` classifies notifications by scanning the message text for keywords:

| Keywords found in message         | Level   |
|-----------------------------------|---------|
| "error", "fail", "fatal"          | error   |
| "warn", "caution"                 | warn    |
| (none of the above)               | info    |

This avoids depending on a `level` field that Claude Code does not always
provide in notification payloads.

---

## Main Loop Structure

```
while True:
    now = current time in ms

    ── Button input ──────────────────────────────────
    if debounce ok:
        if btn1 pressed:
            send keycode 1, flash green
        elif btn2 or btn3 pressed:
            wait 40 ms (combo window)
            re-read both
            if both: toggle kitt_enabled
            elif btn2: send keycode 2, flash blue
            elif btn3: send keycode 3, flash red

    ── Permission timeout ────────────────────────────
    if PERMISSION and elapsed > 5000 ms:
        → IDLE, leds off

    ── NeoPixel breathing tick ───────────────────────
    if NeoPixel AND IDLE AND kitt_enabled AND due:
        compute brightness from cosine
        set blue channel
        advance next tick time

    ── KITT tick ─────────────────────────────────────
    if NOT NeoPixel AND IDLE AND kitt_enabled AND due:
        advance knight_step
        set LEDs (bright current, dim previous)
        advance next tick time

    ── Serial input ──────────────────────────────────
    line = read one char from serial buffer
    if complete line:
        parse JSON
        act on type field
```

Each section is guarded so it only runs when meaningful, keeping the loop fast
and deterministic.
