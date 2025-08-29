from ignis import widgets

from .widgets.player import Media


class CentreBar(widgets.Box):
    def __init__(self):
        super().__init__(
            hexpand=True,
            vexpand=True,
            css_classes=["bar-center"],
        )
        self.append(Media())


class Bar(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            namespace="ignis_bar",
            monitor=monitor_id,
            css_classes=["bar-window"],
            anchor=["left", "top", "right"],
            exclusivity="exclusive",
            child=widgets.CenterBox(
                start_widget=widgets.Box(
                    css_classes=["bar-start"],
                    child=[],
                ),
                center_widget=widgets.Box(
                    css_classes=["bar-center"],
                    child=[CentreBar()],
                ),
                end_widget=widgets.Box(
                    css_classes=["bar-end"],
                    child=[],
                ),
            ),
        )
