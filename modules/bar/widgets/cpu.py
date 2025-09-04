from ignis import widgets
from ignis.services.fetch import FetchService
from ignis.utils import Poll

from ...shared_widgets.circular_progress import CircularProgressBar

fetch = FetchService.get_default()


class CpuUsage(widgets.Box):
    def __init__(self) -> None:
        super().__init__(
            css_classes=["bar-cpu"],
            spacing=4,
            vexpand=True,
            hexpand=True,
        )

        Poll(5000, lambda _: self.set_tooltip_text(f"CPU Temp: {fetch.cpu_temp}°C"))
        self._cpu_progress = CircularProgressBar(
            line_width=2,
            size=(23, 23),
            start_angle=270,
            pie=True,
            end_angle=630,
            css_classes=["progress-cpu"],
            max_value=100,
            value=0,
        )

        self._cpu_icon = widgets.Label(
            css_classes=["cpu-icon"],
            valign="center",
            label="",
        )

        self._cpu_overlay = widgets.Overlay(
            child=self._cpu_progress,
            halign="center",
            overlays=[self._cpu_icon],
            hexpand=True,
            vexpand=True,
        )

        self._cpu_label = widgets.Label(
            valign="center",
            halign="start",
            css_classes=["cpu-label"],
            label="0%",
        )

        self.append(self._cpu_overlay)
        self.append(self._cpu_label)

        # Track previous CPU stats for calculation
        self._prev_idle = 0
        self._prev_total = 0

        # Poll CPU usage every 2 seconds
        self._poll = Poll(
            timeout=2000,
            callback=self._update_cpu_usage,
        )

    def _get_cpu_stats(self):
        with open("/proc/stat", "r") as f:
            line = f.readline().strip()

        cpu_times = [int(x) for x in line.split()[1:]]
        idle_time = cpu_times[3]
        total_time = sum(cpu_times)

        return idle_time, total_time

    def _update_cpu_usage(self, poll_instance) -> float:
        idle_time, total_time = self._get_cpu_stats()

        # Calculate CPU usage percentage
        if self._prev_total != 0:
            idle_diff = idle_time - self._prev_idle
            total_diff = total_time - self._prev_total

            if total_diff > 0:
                cpu_percent = (1 - idle_diff / total_diff) * 100
            else:
                cpu_percent = 0
        else:
            cpu_percent = 0

        self._prev_idle = idle_time
        self._prev_total = total_time

        # Update UI
        setattr(self._cpu_progress, "value", cpu_percent)
        self._cpu_label.label = f"{cpu_percent:.0f}%"

        return cpu_percent
