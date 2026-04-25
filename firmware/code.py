"""
Gavel – Claude Code physical controller
Raspberry Pi Pico / Waveshare RP2040 Zero firmware (CircuitPython)

Buttons (both boards):
  GP14 → Allow Once   → sends '1'
  GP15 → Always Allow → sends '2'
  GP26 → Reject       → sends '3'

Regular LED mode (Raspberry Pi Pico):
  GP2 → Allow Once   (green)
  GP3 → Always Allow (green)
  GP4 → Reject       (red)

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

# Board auto-detection — no manual change needed
# NeoPixel boards: Waveshare RP2040 Zero, Seeed XIAO RP2040
# Discrete LED boards: Raspberry Pi Pico, Pico W (default)
USE_NEOPIXEL = board.board_id in ("waveshare_rp2040_zero", "seeeduino_xiao_rp2040")

# NeoPixel breathing animation
BREATH_PERIOD = 4.0   # seconds per full breath cycle
BREATH_MAX    = 125    # peak brightness (0–255)
BREATH_UPDATE = 100    # ms between brightness updates

# KITT animation (Pico only)
KNIGHT_STEP_MS = 1000  # ms per LED step

# Button debounce — guards against electrical bounce on the falling edge only
DEBOUNCE_MS = 50

# Permission timeout — return to idle if no response within this time
PERMISSION_TIMEOUT_MS = 5_000

# How long to hold the pressed button's LED after a decision
DECISION_HOLD_MS = 2_000

# KITT / breathing mode — toggle with Button 2 + Button 3 simultaneously
KITT_DEFAULT = False

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

btn_allow_once   = make_button(board.GP14)
btn_always_allow = make_button(board.GP15)
btn_reject       = make_button(board.GP26)

# Each entry: (button_object, keycode, NeoPixel_color, discrete_LED_index)
BUTTONS = [
    (btn_allow_once,   Keycode.ONE,   (0, 255, 0), 0),
    (btn_always_allow, Keycode.TWO,   (0, 0, 255), 1),
    (btn_reject,       Keycode.THREE, (255, 0, 0), 2),
]

# ── LED setup ─────────────────────────────────────────────────
import pwmio

# Both boards: anode → GPIO, cathode → GND (active-high): GPIO HIGH = on.
BRIGHT = 65535
DIM    = 8000
OFF    = 0

def make_led(pin):
    return pwmio.PWMOut(pin, frequency=1000, duty_cycle=OFF)

led_allow_once   = make_led(board.GP2)
led_always_allow = make_led(board.GP3)
led_reject       = make_led(board.GP4)
LEDS   = [led_allow_once, led_always_allow, led_reject]

if USE_NEOPIXEL:
    import neopixel
    np = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=1.0, auto_write=True, pixel_order=neopixel.RGB)
    breath_next = 0

KNIGHT_SEQUENCE = [0, 1, 2, 1]
knight_step = 0
knight_prev = -1
knight_next = 0

def all_leds_off():
    if USE_NEOPIXEL:
        np[0] = (0, 0, 0)
    for led in LEDS:
        led.duty_cycle = OFF

def set_led(index, duty):
    LEDS[index].duty_cycle = duty

def set_waiting_leds():
    if USE_NEOPIXEL:
        np[0] = (255, 255, 255)
    for led in LEDS:
        led.duty_cycle = BRIGHT

def flash_all(times=3, on_ms=80, off_ms=80):
    for _ in range(times):
        if USE_NEOPIXEL:
            np[0] = (255, 255, 255)
        for led in LEDS:
            led.duty_cycle = BRIGHT
        time.sleep(on_ms / 1000)
        if USE_NEOPIXEL:
            np[0] = (0, 0, 0)
        for led in LEDS:
            led.duty_cycle = OFF
        time.sleep(off_ms / 1000)

# ── Notification flash helper ─────────────────────────────────
def flash_for_level(level):
    all_leds_off()
    if level == "error":
        for _ in range(5):
            if USE_NEOPIXEL:
                np[0] = (255, 0, 0)
            set_led(2, BRIGHT)
            time.sleep(0.1)
            if USE_NEOPIXEL:
                np[0] = (0, 0, 0)
            set_led(2, OFF)
            time.sleep(0.1)
    elif level == "warn":
        for _ in range(3):
            if USE_NEOPIXEL:
                np[0] = (255, 165, 0)  # orange
            for led in LEDS:
                led.duty_cycle = BRIGHT
            time.sleep(0.2)
            if USE_NEOPIXEL:
                np[0] = (0, 0, 0)
            for led in LEDS:
                led.duty_cycle = OFF
            time.sleep(0.08)
    else:
        flash_all(times=1, on_ms=200)

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

def press_button(keycode, color, led_idx):
    all_leds_off()
    send_key(keycode)
    if USE_NEOPIXEL:
        np[0] = color
    set_led(led_idx, BRIGHT)

# ── Startup flash ─────────────────────────────────────────────
flash_all(times=2, on_ms=100, off_ms=100)

# ── State ─────────────────────────────────────────────────────
STATE_IDLE       = "idle"
STATE_PERMISSION = "permission"
state = STATE_IDLE

kitt_enabled = KITT_DEFAULT  # runtime toggle; default set in config block above

# ── Main loop ─────────────────────────────────────────────────
last_press       = 0
last_combo       = 0
permission_time  = 0  # timestamp when STATE_PERMISSION was entered
decision_off_at  = 0  # ms timestamp to clear the decision LED; 0 = inactive
waiting_release  = False  # True = block until all buttons are physically released

while True:
    now = time.monotonic_ns() // 1_000_000  # ms

    # ── Button input ──────────────────────────────────────────
    all_released = btn_allow_once.value and btn_always_allow.value and btn_reject.value
    if waiting_release:
        if all_released:
            waiting_release = False
    elif (now - last_press) > DEBOUNCE_MS:
        if not btn_allow_once.value:
            press_button(*BUTTONS[0][1:])
            decision_off_at = now + DECISION_HOLD_MS
            state = STATE_IDLE
            last_press = now
            waiting_release = True

        elif not btn_always_allow.value or not btn_reject.value:
            # Wait 40ms to see if both get pressed (combo window)
            time.sleep(0.04)
            b2 = not btn_always_allow.value
            b3 = not btn_reject.value

            if b2 and b3:
                # Combo: toggle KITT / breathing mode
                if (now - last_combo) > 500:
                    kitt_enabled = not kitt_enabled
                    if not kitt_enabled:
                        all_leds_off()
                    last_combo = now
            else:
                for btn, keycode, color, led_idx in BUTTONS[1:]:
                    if not btn.value:
                        press_button(keycode, color, led_idx)
                        decision_off_at = now + DECISION_HOLD_MS
                        state = STATE_IDLE
                        break
            last_press = now
            waiting_release = True

    # ── Permission timeout ────────────────────────────────────
    if state == STATE_PERMISSION and (now - permission_time) > PERMISSION_TIMEOUT_MS:
        state = STATE_IDLE
        all_leds_off()

    # ── Decision LED hold ─────────────────────────────────────
    if decision_off_at and now >= decision_off_at:
        all_leds_off()
        decision_off_at = 0

    # ── NeoPixel breathing (sine wave, non-blocking) ──────────
    if USE_NEOPIXEL and state == STATE_IDLE and kitt_enabled and not decision_off_at and now >= breath_next:
        t = time.monotonic()
        brightness = int((1 - math.cos(2 * math.pi * t / BREATH_PERIOD)) / 2 * BREATH_MAX)
        np[0] = (0, 0, brightness)
        breath_next = now + BREATH_UPDATE

    # ── KITT animation (regular LEDs only, non-blocking) ──────
    if not USE_NEOPIXEL and state == STATE_IDLE and kitt_enabled and not decision_off_at and now >= knight_next:
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
            msg_type = msg.get("type", "")
            level    = msg.get("level", "info")

            if msg_type == "permission":
                state = STATE_PERMISSION
                permission_time = now
                decision_off_at = 0
                set_waiting_leds()

            elif msg_type == "notification":
                flash_for_level(level)
                state = STATE_IDLE
                if not USE_NEOPIXEL:
                    knight_prev = -1
                    knight_next = now + KNIGHT_STEP_MS

            elif msg_type == "idle":
                state = STATE_IDLE
                all_leds_off()
                if not USE_NEOPIXEL:
                    knight_prev = -1
                    knight_next = now + KNIGHT_STEP_MS

        except (ValueError, KeyError) as e:
            print("JSON error:", e, "line:", line)
