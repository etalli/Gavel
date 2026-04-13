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

# ── LEDs ──────────────────────────────────────────────────────
def make_led(pin):
    led = digitalio.DigitalInOut(pin)
    led.direction = digitalio.Direction.OUTPUT
    led.value = False
    return led

led_allow_once   = make_led(board.GP10)
led_always_allow = make_led(board.GP11)
led_reject       = make_led(board.GP12)

# ── Helpers ───────────────────────────────────────────────────
def all_leds_off():
    led_allow_once.value = False
    led_always_allow.value = False
    led_reject.value = False

def flash_all(times=3, on_ms=80, off_ms=80):
    for _ in range(times):
        led_allow_once.value = True
        led_always_allow.value = True
        led_reject.value = True
        time.sleep(on_ms / 1000)
        all_leds_off()
        time.sleep(off_ms / 1000)

def set_waiting_leds():
    led_allow_once.value = True
    led_always_allow.value = True
    led_reject.value = True

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

# ── Main loop ─────────────────────────────────────────────────
DEBOUNCE_MS = 50
last_press = 0

while True:
    now = time.monotonic_ns() // 1_000_000  # ms

    # ── Button input ──────────────────────────────────────────
    if (now - last_press) > DEBOUNCE_MS:
        if not btn_allow_once.value:
            all_leds_off()
            led_allow_once.value = True
            send_key(Keycode.ONE)
            time.sleep(0.2)
            all_leds_off()
            last_press = now

        elif not btn_always_allow.value:
            all_leds_off()
            led_always_allow.value = True
            send_key(Keycode.TWO)
            time.sleep(0.2)
            all_leds_off()
            last_press = now

        elif not btn_reject.value:
            all_leds_off()
            led_reject.value = True
            send_key(Keycode.THREE)
            time.sleep(0.2)
            all_leds_off()
            last_press = now

    # ── Incoming serial from Mac ──────────────────────────────
    line = read_serial_line()
    if line:
        print("received:", line)
        try:
            msg = json.loads(line)
            t = msg.get("type", "")
            level = msg.get("level", "info")

            if t == "permission":
                set_waiting_leds()

            elif t == "notification":
                if level == "error":
                    all_leds_off()
                    for _ in range(5):
                        led_reject.value = True
                        time.sleep(0.1)
                        led_reject.value = False
                        time.sleep(0.1)
                elif level == "warn":
                    flash_all(times=3)
                else:
                    flash_all(times=1, on_ms=200)

            elif t == "idle":
                all_leds_off()

        except (ValueError, KeyError) as e:
            print("JSON error:", e, "line:", line)
