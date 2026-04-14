"""
Gavel – Claude Code physical controller
Raspberry Pi Pico / Waveshare RP2040 Zero firmware (CircuitPython)

Buttons (both boards):
  GP2 → Allow Once   → sends '1'
  GP3 → Always Allow → sends '2'
  GP4 → Reject       → sends '3'

Regular LED mode (Raspberry Pi Pico):
  GP10 → Allow Once   (green)
  GP11 → Always Allow (green)
  GP12 → Reject       (red)

NeoPixel mode (Waveshare RP2040 Zero):
  GP16 → RGB NeoPixel — color-coded per event

Serial: USB serial (/dev/tty.usbmodem*) from Mac hook scripts
  Incoming JSON: {"type": "notification"|"permission"|"idle", "level": "info"|"warn"|"error"}
"""

import board
import digitalio
import json
import math
import time
import usb_cdc
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# ── Config ────────────────────────────────────────────────────

# Board selection
# True  = Waveshare RP2040 Zero (NeoPixel on GP16)
# False = Raspberry Pi Pico    (LEDs on GP10/GP11/GP12)
USE_NEOPIXEL = True

# NeoPixel breathing animation
BREATH_PERIOD = 4.0   # seconds per full breath cycle
BREATH_MAX    = 125    # peak brightness (0–255)
BREATH_UPDATE = 100    # ms between brightness updates

# KITT animation (Pico only)
KNIGHT_STEP_MS = 1000  # ms per LED step

# Button debounce
DEBOUNCE_MS = 50

# ── USB Keyboard ──────────────────────────────────────────────
kbd = Keyboard(usb_hid.devices)

# ── USB Serial data port (separate from REPL console) ────────
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

# ── LED setup ─────────────────────────────────────────────────
if USE_NEOPIXEL:
    import neopixel
    np = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=1.0, auto_write=True)

    def all_leds_off():
        np[0] = (0, 0, 0)

    def set_waiting_leds():
        np[0] = (255, 255, 255)  # white = waiting for input

    def neo_flash(r, g, b, times=1, on_ms=200, off_ms=80):
        for _ in range(times):
            np[0] = (r, g, b)
            time.sleep(on_ms / 1000)
            np[0] = (0, 0, 0)
            time.sleep(off_ms / 1000)

    def flash_all(times=3, on_ms=80, off_ms=80):
        neo_flash(255, 255, 255, times, on_ms, off_ms)

    breath_next = 0

else:
    import pwmio

    def make_led(pin):
        return pwmio.PWMOut(pin, frequency=1000, duty_cycle=0)

    led_allow_once   = make_led(board.GP10)
    led_always_allow = make_led(board.GP11)
    led_reject       = make_led(board.GP12)
    LEDS   = [led_allow_once, led_always_allow, led_reject]
    BRIGHT = 65535
    DIM    = 8000
    OFF    = 0

    def all_leds_off():
        for led in LEDS:
            led.duty_cycle = OFF

    def set_led(index, duty):
        LEDS[index].duty_cycle = duty

    def set_waiting_leds():
        for led in LEDS:
            led.duty_cycle = BRIGHT

    def flash_all(times=3, on_ms=80, off_ms=80):
        for _ in range(times):
            set_waiting_leds()
            time.sleep(on_ms / 1000)
            all_leds_off()
            time.sleep(off_ms / 1000)

    KNIGHT_SEQUENCE = [0, 1, 2, 1]
    knight_step = 0
    knight_prev = -1
    knight_next = 0

# ── Serial helpers ────────────────────────────────────────────
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

def send_key(keycode):
    kbd.press(keycode)
    time.sleep(0.05)
    kbd.release_all()
    time.sleep(0.05)

# ── Startup flash ─────────────────────────────────────────────
flash_all(times=2, on_ms=100, off_ms=100)

# ── State ─────────────────────────────────────────────────────
STATE_IDLE       = "idle"
STATE_PERMISSION = "permission"
state = STATE_IDLE

