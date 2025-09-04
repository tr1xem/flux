from ignis import widgets
from ignis.window_manager import WindowManager

from .menu import opened_menu
from .widgets import (
    Brightness,
    NotificationCenter,
    QuickSettings,
    User,
    VolumeSlider,
)

window_manager = WindowManager.get_default()


class ControlCenter(widgets.RevealerWindow):
    def __init__(self, monitor_id: int = 0):
        revealer = widgets.Revealer(
            transition_type="slide_left",
            child=widgets.Box(
                vertical=True,
                css_classes=["control-center"],
                child=[
                    widgets.Box(
                        vertical=True,
                        css_classes=["control-center-widget"],
                        child=[
                            User(),
                            QuickSettings(),
                            VolumeSlider("speaker"),
                            VolumeSlider("microphone"),
                            Brightness(),
                        ],
                    ),
                    NotificationCenter(),
                ],
            ),
            transition_duration=300,
            reveal_child=True,
        )

        super().__init__(
            visible=False,
            popup=True,
            kb_mode="on_demand",
            monitor=monitor_id,
            layer="top",
            css_classes=["unset"],
            anchor=["top", "right", "bottom", "left"],
            namespace=f"ignis_CONTROL_CENTER_{monitor_id}",
            child=widgets.Box(
                child=[
                    widgets.Button(
                        vexpand=True,
                        hexpand=True,
                        css_classes=["unset"],
                        on_click=lambda x: window_manager.close_window(
                            f"ignis_CONTROL_CENTER_{monitor_id}"
                        ),
                    ),
                    revealer,
                ],
            ),
            setup=lambda self: self.connect(
                "notify::visible", lambda x, y: opened_menu.set_value("")
            ),
            revealer=revealer,
        )
