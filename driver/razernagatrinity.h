#ifndef INCLUDE_DRIVER_RAZERNAGATRINITY_H_
#define INCLUDE_DRIVER_RAZERNAGATRINITY_H_

#define USB_VENDOR_ID_RAZER 0x1532
#define USB_PRODUCT_ID_RAZER_NAGA_TRINITY 0x0067

#define USB_WAIT_MIN 500
#define USB_WAIT_MAX 1000

struct razer_device {
    struct usb_device* usb_dev;
    struct mutex lock;
}

#endif  // INCLUDE_DRIVER_RAZERNAGATRINITY_H_
