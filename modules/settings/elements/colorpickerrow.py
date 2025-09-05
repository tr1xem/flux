from ignis import widgets
from .row import SettingsRow
from typing import Callable
import subprocess


class ColorPickerRow(SettingsRow):
    def __init__(
        self,
        color: str = "#FFFFFF",
        on_change: Callable | None = None,
        **kwargs,
    ):
        # Create a colored button that shows the current color
        self._color_display = widgets.Box(
            css_classes=["color-picker-display"],
            width_request=40,
            height_request=25,
        )
        
        self._button = widgets.Button(
            child=self._color_display,
            on_click=self._open_color_picker,
            css_classes=["color-picker-button"],
            halign="end",
        )
        
        self._on_change = on_change
        self._current_color = color
        self._set_color(color)
        
        super().__init__(additional_widgets=[self._button], **kwargs)
    
    def _set_color(self, color_hex: str):
        """Set the color and update the display"""
        self._current_color = color_hex
        self._color_display.set_style(f"background-color: {color_hex}; border: 1px solid #ccc; border-radius: 3px;")
    
    def _open_color_picker(self, *args):
        """Open system color picker using zenity"""
        try:
            # Use zenity color picker
            result = subprocess.run([
                "zenity", "--color-selection", 
                f"--color={self._current_color}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # zenity returns rgb(r,g,b) format, convert to hex
                color_str = result.stdout.strip()
                if color_str.startswith("rgb("):
                    # Parse rgb(r,g,b) to hex
                    rgb_values = color_str[4:-1].split(",")
                    r, g, b = [int(val.strip()) for val in rgb_values]
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    hex_color = color_str
                
                self._set_color(hex_color)
                if self._on_change:
                    self._on_change(hex_color)
                    
        except FileNotFoundError:
            # Fallback to a simple text entry if zenity is not available
            print("Zenity not found, color picker unavailable")