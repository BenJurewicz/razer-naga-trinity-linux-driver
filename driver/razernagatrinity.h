#ifndef INCLUDE_DRIVER_RAZERNAGATRINITY_H_
#define INCLUDE_DRIVER_RAZERNAGATRINITY_H_

#include <linux/hid.h>

#define DRIVER_NAME "RazerNagaMouseDriver"

#define USB_VENDOR_ID_RAZER 0x1532
#define USB_PRODUCT_ID_RAZER_NAGA_TRINITY 0x0067

#define USB_WAIT_MIN 500
#define USB_WAIT_MAX 1000

// Helper macro for printing to dmesg in the correct format.
// Valid values for print_type are taken from include/linux/kern_levels.h:
//	KERN_EMERG		/* system is unusable */
//	KERN_ALERT		/* action must be taken immediately */
//	KERN_CRIT		/* critical conditions */
//	KERN_ERR	    	/* error conditions */
//	KERN_WARNING		/* warning conditions */
//	KERN_NOTICE		/* normal but significant condition */
//	KERN_INFO		/* informational */
//	KERN_DEBUG		/* debug-level messages */
#define RZR_PRINT(print_type, fmt, ...) \
    printk(print_type "%s: " fmt, DRIVER_NAME, ##__VA_ARGS__)

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
