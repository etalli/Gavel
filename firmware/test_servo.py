"""
Gavel – Servo test script

Cycles through the four positions used in production:
  0°  → idle
  45° → info notification
  90° → warn notification
  135° → error notification

Copy this file to the CIRCUITPY drive as code.py to run the test.
Restore the original code.py when done.
"""

import board
import pwmio
import time

_servo_pwm = pwmio.PWMOut(board.GP6, frequency=50)

def set_servo(angle):
    pulse_us = 1000 + int(angle / 180 * 1000)  # 1000–2000 µs
    _servo_pwm.duty_cycle = pulse_us * 65535 // 20000

POSITIONS = [
    (  0, "idle              (0°)"),
    ( 45, "info notification (45°)"),
    ( 90, "warn notification (90°)"),
    (135, "error notification (135°)"),
]

print("Servo test starting — GP6")
print()

while True:
    for angle, label in POSITIONS:
        print("moving to:", label)
        set_servo(angle)
        time.sleep(1.5)
