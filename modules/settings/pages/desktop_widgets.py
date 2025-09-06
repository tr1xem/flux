from user_options import user_options
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

from ..elements import (
    SettingsEntry,
    SettingsGroup,
    SettingsPage,
    SwitchRow,
    ButtonRow,
    SpinRow,
)


def open_color_picker(current_color, title, callback):
    """Global GTK color picker function using native ColorChooserDialog"""
    dialog = Gtk.ColorChooserDialog.new(title, None)
    dialog.set_modal(True)

    # Set current color if valid
    try:
        rgba = Gdk.RGBA()
        if rgba.parse(current_color):
            dialog.set_rgba(rgba)
    except Exception:
        pass

    def on_response(dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            rgba = dialog.get_rgba()
            # Convert RGBA to hex
            r = int(rgba.red * 255)
            g = int(rgba.green * 255)
            b = int(rgba.blue * 255)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            callback(hex_color)
        dialog.destroy()

    dialog.connect("response", on_response)
    dialog.present()


class DesktopWidgetsEntry(SettingsEntry):
    def __init__(self):
        page = SettingsPage(
            name="Desktop Widgets",
            groups=[
                SettingsGroup(
                    name="Time Widget",
                    rows=[
                        SwitchRow(
                            label="Time Widget",
                            sublabel="Show movable Time widget on desktop",
                            active=user_options.desktop_widgets.bind("time_enabled"),
                            on_change=(
                                lambda x,
                                state: user_options.desktop_widgets.set_time_enabled(
                                    state
                                )
                            ),
                        ),
                        SwitchRow(
                            label="Custom Color",
                            sublabel="Use custom color instead of default theme color",
                            active=user_options.time.bind("use_custom_color"),
                            on_change=(
                                lambda x, state: user_options.time.set_use_custom_color(
                                    state
                                )
                            ),
                        ),
                        ButtonRow(
                            label="Choose Color",
                            sublabel="Click to choose custom color (only works when Custom Color is enabled)",
                            button_label="Pick Color",
                            on_click=lambda *args: self._open_time_color_picker(),
                        ),
                        SpinRow(
                            label="Font Size",
                            sublabel="Font size for the time widget (in pixels)",
                            value=user_options.time.bind("font_size"),
                            min=1,
                            max=999,
                            step=1,
                            on_change=(
                                lambda x, value: user_options.time.set_font_size(
                                    int(value)
                                )
                            ),
                        ),
                        SwitchRow(
                            label="Time Positioning Mode",
                            sublabel="Enable to move time widget to top layer for repositioning",
                            active=user_options.desktop_widgets.bind("time_positioning_mode"),
                            on_change=(
                                lambda x,
                                state: user_options.desktop_widgets.set_time_positioning_mode(
                                    state
                                )
                            ),
                        ),
                    ],
                ),
                SettingsGroup(
                    name="Date Widget",
                    rows=[
                        SwitchRow(
                            label="Date Widget",
                            sublabel="Show movable date widget on desktop",
                            active=user_options.desktop_widgets.bind("date_enabled"),
                            on_change=(
                                lambda x,
                                state: user_options.desktop_widgets.set_date_enabled(
                                    state
                                )
                            ),
                        ),
                        SwitchRow(
                            label="Custom Color",
                            sublabel="Use custom color instead of default theme color",
                            active=user_options.date.bind("use_custom_color"),
                            on_change=(
                                lambda x, state: user_options.date.set_use_custom_color(
                                    state
                                )
                            ),
                        ),
                        ButtonRow(
                            label="Choose Color",
                            sublabel="Click to choose custom color (only works when Custom Color is enabled)",
                            button_label="Pick Color",
                            on_click=lambda *args: self._open_date_color_picker(),
                        ),
                        SpinRow(
                            label="Font Size",
                            sublabel="Font size for the date widget (in pixels)",
                            value=user_options.date.bind("font_size"),
                            min=1,
                            max=999,
                            step=1,
                            on_change=(
                                lambda x, value: user_options.date.set_font_size(
                                    int(value)
                                )
                            ),
                        ),
                        SwitchRow(
                            label="Date Positioning Mode",
                            sublabel="Enable to move date widget to top layer for repositioning",
                            active=user_options.desktop_widgets.bind("date_positioning_mode"),
                            on_change=(
                                lambda x,
                                state: user_options.desktop_widgets.set_date_positioning_mode(
                                    state
                                )
                            ),
                        ),
                    ],
                ),
                SettingsGroup(
                    name="Widget Positioning",
                    rows=[
                        SwitchRow(
                            label="Change Position Mode",
                            sublabel="Enable to move widgets to top layer for repositioning. Turn off when done to move back to desktop.",
                            active=user_options.desktop_widgets.bind("positioning_mode"),
                            on_change=(
                                lambda x,
                                state: user_options.desktop_widgets.set_positioning_mode(
                                    state
                                )
                            ),
                        ),
                    ],
                ),
            ],
        )
        super().__init__(
            label="Desktop Widgets",
            icon="preferences-desktop-wallpaper-symbolic",
            page=page,
        )

    def _open_time_color_picker(self):
        """Open color picker for time widget"""
        if not user_options.time.use_custom_color:
            print("Enable Custom Color first to use color picker for time widget")
            return

        open_color_picker(
            user_options.time.color,
            "Time Widget Color",
            lambda color: user_options.time.set_color(color),
        )

    def _open_date_color_picker(self):
        """Open color picker for date widget"""
        if not user_options.date.use_custom_color:
            print("Enable Custom Color first to use color picker for date widget")
            return

        open_color_picker(
            user_options.date.color,
            "Date Widget Color",
            lambda color: user_options.date.set_color(color),
        )
