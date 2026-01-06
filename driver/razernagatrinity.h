#ifndef INCLUDE_DRIVER_RAZERNAGATRINITY_H_
#define INCLUDE_DRIVER_RAZERNAGATRINITY_H_

#include <linux/hid.h>
#include <linux/types.h>

#define DRIVER_NAME "RazerNagaMouseDriver"

#define USB_VENDOR_ID_RAZER 0x1532
#define USB_PRODUCT_ID_RAZER_NAGA_TRINITY 0x0067

#define USB_WAIT_MIN 500
#define USB_WAIT_MAX 1000

struct razer_rgb {
    unsigned char r;
    unsigned char g;
    unsigned char b;
};

struct razer_device {
    struct usb_device* usb_dev;
    struct mutex lock;

    struct razer_rgb scroll_color;
    struct razer_rgb logo_color;
    struct razer_rgb side_color;
};

#endif  // INCLUDE_DRIVER_RAZERNAGATRINITY_H_
