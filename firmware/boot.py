import usb_hid

# Enable USB HID (keyboard) on boot
usb_hid.enable(
    (usb_hid.Device.KEYBOARD,),
    boot_device=1
)
