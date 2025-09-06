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

_control_center_instance = None


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
            monitor=0,
            layer="top",
            css_classes=["unset"],
            anchor=["top", "right", "bottom", "left"],
            namespace="ignis_CONTROL_CENTER",
            child=widgets.Box(
                child=[
                    widgets.Button(
                        vexpand=True,
                        hexpand=True,
                        css_classes=["unset"],
                        on_click=lambda x: window_manager.close_window("ignis_CONTROL_CENTER"),
                    ),
                    revealer,
                ],
            ),
            setup=lambda self: self.connect(
                "notify::visible", lambda x, y: opened_menu.set_value("")
            ),
            revealer=revealer,
        )

    def show_on_monitor(self, monitor_id: int):
        """Show the control center on the specified monitor"""
        if self.monitor != monitor_id:
            self.set_monitor(monitor_id)
        self.set_visible(True)

    def toggle_on_monitor(self, monitor_id: int):
        """Toggle the control center on the specified monitor"""
        if not self.visible:
            self.show_on_monitor(monitor_id)
        elif self.monitor == monitor_id:
            self.set_visible(False)
        else:
            self.show_on_monitor(monitor_id)


def get_control_center():
    global _control_center_instance
    if _control_center_instance is None:
        _control_center_instance = ControlCenter()
    return _control_center_instance
