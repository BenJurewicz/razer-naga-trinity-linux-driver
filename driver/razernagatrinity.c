#include "razernagatrinity.h"

#include <linux/hid.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/usb/input.h>

#include "asm-generic/errno-base.h"
#include "linux/gfp_types.h"
#include "linux/kern_levels.h"
#include "linux/types.h"

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

// ============================================================================
// Device Attribute
// ============================================================================

static ssize_t send_mode_switch(struct razer_device* dev) {
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

static ssize_t razer_attr_change_led_color(
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

    ssize_t retval = send_mode_switch(device);
    if (retval) {
        return retval;
    }

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
    data[5] = 0x0E;
    data[6] = 0x0F;
    data[7] = 0x03;
    data[8] = 0x00;
    data[9] = 0x00;
    data[10] = 0x00;
    data[11] = 0x00;
    data[12] = 0x02;
    // data[13] = 0xFF;  // 1
    // data[14] = 0x00;  // 1
    // data[15] = 0xFF;  // 1
    // data[16] = 0xFF;  // 2
    // data[17] = 0x00;  // 2
    // data[18] = 0xFF;  // 2
    // data[19] = 0xFF;  // 3
    // data[20] = 0x00;  // 3
    // data[21] = 0xFF;  // 3
    data[13] = rgb->r;  // 1
    data[14] = rgb->g;  // 1
    data[15] = rgb->b;  // 1
    data[16] = rgb->r;  // 2
    data[17] = rgb->g;  // 2
    data[18] = rgb->b;  // 2
    data[19] = rgb->r;  // 3
    data[20] = rgb->g;  // 3
    data[21] = rgb->b;  // 3

    send_data(device, data);

    kfree(data);

    return count;
}

static DEVICE_ATTR(change_led_color, 0220, NULL, razer_attr_change_led_color);

// ============================================================================
// HID Initialization
// ============================================================================

static void razer_device_init(
    struct razer_device* dev, struct usb_interface* intf
) {
    mutex_init(&dev->lock);
    dev->usb_dev = interface_to_usbdev(intf);
}

static int razer_probe(
    struct hid_device* hdev, const struct hid_device_id* id
) {
    int retval = 0;
    struct usb_interface* intf = to_usb_interface(hdev->dev.parent);
    struct razer_device* dev = NULL;

    dev = kzalloc(sizeof(struct razer_device), GFP_KERNEL);
    if (dev == NULL) {
        dev_err(&intf->dev, "out of memory\n");
        return -ENOMEM;
    }

    razer_device_init(dev, intf);

    // Create the file for the matrix effect
    if (device_create_file(&hdev->dev, &dev_attr_change_led_color)) {
        goto exit_free;
    }

    // TODO: I think these two lines do the same thing
    hid_set_drvdata(hdev, dev);
    dev_set_drvdata(&hdev->dev, dev);

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

    return 0;

exit_free:
    kfree(dev);
    return retval;
}

static void razer_remove(struct hid_device* hdev) {
    struct usb_interface* intf = to_usb_interface(hdev->dev.parent);
    struct razer_device* dev = hid_get_drvdata(hdev);

    device_remove_file(&hdev->dev, &dev_attr_change_led_color);

    hid_hw_stop(hdev);

    kfree(dev);
    dev_info(&intf->dev, "Razer Device disconnected\n");
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
