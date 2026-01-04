import usb.core
import usb.util
import sys
import time

# Check command line arguments
if len(sys.argv) != 4:
    print("Usage: sudo python3 main.py <rgb1> <rgb2> <rgb3>")
    print("Example: sudo python3 main.py ff00ff f1f2f3 ffffff")
    sys.exit(1)

# Parse RGB hex values into bytes
rgb_values = []
for arg in sys.argv[1:4]:
    # Remove any '0x' prefix if present
    arg = arg.replace("0x", "").replace("0X", "")

    # Validate hex string
    if len(arg) != 6:
        print(f"Error: '{arg}' must be 6 hex digits (RRGGBB)")
        sys.exit(1)

    try:
        # Parse as hex and extract R, G, B bytes
        rgb_int = int(arg, 16)
        r = (rgb_int >> 16) & 0xFF
        g = (rgb_int >> 8) & 0xFF
        b = rgb_int & 0xFF
        rgb_values.extend([r, g, b])
        print(f"Parsed {arg}: R={r:02x}, G={g:02x}, B={b:02x}")
    except ValueError:
        print(f"Error: '{arg}' is not a valid hex value")
        sys.exit(1)

VENDOR_ID = 0x1532  # Razer
PRODUCT_ID = 0x0067  # Naga Trinity (Mouse)


def calc_crc(data):
    # Source and explanation of this function is in
    # openrazer driver/razercommon.c razer_calculate_crc
    crc = 0
    for byte in data[2:88]:  # starts at 2, ends at 88
        crc = crc ^ byte
    return crc


# Find the device
dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if dev is None:
    raise ValueError("Device not found")
devStr = str(dev)[0:60] + "..."
print(f"Found device: {devStr}")

# Detach kernel driver if attached (important for HID devices)
kernel_driver_detached = False
if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
        kernel_driver_detached = True
        print("Kernel driver detached")
    except usb.core.USBError as e:
        print(f"Could not detach kernel driver: {e}")

# Get the active configuration
cfg = dev.get_active_configuration()
print(f"Active configuration: {cfg.bConfigurationValue}")

# Get the first interface
intf = cfg[(0, 0)]

# Get endpoints
ep_out = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
    == usb.util.ENDPOINT_OUT,
)
ep_out_str = str(ep_out)[0:60] + "..."

ep_in = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
    == usb.util.ENDPOINT_IN,
)
ep_in_str = str(ep_in)[0:60] + "..."

print(f"OUT endpoint: {ep_out_str}")
print(f"IN endpoint: {ep_in_str}")

try:
    data = [
        0x00,
        0x1F,
        0x00,
        0x00,
        0x00,
        0x06,
        0x0F,
        0x02,
        0x00,
        0x00,
        0x08,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
    ]

    data[-2] = calc_crc(data)

    ret = dev.ctrl_transfer(
        bmRequestType=0x21, bRequest=0x09, wValue=0x0300, wIndex=0, data_or_wLength=data
    )
    print(f"Mode change sent. Sent {ret} bytes")

except usb.core.USBError as e:
    print(f"Mode change failled with error: {e}")

# time.sleep(1)

# Send a control transfer (configuration URB)
# bmRequestType, bRequest, wValue, wIndex, data
try:
    data = [
        0x00,
        0x1F,
        0x00,
        0x00,
        0x00,
        0x0E,
        0x0F,
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x02,
        # 0xFF,  # 1
        # 0x00,  # 1
        # 0xFF,  # 1
        # 0xFF,  # 2
        # 0x00,  # 2
        # 0xFF,  # 2
        # 0xFF,  # 3
        # 0x00,  # 3
        # 0xFF,  # 3
        rgb_values[0],  # 1
        rgb_values[1],  # 1
        rgb_values[2],  # 1
        rgb_values[3],  # 2
        rgb_values[4],  # 2
        rgb_values[5],  # 2
        rgb_values[6],  # 3
        rgb_values[7],  # 3
        rgb_values[8],  # 3
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]

    data[-2] = calc_crc(data)

    print("Calculated crc is: ", calc_crc(data))

    ret = dev.ctrl_transfer(
        bmRequestType=0x21, bRequest=0x09, wValue=0x0300, wIndex=0, data_or_wLength=data
    )
    print(f"Color change sent. Sent {ret} bytes")

except usb.core.USBError as e:
    print(f"Color change failled with error: {e}")

# Clean up - reattach kernel driver
if kernel_driver_detached:
    try:
        usb.util.release_interface(dev, 0)
        print("Interface released")
        dev.attach_kernel_driver(0)
        print("Kernel driver reattached")
    except usb.core.USBError as e:
        print(f"Could not reattach kernel driver: {e}")

usb.util.dispose_resources(dev)
