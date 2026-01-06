# Razer Naga Trinity HID Linux Kernel Driver

This is a HID driver made for controlling the LEDs ona Razer Naga Trinity mouse.
It supports setting the individual zones separately.

## Explanation of directories

- driver - this is the kernel driver code
- python - this is code that I used to reverse engineer the Razer USB protocol
- gui - a simple GUI app that is meant to show off the functionality of the driver

## Learning Material

The code is based on the [openrazer](https://openrazer.github.io/) project,
as well as HID drivers in the Linux kernel.

Other useful resources:

- <https://sysprog21.github.io/lkmpg/>
- <https://www.youtube.com/watch?v=is9wVOKeIjQ>
- <https://www.youtube.com/watch?v=7Zo3bdaqfbo>
