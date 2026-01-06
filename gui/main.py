# This file has been AI generated

import customtkinter as ctk
from tkinter.colorchooser import askcolor
import glob
import os
import sys

# Set the appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(2.0)


class DeviceManager:
    """Handles finding the device and interacting with sysfs files."""

    def __init__(self):
        self.path = self._find_device_path()
        self.writable = self._check_permissions()

    def _find_device_path(self):
        """Finds the sysfs path for the Razer Naga Trinity's mouse interface."""
        search_pattern = "/sys/bus/hid/devices/*:1532:0067.*"
        devices = glob.glob(search_pattern)
        for device_path in devices:
            # The mouse interface is the one with the led_* files
            if os.path.exists(os.path.join(device_path, "led_all_color")):
                return device_path
        return None

    def _check_permissions(self):
        """Checks if the script has write permissions for the device files."""
        if not self.path:
            return False

        # Check write permissions for one of the files.
        # This is a good indicator for the rest.
        test_path = os.path.join(self.path, "led_all_color")
        if os.path.exists(test_path):
            return os.access(test_path, os.W_OK)
        return False

    def get_color(self, zone: str) -> tuple[int, int, int] | None:
        """Reads the current color for a specific zone."""
        if not self.writable:
            return None

        file_path = os.path.join(self.path, f"led_{zone}_color")
        try:
            with open(file_path, "r") as f:
                content = f.read().strip()
                r, g, b = [int(c, 16) for c in content.split()]
                return r, g, b
        except (IOError, ValueError, IndexError):
            return 0, 0, 0

    def set_color(self, zone: str, r: int, g: int, b: int):
        """Sets the color for a specific zone."""
        if not self.writable:
            return

        file_path = os.path.join(self.path, f"led_{zone}_color")
        try:
            with open(file_path, "w") as f:
                f.write(f"{r:02x} {g:02x} {b:02x}\n")
        except IOError:
            # This could be a permissions error, handled globally, but good to have failsafe
            pass


from CTkColorPicker import CTkColorPicker


class ColorController(ctk.CTkFrame):
    """A frame containing all controls for changing a color."""

    def __init__(
        self,
        master,
        zone: str,
        initial_color: tuple[int, int, int],
        on_color_change_callback,
    ):
        super().__init__(master, fg_color="transparent")
        self.zone = zone
        self.on_color_change_callback = on_color_change_callback

        self.r_var = ctk.StringVar(value=str(initial_color[0]))
        self.g_var = ctk.StringVar(value=str(initial_color[1]))
        self.b_var = ctk.StringVar(value=str(initial_color[2]))
        self.hex_var = ctk.StringVar(value=self._rgb_to_hex(initial_color))

        self.r_var.trace_add("write", self._update_from_rgb)
        self.g_var.trace_add("write", self._update_from_rgb)
        self.b_var.trace_add("write", self._update_from_rgb)
        self.hex_var.trace_add("write", self._update_from_hex)
        self._is_updating = False  # To prevent trace recursion

        self.color_swatch = ctk.CTkFrame(self, width=350, height=60, corner_radius=10)
        self.color_swatch.pack(pady=5)

        self.pick_button = CTkColorPicker(self, command=self._on_color_picked)
        self.pick_button.pack(pady=5, padx=20)

        # RGB and HEX entry frames
        entry_frame = ctk.CTkFrame(self)
        entry_frame.pack(pady=5, padx=20, fill="x")
        entry_frame.grid_columnconfigure((0, 1), weight=1)

        self._create_rgb_entries(entry_frame)
        self._create_hex_entry(entry_frame)

        self.update_color(initial_color)

    def _create_rgb_entries(self, parent):
        rgb_frame = ctk.CTkFrame(parent, fg_color="transparent")
        rgb_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(rgb_frame, text="R").pack(side="left", padx=5)
        ctk.CTkEntry(rgb_frame, textvariable=self.r_var, width=50).pack(side="left")

        ctk.CTkLabel(rgb_frame, text="G").pack(side="left", padx=5)
        ctk.CTkEntry(rgb_frame, textvariable=self.g_var, width=50).pack(side="left")

        ctk.CTkLabel(rgb_frame, text="B").pack(side="left", padx=5)
        ctk.CTkEntry(rgb_frame, textvariable=self.b_var, width=50).pack(side="left")

    def _create_hex_entry(self, parent):
        hex_frame = ctk.CTkFrame(parent, fg_color="transparent")
        hex_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(hex_frame, text="Hex").pack(side="left", padx=5)
        ctk.CTkEntry(hex_frame, textvariable=self.hex_var).pack(
            side="left", expand=True, fill="x"
        )

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _hex_to_rgb(self, hex_code: str) -> tuple[int, int, int] | None:
        hex_code = hex_code.lstrip("#")
        if len(hex_code) == 6:
            try:
                return tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                return None
        return None

    def _on_color_picked(self, hex_color):
        rgb = self._hex_to_rgb(hex_color)
        if rgb:
            self.update_color(rgb, source="picker")

    def _update_from_rgb(self, *args):
        if self._is_updating:
            return
        try:
            r = int(self.r_var.get() or 0)
            g = int(self.g_var.get() or 0)
            b = int(self.b_var.get() or 0)
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                self.update_color((r, g, b), source="rgb")
        except (ValueError, ctk.TclError):
            pass

    def _update_from_hex(self, *args):
        if self._is_updating:
            return

        hex_val = self.hex_var.get()
        # Allow empty or partial hex codes while typing
        if len(hex_val) > 0 and hex_val[0] == "#" and len(hex_val) <= 7:
            if len(hex_val) == 7 or len(hex_val) == 4:  # e.g. #FFF
                rgb = self._hex_to_rgb(hex_val)
                if rgb:
                    self.update_color(rgb, source="hex")
        # if user deletes the #
        elif len(hex_val) <= 6:
            rgb = self._hex_to_rgb(hex_val)
            if rgb:
                self.update_color(rgb, source="hex")

    def update_color(self, color: tuple[int, int, int], source: str = "init"):
        self._is_updating = True
        r, g, b = color

        self.color_swatch.configure(fg_color=self._rgb_to_hex(color))

        if source != "rgb":
            self.r_var.set(str(r))
            self.g_var.set(str(g))
            self.b_var.set(str(b))

        if source != "hex":
            self.hex_var.set(self._rgb_to_hex(color))

        self._is_updating = False

        if source != "init":
            self.on_color_change_callback(self.zone, r, g, b)


