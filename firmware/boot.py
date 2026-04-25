import usb_cdc

# Enable both console (REPL) and a separate data serial port.
# The data port is /dev/tty.usbmodem*2 on Mac and does not
# interfere with USB HID keyboard.
usb_cdc.enable(console=True, data=True)