# kitt_enabled controls KITT (Pico) and breathing (NeoPixel)
kitt_enabled = True  # toggle with Button 2 + Button 3 simultaneously

# ── Main loop ─────────────────────────────────────────────────
last_press = 0
last_combo = 0

while True:
    now = time.monotonic_ns() // 1_000_000  # ms

    # ── Button input ──────────────────────────────────────────
    if (now - last_press) > DEBOUNCE_MS:
        if not btn_allow_once.value:
            all_leds_off()
            send_key(Keycode.ONE)
            if USE_NEOPIXEL:
                neo_flash(0, 255, 0, times=1, on_ms=200)   # green
            else:
                set_led(0, BRIGHT)
                time.sleep(0.2)
                all_leds_off()
            last_press = now

        elif not btn_always_allow.value or not btn_reject.value:
            # Wait 40ms to see if both get pressed (combo window)
            time.sleep(0.04)
            btn2 = not btn_always_allow.value
            btn3 = not btn_reject.value

            if btn2 and btn3:
                # Combo: toggle KITT / breathing mode
                if (now - last_combo) > 500:
                    kitt_enabled = not kitt_enabled
                    if not kitt_enabled:
                        all_leds_off()
                    last_combo = now
            elif btn2:
                all_leds_off()
                send_key(Keycode.TWO)
                if USE_NEOPIXEL:
                    neo_flash(0, 0, 255, times=1, on_ms=200)  # blue
                else:
                    set_led(1, BRIGHT)
                    time.sleep(0.2)
                    all_leds_off()
            elif btn3:
                all_leds_off()
                send_key(Keycode.THREE)
                if USE_NEOPIXEL:
                    neo_flash(255, 0, 0, times=1, on_ms=200)  # red
                else:
                    set_led(2, BRIGHT)
                    time.sleep(0.2)
                    all_leds_off()
            last_press = now

    # ── NeoPixel breathing (sine wave, non-blocking) ──────────
    if USE_NEOPIXEL and state == STATE_IDLE and kitt_enabled and now >= breath_next:
        t = time.monotonic()
        brightness = int((1 - math.cos(2 * math.pi * t / BREATH_PERIOD)) / 2 * BREATH_MAX)
        np[0] = (0, 0, brightness)
        breath_next = now + BREATH_UPDATE

    # ── KITT animation (regular LEDs only, non-blocking) ──────
    if not USE_NEOPIXEL and state == STATE_IDLE and kitt_enabled and now >= knight_next:
        all_leds_off()
        curr = KNIGHT_SEQUENCE[knight_step]
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
            t     = msg.get("type", "")
            level = msg.get("level", "info")

            if t == "permission":
                state = STATE_PERMISSION
                set_waiting_leds()

            elif t == "notification":
                all_leds_off()
                if level == "error":
                    if USE_NEOPIXEL:
                        neo_flash(255, 0, 0, times=5, on_ms=100, off_ms=100)
                    else:
                        for _ in range(5):
                            set_led(2, BRIGHT)
                            time.sleep(0.1)
                            set_led(2, OFF)
                            time.sleep(0.1)
                elif level == "warn":
                    if USE_NEOPIXEL:
                        neo_flash(255, 165, 0, times=3)  # orange
                    else:
                        flash_all(times=3)
                else:
                    if USE_NEOPIXEL:
                        neo_flash(255, 255, 255, times=1, on_ms=200)  # white
                    else:
                        flash_all(times=1, on_ms=200)
                state = STATE_IDLE
                if not USE_NEOPIXEL:
                    knight_prev = -1
                    knight_next = now + KNIGHT_STEP_MS

            elif t == "idle":
                state = STATE_IDLE
                all_leds_off()
                if not USE_NEOPIXEL:
                    knight_prev = -1
                    knight_next = now + KNIGHT_STEP_MS

        except (ValueError, KeyError) as e:
            print("JSON error:", e, "line:", line)
