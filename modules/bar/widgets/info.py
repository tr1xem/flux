from ignis import utils, widgets
from ignis.services.fetch import FetchService


class Info(widgets.CenterBox):
    def __init__(self):
        super().__init__(
            css_classes=["info-box"],
        )

        self.fetch = FetchService.get_default()

        self.osLogo = widgets.Picture(
            image=self.fetch.os_logo,
            css_classes=["os-logo"],
            # hexpand=True,
            height=40,
            width=40,
            # pixel_size=40,
        )
        self.osName = widgets.Label(
            label=self.fetch.os_name,
            css_classes=["os-name"],
            justify="left",
            halign="start",
        )
        self.osKernel = widgets.Label(
            label=self.fetch.kernel,
            css_classes=["os-kernel"],
            justify="left",
            halign="start",
        )
        self.ramUsage = widgets.Scale(
            css_classes=["usage-slider"],
            # value=self.fetch.bind("mem_used", lambda x: (x / self.fetch.mem_total) * 100),
            sensitive=False,
            hexpand=True,
            min=0,
            max=100,
            on_change=lambda x: print(x.value),
        )

        utils.Poll(
            1000,
            lambda _: self.ramUsage.set_value(
                self.fetch.mem_used / self.fetch.mem_total * 100
            ),
        )

        self.start_widget = widgets.Box(
            hexpand=True,
            vertical=False,
            child=[
                self.osLogo,
                widgets.Box(
                    vertical=True,
                    spacing=3,
                    hexpand=True,
                    valign="center",
                    halign="start",
                    child=[self.osName, self.osKernel],
                ),
            ],
        )
        self.end_widget = widgets.Box(
            hexpand=True,
            vertical=False,
            halign="end",
            child=[self.ramUsage],
        )
