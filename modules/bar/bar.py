import datetime

from ignis import utils, widgets
from ignis.variable import Variable

from .widgets import (
    CpuUsage,
    Datetime,
    Player,
    RamUsage,
    StatusPill,
    Tray,
    Weather,
    WindowTitle,
    Workspaces,
)


class CentreBar(widgets.Box):
    def __init__(self, monitor_id: int = 0):
        super().__init__(css_classes=["bar-center"], hexpand=True, spacing=9)
        self.append(
            widgets.Box(
                css_classes=["usage"],
                spacing=9,
                child=[
                    CpuUsage(),
                    RamUsage(),
                ],
            )
        )
        self.append(Player(monitor_id))
        self.append(Workspaces(monitor_id))
        self.append(Weather())
        self.append(Datetime(monitor_id))


class Bar(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            namespace=f"ignis_BAR_{monitor_id}",
            monitor=monitor_id,
            css_classes=["bar-window"],
            anchor=["top", "left", "right"],
            exclusivity="exclusive",
            child=widgets.CenterBox(
                hexpand=True,
                vexpand=True,
                start_widget=widgets.Box(
                    css_classes=["bar-start"],
                    hexpand=True,
                    vexpand=True,
                    valign="fill",
                    halign="start",
                    child=[WindowTitle()],
                ),
                center_widget=widgets.Box(
                    hexpand=True,
                    vexpand=True,
                    css_classes=["bar-center"],
                    halign="center",
                    child=[CentreBar(monitor_id)],
                ),
                end_widget=widgets.Box(
                    hexpand=True,
                    css_classes=["bar-end"],
                    halign="end",
                    child=[Tray(), StatusPill(monitor_id)],
                ),
            ),
        )
