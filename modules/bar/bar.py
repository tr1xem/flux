import datetime

from ignis import utils, widgets
from ignis.variable import Variable

from .widgets import CpuUsage, Player, RamUsage, StatusPill, Tray, Weather, Workspaces


class Datetime(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["datetime"],
        )
        self.current_time = Variable(
            value=utils.Poll(
                1000,
                lambda x: datetime.datetime.now().strftime("<b>%I:%M</b> • %A, %-d %b"),
            ).bind("output")
        )
        self.time = widgets.Label(
            label=self.current_time.bind("value"),
            use_markup=True,
        )
        self.append(self.time)


class CentreBar(widgets.Box):
    def __init__(self):
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
        self.append(Player())
        self.append(Workspaces(0))
        self.append(Weather())
        self.append(Datetime())


class Bar(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            namespace="ignis_BAR",
            monitor=monitor_id,
            css_classes=["bar-window"],
            anchor=["top", "left", "right"],
            exclusivity="exclusive",
            child=widgets.CenterBox(
                hexpand=True,
                start_widget=widgets.Box(
                    css_classes=["bar-start"],
                    hexpand=True,
                    vexpand=True,
                    valign="center",
                    halign="center",
                    child=[],
                ),
                center_widget=widgets.Box(
                    hexpand=True,
                    vexpand=True,
                    css_classes=["bar-center"],
                    halign="center",
                    child=[CentreBar()],
                ),
                end_widget=widgets.Box(
                    hexpand=True,
                    css_classes=["bar-end"],
                    halign="end",
                    child=[Tray(), StatusPill(monitor_id)],
                ),
            ),
        )
