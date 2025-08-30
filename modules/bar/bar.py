from ignis import widgets

from .widgets.workspaces import Workspaces


class CentreBar(widgets.Box):
    def __init__(self):
        super().__init__(css_classes=["bar-center"], hexpand=True)
        # self.append(Media())
        # self.append(Info())


class Bar(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            namespace="ignis_bar",
            monitor=monitor_id,
            css_classes=["bar-window"],
            anchor=["top", "left", "right"],
            exclusivity="exclusive",
            child=widgets.CenterBox(
                hexpand=True,
                start_widget=widgets.Box(
                    css_classes=["bar-start"],
                    hexpand=True,
                    halign="start",
                    child=[Workspaces()],
                ),
                center_widget=widgets.Box(
                    hexpand=True,
                    css_classes=["bar-center"],
                    child=[CentreBar()],
                ),
                end_widget=widgets.Box(
                    hexpand=True,
                    css_classes=["bar-end"],
                    child=[],
                ),
            ),
        )
