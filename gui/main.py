# This file has been AI generated

import customtkinter as ctk
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
    ZONES = ["scroll", "logo", "side"]

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

        for i, zone in enumerate(self.ZONES):
            zone_frame = ctk.CTkFrame(individual_frame, fg_color=("gray90", "gray13"))
            zone_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self._populate_zone_frame(zone_frame, zone)

        # === All Tab Content ===
        all_frame = ctk.CTkFrame(all_tab, fg_color="transparent")
        all_frame.pack(expand=True, fill="both")
        all_frame.grid_columnconfigure(0, weight=1)

        zone_frame = ctk.CTkFrame(all_frame, fg_color=("gray90", "gray13"))
        zone_frame.grid(row=0, column=0, padx=5, pady=5)
        self._populate_zone_frame(zone_frame, "all")

        # --- Auto-sizing ---
        self.update_idletasks()
        required_width = self.tabview.winfo_reqwidth() + 20
        required_height = self.tabview.winfo_reqheight() + 30
        self.geometry(f"{required_width}x{required_height}")
        self.deiconify()

    def _populate_zone_frame(self, parent_frame, zone):
        """Creates and packs the standard widgets for a lighting zone."""
        label = ctk.CTkLabel(
            parent_frame, text=zone.capitalize(), font=ctk.CTkFont(weight="bold")
        )
        label.pack(pady=(10, 0))

        mode_var = ctk.StringVar(value="Static")
        mode_selector = ctk.CTkSegmentedButton(
            parent_frame,
            values=["Static", "Spectrum"],
            variable=mode_var,
            command=lambda mode, z=zone: self.on_mode_change(z, mode),
        )
        mode_selector.pack(pady=(5, 0))
        self.mode_vars[zone] = mode_var

        # Use scroll color as a baseline for the 'all' controller
        initial_color_source = "scroll" if zone == "all" else zone
        initial_color = self.device_manager.get_color(initial_color_source) or (0, 0, 0)

        controller = ColorController(
            parent_frame, zone, initial_color, self.on_color_change
        )
        controller.pack(padx=5, pady=5)
        self.color_controllers[zone] = controller

    def on_closing(self):
        """Stops all animation threads before closing the app."""
        self._stop_all_animations()
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

    # _start_animation and _stop_animation helpers
    def _start_animation(self, zone):
        """Stops any existing thread for a zone and starts a new one."""
        if zone in self.animation_threads:
            self.animation_threads[zone].stop()
        
        animator = SpectrumAnimator(self.device_manager, zone, self._update_animator_ui)
        self.animation_threads[zone] = animator
        animator.start()

    def _stop_animation(self, zone):
        """Stops and removes the animation thread for a given zone."""
        if zone in self.animation_threads:
            self.animation_threads[zone].stop()
            del self.animation_threads[zone]

    def _stop_all_animations(self):
        """Stops all running animation threads."""
        for zone in list(self.animation_threads.keys()):
            self._stop_animation(zone)

    # on_mode_change now dispatches to cleaner helper methods
    def on_mode_change(self, zone: str, mode: str):
        """Handles mode changes from the UI."""
        if mode == "Spectrum":
            self._set_spectrum_mode(zone)
        elif mode == "Static":
            self._set_static_mode(zone)

    def _set_spectrum_mode(self, zone: str):
        """Activates Spectrum mode for a given zone."""
        if zone == "all":
            # Stop individual animations and start the 'all' animation
            for z in self.ZONES:
                self._stop_animation(z)
            self._start_animation("all")
            # Update all UI elements to reflect the new mode
            for z in self.color_controllers.keys():
                self.mode_vars[z].set("Spectrum")
                self.color_controllers[z].set_enabled(False)
        else:
            # Stop the 'all' animation if it's running
            self._stop_animation("all")
            self._start_animation(zone)
            # Update the specific UI element
            self.mode_vars[zone].set("Spectrum")
            self.color_controllers[zone].set_enabled(False)
            
            # If all individual zones are now spectrum, consolidate to a single 'all' animation
            if all(z in self.animation_threads for z in self.ZONES):
                self._set_spectrum_mode("all")

    def _set_static_mode(self, zone: str):
        """Activates Static mode for a given zone."""
        # Stop the relevant animation(s)
        if zone == "all":
            self._stop_all_animations()
        else:
            self._stop_animation(zone)
            self._stop_animation("all") # Changing an individual zone also stops the 'all' effect

        # Update UI state and apply color
        if zone == "all":
            for z in self.color_controllers.keys():
                self.mode_vars[z].set("Static")
                self.color_controllers[z].set_enabled(True)
            
            r, g, b = self._get_controller_color(self.color_controllers["all"])
            self.device_manager.set_color("all", r, g, b)
            # Ensure individual controllers show the same color
            for z in self.ZONES:
                self.color_controllers[z].update_color((r, g, b), source="global")
        else:
            self.mode_vars[zone].set("Static")
            self.color_controllers[zone].set_enabled(True)
            r, g, b = self._get_controller_color(self.color_controllers[zone])
            self.device_manager.set_color(zone, r, g, b)
            # Update the 'all' controller's UI if it was in spectrum mode
            if "all" in self.mode_vars and self.mode_vars["all"].get() == "Spectrum":
                self.mode_vars["all"].set("Static")
                self.color_controllers["all"].set_enabled(True)

    def _get_controller_color(self, controller: ColorController) -> tuple[int, int, int]:
        """Safely gets the RGB color from a ColorController."""
        try:
            r = int(controller.r_var.get())
            g = int(controller.g_var.get())
            b = int(controller.b_var.get())
            return r, g, b
        except (ValueError, ctk.TclError):
            return 0, 0, 0

    def on_color_change(self, zone: str, r: int, g: int, b: int):
        """Handles color changes from the ColorController, implying Static mode."""
        self._stop_all_animations()

        # Set the mode UI to Static for all affected zones
        if zone == "all":
            for z in self.mode_vars.keys():
                self.mode_vars[z].set("Static")
                self.color_controllers[z].set_enabled(True)
        else:
            self.mode_vars[zone].set("Static")
            if "all" in self.mode_vars:
                self.mode_vars["all"].set("Static")
                self.color_controllers["all"].set_enabled(True)

        # Set device color
        if zone == "all":
            self.device_manager.set_color("all", r, g, b)
            for z in self.ZONES:
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
