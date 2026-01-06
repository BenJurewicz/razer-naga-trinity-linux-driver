# Razer Naga Trinity HID Linux Kernel Driver

This is a HID driver made for controlling the LEDs ona Razer Naga Trinity mouse.
It supports setting the individual zones separately.

## Explanation of directories

- driver - this is the kernel driver code
- python - this is code that I used to reverse engineer the Razer USB protocol
- gui - a simple GUI app that is meant to show off the functionality of the driver

## Useful commands

### Recompile the driver

Execute in the driver directory

```bash
make clean && bear -- make

```

The bear command is optional but it generates the file `compile_commands.json`,
so that clang knows whats going on in the project.
This way you can move around the code and jump to the kernel headers.

### Insert/Remove the kernel module

Execute in the driver directory

Remove the module:

```bash
sudo rmmod razernagatrinity
```

Insert the module:

```bash
sudo insmod razernagatrinity.ko
```

### Turn on the GUI app

Execute in the gui directory

```bash
sudo venv/bin/python main.py
```

Turns on the GUI. Before running it,
you of course need to install the `requirements.txt`, preferably in a venv.

You don't need to be in the venv to execute this command.

I know that using `sudo` to open the gui is not ideal, but I found this is
simpler than creating a `udev` rule to set the permissions.

## Learning Material

The code is based on the [openrazer](https://openrazer.github.io/) project,
as well as HID drivers in the Linux kernel.

Other useful resources:

- <https://sysprog21.github.io/lkmpg/>
- <https://www.youtube.com/watch?v=is9wVOKeIjQ>
- <https://www.youtube.com/watch?v=7Zo3bdaqfbo>