class App(ctk.CTk):
    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager
        self.controllers = {}

        self.title("Razer Naga Trinity Control")
        self.resizable(True, True)
        self.withdraw()  # Hide window initially

        if not self.device_manager.writable:
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)
            label = ctk.CTkLabel(
                self,
                text="Razer Naga Trinity not found or insufficient permissions.\n\n"
                "Please ensure the kernel module is loaded and that\n"
                "you have write access to the sysfs files.",
                text_color="orange",
                wraplength=400,
            )
            label.grid(row=0, column=0, sticky="nsew")
            self.deiconify()  # Show error message window
            return

        # Main Tab View
        self.tabview = ctk.CTkTabview(self, anchor="w")
        self.tabview.pack(padx=10, pady=10, expand=True, fill="both")

        individual_tab = self.tabview.add("Individual")
        all_tab = self.tabview.add("All")

        # === Individual Tab Content ===
        individual_frame = ctk.CTkFrame(individual_tab, fg_color="transparent")
        individual_frame.pack(expand=True, fill="both")
        individual_frame.grid_columnconfigure((0, 1, 2), weight=1)

        zones = ["scroll", "logo", "side"]
        for i, zone in enumerate(zones):
            zone_frame = ctk.CTkFrame(individual_frame, fg_color=("gray90", "gray13"))
            zone_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

            label = ctk.CTkLabel(
                zone_frame, text=zone.capitalize(), font=ctk.CTkFont(weight="bold")
            )
            label.pack(pady=(10, 0))

            initial_color = self.device_manager.get_color(zone) or (0, 0, 0)
            controller = ColorController(
                zone_frame, zone, initial_color, self.on_color_change
            )
            controller.pack(padx=5, pady=5)
            self.controllers[zone] = controller

        # === All Tab Content ===
        all_frame = ctk.CTkFrame(all_tab, fg_color="transparent")
        all_frame.pack(expand=True, fill="both")
        all_frame.grid_columnconfigure(0, weight=1)

        zone_frame = ctk.CTkFrame(all_frame, fg_color=("gray90", "gray13"))
        zone_frame.grid(row=0, column=0, padx=5, pady=5)

        label = ctk.CTkLabel(zone_frame, text="All", font=ctk.CTkFont(weight="bold"))
        label.pack(pady=(10, 0))

        initial_color = self.device_manager.get_color("scroll") or (
            0,
            0,
            0,
        )  # Use scroll as a baseline
        all_controller = ColorController(
            zone_frame, "all", initial_color, self.on_color_change
        )
        all_controller.pack(padx=5, pady=5)
        self.controllers["all"] = all_controller

        # --- Auto-sizing ---
        self.update_idletasks()
        required_width = self.tabview.winfo_reqwidth() + 20
        required_height = self.tabview.winfo_reqheight() + 30
        self.geometry(f"{required_width}x{required_height}")
        self.deiconify()

    def on_color_change(self, zone: str, r: int, g: int, b: int):
        if zone == "all":
            self.device_manager.set_color("all", r, g, b)
            # Update the UI of the individual controllers
            for z in ["scroll", "logo", "side"]:
                if z in self.controllers:
                    self.controllers[z].update_color((r, g, b), source="global")
        else:
            self.device_manager.set_color(zone, r, g, b)


if __name__ == "__main__":
    try:
        device_manager = DeviceManager()
        app = App(device_manager)
        app.mainloop()
    except Exception as e:
        # Fallback for unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # Try to show a simple error window if tkinter is available
        try:
            root = ctk.CTk()
            root.title("Error")
            root.geometry("400x150")
            label = ctk.CTkLabel(
                root, text=f"An unexpected error occurred:\n{e}", text_color="red"
            )
            label.pack(expand=True, fill="both", padx=20, pady=20)
            root.mainloop()
        except:
            pass

        sys.exit(1)
