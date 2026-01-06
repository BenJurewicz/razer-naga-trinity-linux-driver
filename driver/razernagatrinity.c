#include "razernagatrinity.h"

#include <linux/hid.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/usb.h>

// ============================================================================
// Sending Control URBs to the mouse
// ============================================================================

// Calculate the checksum for a standard control transfer packed with lenght=90
static unsigned char calc_checksum(unsigned char* data) {
    unsigned char crc = 0;
    unsigned int i;
    for (i = 2; i < 88; i++) {
        crc ^= data[i];
    }
    return crc;
}

static void send_data(struct razer_device* device, unsigned char* data) {
    // Values taken from reverse engineering the Razer Synapse 3 app with
    // wireshark
    uint request = HID_REQ_SET_REPORT;  // 0x09
    uint request_type =
        USB_DIR_OUT | USB_RECIP_INTERFACE | USB_TYPE_CLASS;  // 0x21
    uint value = 0x300;
    uint index = 0;
    uint size = 90;

    // Set the checksum in the message data
    data[88] = calc_checksum(data);

    mutex_lock(&device->lock);

    int len = usb_control_msg(
        device->usb_dev,
        usb_sndctrlpipe(device->usb_dev, 0),
        request,
        request_type,
        value,
        index,
        data,
        size,
        USB_CTRL_SET_TIMEOUT
    );

    usleep_range(USB_WAIT_MIN, USB_WAIT_MAX);

    if (len != size) {
        printk(KERN_WARNING DRIVER_NAME ": Control transfer failed.\n");
    }

    mutex_unlock(&device->lock);
}

static ssize_t send_init_packet(struct razer_device* dev) {
    // In the original software this packet gets sent once, when the device is
    // connected, and the Razer Synapse software is turned on.
    // Without it the color changing commands don't work.

    unsigned char* data;
    data = kzalloc(90, GFP_KERNEL);
    if (!data) {
        return -ENOMEM;
    }

    data[0] = 0x00;
    data[1] = 0x1F;
    data[2] = 0x00;
    data[3] = 0x00;
    data[4] = 0x00;
    data[5] = 0x06;
    data[6] = 0x0F;
    data[7] = 0x02;
    data[8] = 0x00;
    data[9] = 0x00;
    data[10] = 0x08;

    send_data(dev, data);

    kfree(data);

    return 0;
}

static void update_colors(struct razer_device* device) {
    unsigned char* data;
    data = kzalloc(90, GFP_KERNEL);
    if (!data) {
        printk(KERN_ERR DRIVER_NAME ": No memory\n");
        return;
    }

    data[0] = 0x00;
    data[1] = 0x1F;
    data[2] = 0x00;
    data[3] = 0x00;
    data[4] = 0x00;
    data[5] = 0x0E;
    data[6] = 0x0F;
    data[7] = 0x03;
    data[8] = 0x00;
    data[9] = 0x00;
    data[10] = 0x00;
    data[11] = 0x00;
    data[12] = 0x02;
    // Scroll
    data[13] = device->scroll_color.r;
    data[14] = device->scroll_color.g;
    data[15] = device->scroll_color.b;
    // Logo
    data[16] = device->logo_color.r;
    data[17] = device->logo_color.g;
    data[18] = device->logo_color.b;
    // Side
    data[19] = device->side_color.r;
    data[20] = device->side_color.g;
    data[21] = device->side_color.b;

    send_data(device, data);

    kfree(data);
}

// ============================================================================
// Device Attribute Files
// ============================================================================

static ssize_t razer_attr_change_all_led_color(
    struct device* dev, struct device_attribute* attr, const char* buf,
    size_t count
) {
    struct razer_rgb color = {0};
    if (sscanf(buf, "%2hhx %2hhx %2hhx", &color.r, &color.g, &color.b) != 3) {
        printk(
            KERN_WARNING DRIVER_NAME
            ": Wrong data for changing the color of the leds. The correct "
            "format is \"RR GG BB\". Example: \"ff 00 ff\"."
        );
    }

    struct razer_device* device = dev_get_drvdata(dev);

    device->scroll_color = color;
    device->logo_color = color;
    device->side_color = color;

    update_colors(device);

    return count;
}

static ssize_t razer_attr_change_scroll_led_color(
    struct device* dev, struct device_attribute* attr, const char* buf,
    size_t count
) {
    if (count != 3) {
        printk(
            KERN_WARNING DRIVER_NAME
            ": Changing the color accepts RGB value as 3 bytes"
        );
    }
    struct razer_rgb* rgb = (struct razer_rgb*)buf;

    struct razer_device* device = dev_get_drvdata(dev);

    device->scroll_color.r = rgb->r;
    device->scroll_color.g = rgb->g;
    device->scroll_color.b = rgb->b;

    update_colors(device);

    return count;
}

static ssize_t razer_attr_show_scroll_led_color(
    struct device* dev, struct device_attribute* attr, char* buf
) {
    struct razer_device* device = dev_get_drvdata(dev);
    struct razer_rgb* rgb = &device->scroll_color;
    return sysfs_emit(buf, "%02x %02x %02x\n", rgb->r, rgb->g, rgb->b);
}

static ssize_t razer_attr_change_logo_led_color(
    struct device* dev, struct device_attribute* attr, const char* buf,
    size_t count
) {
    if (count != 3) {
        printk(
            KERN_WARNING DRIVER_NAME
            ": Changing the color accepts RGB value as 3 bytes"
        );
    }
    struct razer_rgb* rgb = (struct razer_rgb*)buf;

    struct razer_device* device = dev_get_drvdata(dev);

    device->logo_color.r = rgb->r;
    device->logo_color.g = rgb->g;
    device->logo_color.b = rgb->b;

    update_colors(device);

    return count;
}

