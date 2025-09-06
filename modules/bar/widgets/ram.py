from ignis import widgets
from ignis.services.fetch import FetchService
from ignis.utils import Poll

from ...shared_widgets.circular_progress import CircularProgressBar

fetch = FetchService.get_default()


class RamUsage(widgets.Box):
    def __init__(self) -> None:
        super().__init__(
            css_classes=["bar-ram"],
            spacing=4,
            vexpand=True,
            hexpand=True,
        )

        self._ram_progress = CircularProgressBar(
            line_width=2,
            size=(23, 23),
            start_angle=270,
            pie=True,
            end_angle=630,
            css_classes=["progress-ram"],
            max_value=fetch.mem_total,
            value=0,
        )
        # Reduce polling frequency to save memory and CPU
        Poll(2000, lambda x: self._ram_progress.set_value(fetch.mem_used))

        self._ram_icon = widgets.Label(
            css_classes=["ram-icon"],
            valign="center",
            label="",
        )

        self._ram_overlay = widgets.Overlay(
            child=self._ram_progress,
            halign="center",
            overlays=[self._ram_icon],
            hexpand=True,
            vexpand=True,
        )

        self._ram_label = widgets.Label(
            valign="center",
            halign="start",
            css_classes=["ram-label"],
        )
        # Reduce polling frequency to save memory and CPU  
        Poll(
            2000,
            lambda x: setattr(
                self._ram_label,
                "label",
                f"{fetch.mem_used / 1024 / 1024:.1f}/{fetch.mem_total / 1024 / 1024:.1f} GB",
            ),
        )

        self.append(self._ram_overlay)
        self.append(self._ram_label)
