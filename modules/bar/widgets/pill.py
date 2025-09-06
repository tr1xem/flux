import datetime
import subprocess

from ignis import utils, widgets
from ignis.options import options
from ignis.services.audio import AudioService
from ignis.services.bluetooth import BluetoothService
from ignis.services.network import NetworkService
from ignis.services.notifications import NotificationService
from ignis.services.recorder import RecorderService
from ignis.services.upower import UPowerDevice, UPowerService
from ignis.variable import Variable
from ignis.window_manager import WindowManager

from ..indicator_icon import IndicatorIcon, NetworkIndicatorIcon
from ...control_center import get_control_center

network = NetworkService.get_default()
notifications = NotificationService.get_default()
recorder = RecorderService.get_default()
audio = AudioService.get_default()
bluetooth = BluetoothService.get_default()
upower = UPowerService.get_default()

window_manager = WindowManager.get_default()

current_time = Variable(
    value=utils.Poll(1000, lambda x: datetime.datetime.now().strftime("%H:%M")).bind(
        "output"
    )
)


def check_recording_processes(*args) -> bool:
    """Check if any screen recording processes are running"""
    recording_processes = [
        "wf-recorder",
        "wl-screenrec",
        "gpu-screen-recorder",
        "obs",
        "ffmpeg",
        "grim",
    ]

    try:
        # Get list of all running processes
        result = subprocess.run(
            ["ps", "ax", "-o", "comm="], capture_output=True, text=True, check=True
        )

        running_processes = result.stdout.strip().split("\n")

        # Check if any recording process is running
        for process in recording_processes:
            if any(process in running_proc for running_proc in running_processes):
                return True

        return False

    except subprocess.CalledProcessError:
        # If ps command fails, assume no recording
        return False


recording_status = Variable(
    value=utils.Poll(1000, check_recording_processes).bind("output")
)


class WifiIcon(NetworkIndicatorIcon):
    def __init__(self):
        super().__init__(device_type=network.wifi, other_device_type=network.ethernet)


class EthernetIcon(NetworkIndicatorIcon):
    def __init__(self):
        super().__init__(device_type=network.ethernet, other_device_type=network.wifi)


class VpnIcon(IndicatorIcon):
    def __init__(self):
        super().__init__(
            image=network.vpn.bind("icon_name"),
            visible=network.vpn.bind("is_connected"),
        )


class DNDIcon(IndicatorIcon):
    def __init__(self):
        super().__init__(
            image="notification-disabled-symbolic",
            visible=options.notifications.bind("dnd"),
        )


class RecorderIcon(IndicatorIcon):
    def __init__(self):
        super().__init__(
            image="media-record-symbolic",
            css_classes=["record-indicator"],
            visible=recording_status.bind("value"),
        )
        self.add_css_class("active")


class VolumeIcon(IndicatorIcon):
    def __init__(self):
        super().__init__(
            image=audio.speaker.bind("icon_name"),
        )


class BluetoothIcon(IndicatorIcon):
    def __init__(self):
        def get_icon_name() -> str:
            if not bluetooth.powered:
                return "bluetooth-disabled-symbolic"
            elif len(bluetooth.connected_devices) > 0:
                return "bluetooth-active-symbolic"
            else:
                return "bluetooth-symbolic"

        super().__init__(
            image=bluetooth.bind("powered", transform=lambda x: get_icon_name()),
            visible=bluetooth.bind("state", transform=lambda state: state != "absent"),
        )


class BatteryItem(widgets.Box):
    def __init__(self, device: UPowerDevice):
        super().__init__(
            css_classes=["battery-item"],
            spacing=4,
            setup=lambda self: device.connect("removed", lambda x: self.unparent()),
            child=[
                widgets.Icon(
                    icon_name=device.bind("icon_name"), css_classes=["battery-icon"]
                ),
                widgets.Label(
                    label=device.bind("percent", lambda x: f"{int(x)}%"),
                    css_classes=["battery-percent"],
                ),
                widgets.Scale(
                    min=0,
                    max=100,
                    value=device.bind("percent"),
                    sensitive=False,
                    css_classes=["battery-scale"],
                ),
            ],
        )


class Battery(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["rec-unset"],
            setup=lambda self: upower.connect(
                "battery-added", lambda x, device: self.append(BatteryItem(device))
            ),
        )


class StatusPill(widgets.Button):
    def __init__(self, monitor: int):
        self._monitor = monitor
        self._control_center = get_control_center()

        super().__init__(
            child=widgets.Box(
                spacing=5,
                child=[
                    RecorderIcon(),
                    BluetoothIcon(),
                    WifiIcon(),
                    EthernetIcon(),
                    VpnIcon(),
                    VolumeIcon(),
                    DNDIcon(),
                    Battery(),
                ],
            ),
            on_click=self.__on_click,
            css_classes=["status-pill"],
        )

        # Connect to control center visibility changes to update styling
        self._control_center.connect("notify::visible", self._on_visibility_changed)
        self._update_classes()

    def _on_visibility_changed(self, *args):
        """Update CSS classes when control center visibility changes"""
        self._update_classes()

    def _update_classes(self):
        """Update CSS classes based on control center visibility"""
        if self._control_center.visible:
            self.css_classes = ["status-pill", "status-active"]
        else:
            self.css_classes = ["status-pill"]

    def __on_click(self, x) -> None:
        self._control_center.toggle_on_monitor(self._monitor)
