"""
Gavel – Claude Code physical controller
Raspberry Pi Pico / Waveshare RP2040 Zero firmware (CircuitPython)

Buttons:
  v2: GP14 → Allow Once / GP15 → Always Allow / GP26 → Reject
  v3: GP2  → Allow Once / GP3  → Always Allow / GP4  → Reject

LEDs:
  v2: GP2  → Allow Once (green) / GP3 → Always Allow (green) / GP4 → Reject (red)
  v3: GP10 → Allow Once (green) / GP11 → Always Allow (green) / GP12 → Reject (red)

NeoPixel (Waveshare RP2040 Zero):
  GP16 → RGB NeoPixel — color-coded per event

Vibration motor (Waveshare RP2040 Zero):
  GP5 → motor driver IN — active high

Servo (Waveshare RP2040 Zero):
  GP6 → servo signal — holds angle by notification severity
         idle=0°  info=45°  warn=90°  error=135°

Serial: USB serial (/dev/tty.usbmodem*) from Mac hook scripts
  Incoming JSON: {"type": "notification"|"permission"|"idle", "level": "info"|"warn"|"error"}
"""

import board
import digitalio
import json
import math
import pwmio
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

# How long to hold the pressed button's LED after a decision
DECISION_HOLD_MS = 2_000

# KITT / breathing mode — toggle with Button 2 + Button 3 simultaneously
KITT_DEFAULT = False

# Permission blink interval for network-category tools (ms)
NETWORK_BLINK_MS = 500

# Servo angles per notification severity (degrees, 0–180)
SERVO_IDLE  =   0
SERVO_INFO  =  45
SERVO_WARN  =  90
SERVO_ERROR = 135

# ── USB Keyboard ──────────────────────────────────────────────
kbd = Keyboard(usb_hid.devices)

# ── USB Serial data port (separate from REPL console) ────────
serial = usb_cdc.data

# ── Servo (GP6, 50 Hz PWM) ───────────────────────────────────
# Pulse width: 1 ms (0°) to 2 ms (180°) over a 20 ms period.
_servo_pwm = pwmio.PWMOut(board.GP6, frequency=50)

def set_servo(angle):
    pulse_us = 1000 + int(angle / 180 * 1000)  # 1000–2000 µs
    _servo_pwm.duty_cycle = pulse_us * 65535 // 20000

set_servo(SERVO_IDLE)

# ── Vibration motor (active high, GP5) ───────────────────────
motor = digitalio.DigitalInOut(board.GP5)
motor.direction = digitalio.Direction.OUTPUT
motor.value = False

def buzz(times=1, on_ms=60, off_ms=60):
    for _ in range(times):
        motor.value = True
        time.sleep(on_ms / 1000)
        motor.value = False
        time.sleep(off_ms / 1000)

# ── Buttons (active low via internal pull-up) ─────────────────
def make_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP
    return b

# v2 boards (Waveshare RP2040 Zero))
#btn_allow_once   = make_button(board.GP14)
#btn_always_allow = make_button(board.GP15)
#btn_reject       = make_button(board.GP26)
# v3 boards
btn_allow_once   = make_button(board.GP2)
btn_always_allow = make_button(board.GP3)
btn_reject       = make_button(board.GP4)


# Each entry: (button_object, keycode, NeoPixel_color, discrete_LED_index, name)
BUTTONS = [
    (btn_allow_once,   Keycode.ONE,   (0, 255, 0), 0, "allow_once"),
    (btn_always_allow, Keycode.TWO,   (0, 0, 255), 1, "always_allow"),
    (btn_reject,       Keycode.THREE, (255, 0, 0), 2, "reject"),
]

# ── LED setup ─────────────────────────────────────────────────
# Both boards: anode → GPIO, cathode → GND (active-high): GPIO HIGH = on.
BRIGHT = 65535
DIM    = 8000
OFF    = 0

def make_led(pin):
    return pwmio.PWMOut(pin, frequency=1000, duty_cycle=OFF)

