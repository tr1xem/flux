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

def toggle_control_center(monitor: int):
    """Toggle or switch the control center window to the specified monitor"""
    window_name = "ignis_CONTROL_CENTER_0"
    window = window_manager.get_window(window_name)
    
    if window and hasattr(window, 'visible') and hasattr(window, 'monitor'):
        if window.visible and window.monitor == monitor:
            # Same monitor and visible - toggle off
            window.visible = False
        else:
            # Different monitor or not visible - switch and show
            if window.monitor != monitor:
                window.set_monitor(monitor)
            window.visible = True


class ControlCenter(widgets.RevealerWindow):
    def __init__(self, monitor_id: int = 0):
        # Always use monitor 0 for single instance, but store requested monitor  
        self.requested_monitor = monitor_id
        
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
            monitor=0,  # Always start on monitor 0 for single instance
            layer="top",
            css_classes=["unset"],
            anchor=["top", "right", "bottom", "left"],
            namespace="ignis_CONTROL_CENTER_0",  # Always use 0 for single instance
            child=widgets.Box(
                child=[
                    widgets.Button(
                        vexpand=True,
                        hexpand=True,
                        css_classes=["unset"],
                        on_click=lambda x: window_manager.close_window("ignis_CONTROL_CENTER_0"),
                    ),
                    revealer,
                ],
            ),
            setup=lambda self: self.connect(
                "notify::visible", lambda x, y: opened_menu.set_value("")
            ),
            revealer=revealer,
        )
