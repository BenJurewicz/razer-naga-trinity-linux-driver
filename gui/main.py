# This file has been AI generated

import customtkinter as ctk
from tkinter.colorchooser import askcolor
import glob
import os
import sys
import threading
import time
import colorsys

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


class SpectrumAnimator(threading.Thread):
    def __init__(self, device_manager, zone, on_color_update_callback=None):
        super().__init__(daemon=True)
        self.device_manager = device_manager
        self.zone = zone
        self.on_color_update_callback = on_color_update_callback
        self._stop_event = threading.Event()
        self.hue = 0.0

    def run(self):
        """Continuously cycles through hues and updates the device color."""
        while not self._stop_event.is_set():
            # Convert HSV to RGB
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)]

            # Set the device color
            self.device_manager.set_color(self.zone, r, g, b)

            # Update the UI if a callback is provided
            if self.on_color_update_callback:
                self.on_color_update_callback(self.zone, (r, g, b))

            # Increment hue
            self.hue += 0.005  # Adjust for speed
            if self.hue >= 1.0:
                self.hue = 0.0

            time.sleep(0.05)  # Adjust for speed and smoothness

    def stop(self):
        """Stops the animation thread."""
        self._stop_event.set()


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
        self.entry_frame = ctk.CTkFrame(self)
        self.entry_frame.pack(pady=5, padx=20, fill="x")
        self.entry_frame.grid_columnconfigure((0, 1), weight=1)

        self._create_rgb_entries(self.entry_frame)
        self._create_hex_entry(self.entry_frame)

        self.update_color(initial_color)

    def set_enabled(self, is_enabled):
        """Enables or disables the interactive widgets in the controller."""
        state = "normal" if is_enabled else "disabled"

        # The CTkColorPicker does not support a disabled state, so we leave it
        # visible. The on_color_change logic handles switching back to static mode.
        self.r_entry.configure(state=state)
        self.g_entry.configure(state=state)
        self.b_entry.configure(state=state)
        self.hex_entry.configure(state=state)


    def _create_rgb_entries(self, parent):
        rgb_frame = ctk.CTkFrame(parent, fg_color="transparent")
        rgb_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(rgb_frame, text="R").pack(side="left", padx=5)
        self.r_entry = ctk.CTkEntry(rgb_frame, textvariable=self.r_var, width=50)
        self.r_entry.pack(side="left")

        ctk.CTkLabel(rgb_frame, text="G").pack(side="left", padx=5)
        self.g_entry = ctk.CTkEntry(rgb_frame, textvariable=self.g_var, width=50)
        self.g_entry.pack(side="left")

        ctk.CTkLabel(rgb_frame, text="B").pack(side="left", padx=5)
        self.b_entry = ctk.CTkEntry(rgb_frame, textvariable=self.b_var, width=50)
        self.b_entry.pack(side="left")

    def _create_hex_entry(self, parent):
        hex_frame = ctk.CTkFrame(parent, fg_color="transparent")
        hex_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(hex_frame, text="Hex").pack(side="left", padx=5)
        self.hex_entry = ctk.CTkEntry(hex_frame, textvariable=self.hex_var)
        self.hex_entry.pack(
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

        if source not in ["anim", "global_anim"]:
            if source != "rgb":
                self.r_var.set(str(r))
                self.g_var.set(str(g))
                self.b_var.set(str(b))

            if source != "hex":
                self.hex_var.set(self._rgb_to_hex(color))

        self._is_updating = False

        if source not in ["init", "anim", "global_anim"]:
            self.on_color_change_callback(self.zone, r, g, b)


class App(ctk.CTk):
    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager
        self.color_controllers = {}
        self.mode_vars = {}
        self.animation_threads = {}

        self.title("Razer Naga Trinity Control")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
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

            mode_var = ctk.StringVar(value="Static")
            mode_selector = ctk.CTkSegmentedButton(
                zone_frame,
                values=["Static", "Spectrum"],
                variable=mode_var,
                command=lambda mode, z=zone: self.on_mode_change(z, mode),
            )
            mode_selector.pack(pady=(5, 0))
            self.mode_vars[zone] = mode_var

            initial_color = self.device_manager.get_color(zone) or (0, 0, 0)
            controller = ColorController(
                zone_frame, zone, initial_color, self.on_color_change
            )
            controller.pack(padx=5, pady=5)
            self.color_controllers[zone] = controller

        # === All Tab Content ===
        all_frame = ctk.CTkFrame(all_tab, fg_color="transparent")
        all_frame.pack(expand=True, fill="both")
        all_frame.grid_columnconfigure(0, weight=1)

        zone_frame = ctk.CTkFrame(all_frame, fg_color=("gray90", "gray13"))
        zone_frame.grid(row=0, column=0, padx=5, pady=5)

        label = ctk.CTkLabel(zone_frame, text="All", font=ctk.CTkFont(weight="bold"))
        label.pack(pady=(10, 0))

        mode_var = ctk.StringVar(value="Static")
        mode_selector = ctk.CTkSegmentedButton(
            zone_frame,
            values=["Static", "Spectrum"],
            variable=mode_var,
            command=lambda mode, z="all": self.on_mode_change(z, mode),
        )
        mode_selector.pack(pady=(5, 0))
        self.mode_vars["all"] = mode_var

        initial_color = self.device_manager.get_color("scroll") or (
            0,
            0,
            0,
        )  # Use scroll as a baseline
        all_controller = ColorController(
            zone_frame, "all", initial_color, self.on_color_change
        )
        all_controller.pack(padx=5, pady=5)
        self.color_controllers["all"] = all_controller

        # --- Auto-sizing ---
        self.update_idletasks()
        required_width = self.tabview.winfo_reqwidth() + 20
        required_height = self.tabview.winfo_reqheight() + 30
        self.geometry(f"{required_width}x{required_height}")
        self.deiconify()

    def on_closing(self):
        """Stops all animation threads before closing the app."""
        for thread in self.animation_threads.values():
            thread.stop()
        self.destroy()

    def _update_animator_ui(self, zone, color):
        """Callback for the animator to update the UI color swatch."""
        hex_color = self.color_controllers["all"]._rgb_to_hex(color)
        if zone == "all":
            for controller in self.color_controllers.values():
                controller.color_swatch.configure(fg_color=hex_color)
        else:
            if zone in self.color_controllers:
                self.color_controllers[zone].color_swatch.configure(fg_color=hex_color)

    def on_mode_change(self, zone: str, mode: str):
        if mode == "Spectrum":
            # Stop conflicting animations
            if zone == "all":
                for z in ["scroll", "logo", "side"]:
                    if z in self.animation_threads:
                        self.animation_threads[z].stop()
                        del self.animation_threads[z]
            else:  # Individual zone
                if "all" in self.animation_threads:
                    self.animation_threads["all"].stop()
                    del self.animation_threads["all"]

            # Stop any existing animation for the same zone before starting a new one
            if zone in self.animation_threads:
                self.animation_threads[zone].stop()

            # Start new animation
            animator = SpectrumAnimator(
                self.device_manager, zone, self._update_animator_ui
            )
            self.animation_threads[zone] = animator
            animator.start()

            # Update UI
            if zone == "all":
                for z in self.color_controllers.keys():
                    self.mode_vars[z].set("Spectrum")
                    self.color_controllers[z].set_enabled(False)
            else:
                self.color_controllers[zone].set_enabled(False)
                # Check if all individual zones are now spectrum
                if all(
                    z in self.animation_threads for z in ["scroll", "logo", "side"]
                ):
                    self.on_mode_change("all", "Spectrum")

        elif mode == "Static":
            # Stop animation
            if zone == "all":
                if "all" in self.animation_threads:
                    self.animation_threads["all"].stop()
                    del self.animation_threads["all"]
                # Also stop individual animations
                for z in ["scroll", "logo", "side"]:
                    if z in self.animation_threads:
                        self.animation_threads[z].stop()
                        del self.animation_threads[z]
            else:  # Individual zone
                if zone in self.animation_threads:
                    self.animation_threads[zone].stop()
                    del self.animation_threads[zone]

            # Update UI and set color
            if zone == "all":
                for z in self.color_controllers.keys():
                    self.mode_vars[z].set("Static")
                    self.color_controllers[z].set_enabled(True)
                # Set color for all based on the 'all' controller
                r, g, b = self._get_controller_color(self.color_controllers["all"])
                self.device_manager.set_color("all", r, g, b)
                for z in ["scroll", "logo", "side"]:
                    self.color_controllers[z].update_color((r, g, b), source="global")
            else:
                self.color_controllers[zone].set_enabled(True)
                r, g, b = self._get_controller_color(self.color_controllers[zone])
                self.device_manager.set_color(zone, r, g, b)
                # If 'all' was in spectrum, its animation is stopped but UI needs update
                if "all" in self.mode_vars and self.mode_vars["all"].get() == "Spectrum":
                    self.mode_vars["all"].set("Static")
                    self.color_controllers["all"].set_enabled(True)


    def _get_controller_color(self, controller: ColorController) -> tuple[int, int, int]:
        try:
            r = int(controller.r_var.get())
            g = int(controller.g_var.get())
            b = int(controller.b_var.get())
            return r, g, b
        except (ValueError, ctk.TclError):
            return 0, 0, 0

    def on_color_change(self, zone: str, r: int, g: int, b: int):
        """Handles color changes from the ColorController, implying Static mode."""
        # Stop any active animations for the affected zone(s)
        if zone == "all":
            for z in list(self.animation_threads.keys()):
                self.animation_threads[z].stop()
                del self.animation_threads[z]
        else:
            if zone in self.animation_threads:
                self.animation_threads[zone].stop()
                del self.animation_threads[zone]
            if "all" in self.animation_threads:
                self.animation_threads["all"].stop()
                del self.animation_threads["all"]

        # Set the mode UI to Static
        if zone == "all":
            for z in self.mode_vars.keys():
                self.mode_vars[z].set("Static")
                # Ensure controller is enabled
                self.color_controllers[z].set_enabled(True)
        else:
            self.mode_vars[zone].set("Static")
            if "all" in self.mode_vars:
                self.mode_vars["all"].set("Static")
                self.color_controllers["all"].set_enabled(True)


        # Set device color
        if zone == "all":
            self.device_manager.set_color("all", r, g, b)
            # Update the UI of the individual controllers
            for z in ["scroll", "logo", "side"]:
                if z in self.color_controllers:
                    self.color_controllers[z].update_color((r, g, b), source="global")
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
