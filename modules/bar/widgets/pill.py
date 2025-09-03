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


class StatusPill(widgets.EventBox):
    def __init__(self, monitor: int):
        self._monitor = monitor
        self._window = window_manager.get_window(f"ignis_CONTROL_CENTER_{monitor}")

        super().__init__(
            child=[
                widgets.Box(
                    css_classes=["status-pill"],
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
                )
            ],
            on_click=self.__on_click,
        )

    def __on_click(self, x) -> None:
        if self._window.monitor == self._monitor:
            self._window.visible = not self._window.visible
        else:
            self._window.set_monitor(self._monitor)
            self._window.visible = True
