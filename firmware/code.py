"""
Gavel – Claude Code physical controller
Raspberry Pi Pico firmware (CircuitPython)

Buttons:
  GP2 → Allow Once   → sends '1'
  GP3 → Always Allow → sends '2'
  GP4 → Reject       → sends '3'

LEDs:
  GP10 → Allow Once   (green)
  GP11 → Always Allow (green)
  GP12 → Reject       (red)

Serial: USB serial (/dev/tty.usbmodem*) from Mac hook scripts
  Incoming JSON: {"type": "notification"|"permission"|"idle", "level": "info"|"warn"|"error"}
"""

import board
import digitalio
import json
import pwmio
import time
import usb_cdc
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# ── USB Keyboard ──────────────────────────────────────────────
kbd = Keyboard(usb_hid.devices)

# ── USB Serial data port (separate from REPL console) ────────
# This is /dev/tty.usbmodem*2 on Mac — does not conflict with HID
serial = usb_cdc.data

# ── Buttons (active low via internal pull-up) ─────────────────
def make_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP
    return b

btn_allow_once   = make_button(board.GP2)
btn_always_allow = make_button(board.GP3)
btn_reject       = make_button(board.GP4)

# ── LEDs (PWM for brightness control) ────────────────────────
def make_led(pin):
    return pwmio.PWMOut(pin, frequency=1000, duty_cycle=0)

led_allow_once   = make_led(board.GP10)
led_always_allow = make_led(board.GP11)
led_reject       = make_led(board.GP12)

LEDS = [led_allow_once, led_always_allow, led_reject]

# PWM duty cycle constants (0–65535)
BRIGHT = 65535       # 100% — active LED
DIM    = 8000        # ~12% — trailing glow
OFF    = 0

# ── Helpers ───────────────────────────────────────────────────
def all_leds_off():
    for led in LEDS:
        led.duty_cycle = OFF

def set_led(index, duty):
    LEDS[index].duty_cycle = duty

def all_leds_on():
    for led in LEDS:
        led.duty_cycle = BRIGHT

def flash_all(times=3, on_ms=80, off_ms=80):
    for _ in range(times):
        all_leds_on()
        time.sleep(on_ms / 1000)
        all_leds_off()
        time.sleep(off_ms / 1000)

def set_waiting_leds():
    all_leds_on()

def send_key(keycode):
    kbd.press(keycode)
    time.sleep(0.05)
    kbd.release_all()
    time.sleep(0.05)

# ── Serial line buffer ────────────────────────────────────────
serial_buf = ""

def read_serial_line():
    global serial_buf
    if not serial.in_waiting:
        return None
    try:
        char = serial.read(1).decode("utf-8")
        if char:
            serial_buf += char
            if "\n" in serial_buf:
                line, serial_buf = serial_buf.split("\n", 1)
                return line.strip()
    except Exception:
        pass
    return None

# ── Startup flash (confirms code.py is running) ───────────────
flash_all(times=2, on_ms=100, off_ms=100)

# ── State ─────────────────────────────────────────────────────
STATE_IDLE       = "idle"
STATE_PERMISSION = "permission"
state = STATE_IDLE

# ── KITT animation (idle state only) ─────────────────────────
# Sequence bounces: LED0 → LED1 → LED2 → LED1 → LED0 → ...
# Active LED is bright; previous LED stays dimly lit as a trail.
KNIGHT_SEQUENCE = [0, 1, 2, 1]
KNIGHT_STEP_MS  = 1000
knight_step = 0
knight_prev = -1     # index of trailing LED (-1 = none)
knight_next = 0      # advance immediately on first loop
kitt_enabled = False  # toggled by pressing Button 2 + Button 3 simultaneously

# ── Main loop ─────────────────────────────────────────────────
DEBOUNCE_MS = 50
last_press = 0
last_combo = 0

while True:
    now = time.monotonic_ns() // 1_000_000  # ms

    # ── Button input ──────────────────────────────────────────
    if (now - last_press) > DEBOUNCE_MS:
        if not btn_allow_once.value:
            all_leds_off()
            set_led(0, BRIGHT)
            send_key(Keycode.ONE)
            time.sleep(0.2)
            all_leds_off()
            last_press = now

        elif not btn_always_allow.value or not btn_reject.value:
            # Wait 40ms to see if both buttons get pressed (combo window)
            time.sleep(0.04)
            btn2 = not btn_always_allow.value
            btn3 = not btn_reject.value

            if btn2 and btn3:
                # Combo: toggle KITT mode
                if (now - last_combo) > 500:
                    kitt_enabled = not kitt_enabled
                    if not kitt_enabled:
                        all_leds_off()
                    last_combo = now
            elif btn2:
                all_leds_off()
                set_led(1, BRIGHT)
                send_key(Keycode.TWO)
                time.sleep(0.2)
                all_leds_off()
            elif btn3:
                all_leds_off()
                set_led(2, BRIGHT)
                send_key(Keycode.THREE)
                time.sleep(0.2)
                all_leds_off()
            last_press = now

    # ── KITT animation (idle only, non-blocking) ──────────────
    if state == STATE_IDLE and kitt_enabled and now >= knight_next:
        all_leds_off()
        curr = KNIGHT_SEQUENCE[knight_step]
        # Trail: previous position stays dimly lit
        if knight_prev >= 0 and knight_prev != curr:
            set_led(knight_prev, DIM)
        set_led(curr, BRIGHT)
        knight_prev = curr
        knight_step = (knight_step + 1) % len(KNIGHT_SEQUENCE)
        knight_next = now + KNIGHT_STEP_MS

    # ── Incoming serial from Mac ──────────────────────────────
    line = read_serial_line()
    if line:
        print("received:", line)
        try:
            msg = json.loads(line)
            t = msg.get("type", "")
            level = msg.get("level", "info")

            if t == "permission":
                state = STATE_PERMISSION
                set_waiting_leds()

            elif t == "notification":
                if level == "error":
                    all_leds_off()
                    for _ in range(5):
                        set_led(2, BRIGHT)
                        time.sleep(0.1)
                        set_led(2, OFF)
                        time.sleep(0.1)
                elif level == "warn":
                    flash_all(times=3)
                else:
                    flash_all(times=1, on_ms=200)
                state = STATE_IDLE
                knight_prev = -1
                knight_next = now + KNIGHT_STEP_MS

            elif t == "idle":
                state = STATE_IDLE
                knight_prev = -1
                knight_next = now + KNIGHT_STEP_MS

        except (ValueError, KeyError) as e:
            print("JSON error:", e, "line:", line)