static ssize_t razer_attr_show_logo_led_color(
    struct device* dev, struct device_attribute* attr, char* buf
) {
    struct razer_device* device = dev_get_drvdata(dev);
    struct razer_rgb* rgb = &device->logo_color;
    return sysfs_emit(buf, "%02x %02x %02x\n", rgb->r, rgb->g, rgb->b);
}

static ssize_t razer_attr_change_side_led_color(
    struct device* dev, struct device_attribute* attr, const char* buf,
    size_t count
) {
    if (count != 3) {
        printk(
            KERN_WARNING DRIVER_NAME
            ": Changing the color accepts RGB value as 3 bytes"
        );
    }
    struct razer_rgb* rgb = (struct razer_rgb*)buf;

    struct razer_device* device = dev_get_drvdata(dev);

    device->side_color.r = rgb->r;
    device->side_color.g = rgb->g;
    device->side_color.b = rgb->b;

    update_colors(device);

    return count;
}

static ssize_t razer_attr_show_side_led_color(
    struct device* dev, struct device_attribute* attr, char* buf
) {
    struct razer_device* device = dev_get_drvdata(dev);
    struct razer_rgb* rgb = &device->side_color;
    return sysfs_emit(buf, "%02x %02x %02x\n", rgb->r, rgb->g, rgb->b);
}

static DEVICE_ATTR(led_all_color, 0220, NULL, razer_attr_change_all_led_color);
static DEVICE_ATTR(
    led_scroll_color, 0660, razer_attr_show_scroll_led_color,
    razer_attr_change_scroll_led_color
);
static DEVICE_ATTR(
    led_logo_color, 0660, razer_attr_show_logo_led_color,
    razer_attr_change_logo_led_color
);
static DEVICE_ATTR(
    led_side_color, 0660, razer_attr_show_side_led_color,
    razer_attr_change_side_led_color
);

// ============================================================================
// HID Initialization
// ============================================================================

static void razer_device_init(
    struct razer_device* dev, struct usb_interface* intf
) {
    mutex_init(&dev->lock);
    dev->usb_dev = interface_to_usbdev(intf);

    dev->scroll_color.r = 0;
    dev->scroll_color.g = 0;
    dev->scroll_color.b = 0;

    dev->logo_color.r = 0;
    dev->logo_color.g = 0;
    dev->logo_color.b = 0;

    dev->side_color.r = 0;
    dev->side_color.g = 0;
    dev->side_color.b = 0;
}

static int razer_probe(
    struct hid_device* hdev, const struct hid_device_id* id
) {
    printk(KERN_INFO DRIVER_NAME ": The mouse was connected\n");
    int retval = 0;
    struct usb_interface* intf = to_usb_interface(hdev->dev.parent);
    struct razer_device* dev = NULL;

    dev = kzalloc(sizeof(struct razer_device), GFP_KERNEL);
    if (dev == NULL) {
        printk(KERN_ERR DRIVER_NAME ": No memory\n");
        return -ENOMEM;
    }

    razer_device_init(dev, intf);

    if (intf->cur_altsetting->desc.bInterfaceProtocol ==
        USB_INTERFACE_PROTOCOL_MOUSE) {
        if (device_create_file(&hdev->dev, &dev_attr_led_all_color)) {
            goto exit_free;
        }
        if (device_create_file(&hdev->dev, &dev_attr_led_scroll_color)) {
            goto exit_free;
        }
        if (device_create_file(&hdev->dev, &dev_attr_led_logo_color)) {
            goto exit_free;
        }
        if (device_create_file(&hdev->dev, &dev_attr_led_side_color)) {
            goto exit_free;
        }
    }

    hid_set_drvdata(hdev, dev);

    retval = hid_parse(hdev);
    if (retval) {
        hid_err(hdev, "parse failed\n");
        goto exit_free;
    }
    retval = hid_hw_start(hdev, HID_CONNECT_DEFAULT);
    if (retval) {
        hid_err(hdev, "hw start failed\n");
        goto exit_free;
    }

    retval = send_init_packet(dev);
    if (retval) {
        printk(KERN_ERR DRIVER_NAME ": No memory\n");
        goto exit_free;
    }

    return 0;

exit_free:
    kfree(dev);
    return retval;
}

static void razer_remove(struct hid_device* hdev) {
    struct usb_interface* intf = to_usb_interface(hdev->dev.parent);
    struct razer_device* dev = hid_get_drvdata(hdev);

    if (intf->cur_altsetting->desc.bInterfaceProtocol ==
        USB_INTERFACE_PROTOCOL_MOUSE) {
        device_remove_file(&hdev->dev, &dev_attr_led_all_color);
        device_remove_file(&hdev->dev, &dev_attr_led_scroll_color);
        device_remove_file(&hdev->dev, &dev_attr_led_logo_color);
        device_remove_file(&hdev->dev, &dev_attr_led_side_color);
    }

    hid_hw_stop(hdev);

    kfree(dev);
    printk(KERN_INFO DRIVER_NAME ": The mouse was disconnected\n");
}

static const struct hid_device_id razer_devices[] = {
    {HID_USB_DEVICE(USB_VENDOR_ID_RAZER, USB_PRODUCT_ID_RAZER_NAGA_TRINITY)},
    {0}
};

MODULE_DEVICE_TABLE(hid, razer_devices);

static struct hid_driver razer_naga_trinity_driver = {
    .name = DRIVER_NAME,
    .id_table = razer_devices,
    .probe = razer_probe,
    .remove = razer_remove,
};

module_hid_driver(razer_naga_trinity_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Benjamin Jurewicz");
MODULE_DESCRIPTION("A HID driver for Razer Naga Trinity mouse");