# v2 boards (Waveshare RP2040 Zero)
#led_allow_once   = make_led(board.GP2)
#led_always_allow = make_led(board.GP3)
#led_reject       = make_led(board.GP4)
# v3 boards
led_allow_once   = make_led(board.GP10) 
led_always_allow = make_led(board.GP11)
led_reject       = make_led(board.GP12)
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

def set_permission_leds(category):
    """Set LEDs based on tool risk category.
    destructive → all bright red  (high alert)
    write       → two LEDs dim    (medium risk)
    readonly    → one LED dim     (low stakes)
    network     → handled by blink loop in main
    """
    all_leds_off()
    if category == "readonly":
        if USE_NEOPIXEL:
            np[0] = (0, 0, 255)   # blue
        set_led(1, DIM)
    elif category == "write":
        if USE_NEOPIXEL:
            np[0] = (255, 200, 0)  # yellow
        set_led(0, DIM)
        set_led(1, DIM)
    elif category == "network":
        pass  # blink loop takes over immediately
    else:  # destructive (default)
        if USE_NEOPIXEL:
            np[0] = (255, 0, 0)   # red
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
        buzz(times=3, on_ms=60, off_ms=60)
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

button_event_queue = []  # buffered when port is closed; flushed on next connection

def press_button(keycode, color, led_idx, name="unknown"):
    all_leds_off()
    set_servo(SERVO_IDLE)
    buzz(times=1, on_ms=60)
    send_key(keycode)
    if USE_NEOPIXEL:
        np[0] = color
    set_led(led_idx, BRIGHT)
    button_event_queue.append(json.dumps({"event": "button", "button": name}) + "\n")

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
decision_off_at  = 0  # ms timestamp to clear the decision LED; 0 = inactive
waiting_release  = False  # True = block until all buttons are physically released
perm_category    = "destructive"  # category of the current permission request
perm_blink_on    = False          # current blink state for network category
perm_blink_next  = 0              # next blink toggle timestamp (ms)

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
                for btn, keycode, color, led_idx, name in BUTTONS[1:]:
                    if not btn.value:
                        press_button(keycode, color, led_idx, name)
                        decision_off_at = now + DECISION_HOLD_MS
                        state = STATE_IDLE
                        break
            last_press = now
            waiting_release = True

    # ── Decision LED hold ─────────────────────────────────────
    if decision_off_at and now >= decision_off_at:
        all_leds_off()
        decision_off_at = 0

    # ── Network permission blink (non-blocking) ───────────────
    if state == STATE_PERMISSION and perm_category == "network" and now >= perm_blink_next:
        perm_blink_on = not perm_blink_on
        if perm_blink_on:
            if USE_NEOPIXEL:
                np[0] = (255, 165, 0)  # orange
            for led in LEDS:
                led.duty_cycle = BRIGHT
        else:
            all_leds_off()
        perm_blink_next = now + NETWORK_BLINK_MS

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
        # Flush buffered button events first — port is confirmed open
        if button_event_queue:
            for evt in button_event_queue:
                serial.write(evt.encode())
            button_event_queue.clear()
        print("received:", line)
        try:
            msg = json.loads(line)
            msg_type = msg.get("type", "")
            level    = msg.get("level", "info")

            if msg_type == "permission":
                state = STATE_PERMISSION
                decision_off_at = 0
                perm_category   = msg.get("category", "destructive")
                perm_blink_on   = False
                perm_blink_next = now
                buzz(times=2, on_ms=60, off_ms=60)
                set_permission_leds(perm_category)

            elif msg_type == "notification":
                angle = {
                    "error": SERVO_ERROR,
                    "warn":  SERVO_WARN,
                }.get(level, SERVO_INFO)
                set_servo(angle)
                flash_for_level(level)
                state = STATE_IDLE
                if not USE_NEOPIXEL:
                    knight_prev = -1
                    knight_next = now + KNIGHT_STEP_MS

            elif msg_type == "idle":
                state = STATE_IDLE
                set_servo(SERVO_IDLE)
                all_leds_off()
                if not USE_NEOPIXEL:
                    knight_prev = -1
                    knight_next = now + KNIGHT_STEP_MS

        except (ValueError, KeyError) as e:
            print("JSON error:", e, "line:", line)
