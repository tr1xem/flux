import asyncio
import time

from ignis import widgets
from ignis.services.bluetooth import BluetoothDevice, BluetoothService

from ....shared_widgets import ToggleBox
from ...menu import Menu
from ...qs_button import QSButton

bluetooth = BluetoothService.get_default()


class BluetoothDeviceItem(widgets.Button):
    def __init__(self, device: BluetoothDevice):
        def handle_click(x):
            if device.connected:
                asyncio.create_task(device.disconnect_from())
            else:
                asyncio.create_task(device.connect_to())

        super().__init__(
            css_classes=["network-item", "unset"],
            on_click=handle_click,
            child=widgets.Box(
                child=[
                    widgets.Icon(
                        image=device.bind("icon_name"),
                    ),
                    widgets.Label(
                        label=device.alias,
                        halign="start",
                        css_classes=["wifi-network-label"],
                    ),
                    widgets.Icon(
                        image="object-select-symbolic",
                        halign="end",
                        hexpand=True,
                        visible=device.bind("connected"),
                    ),
                ]
            ),
        )


class BluetoothMenu(Menu):
    def __init__(self):
        self._setup_mode_enabled = False
        
        super().__init__(
            name="bluetooth",
            child=[
                ToggleBox(
                    label="Bluetooth",
                    active=bluetooth.bind("powered"),
                    on_change=lambda x, state: bluetooth.set_powered(state),
                    css_classes=["network-header-box"],
                ),
                widgets.Box(
                    vertical=True,
                    child=bluetooth.bind(
                        "devices",
                        transform=self._transform_devices,
                    ),
                ),
            ],
        )
        
        # Connect to reveal state changes to enable setup mode only when expanded
        self.connect("notify::reveal-child", self._on_reveal_changed)
    
    def _on_reveal_changed(self, *args):
        """Called when the menu is expanded or collapsed"""
        if self.reveal_child:
            self.enable_setup_mode_if_needed()
    
    def _transform_devices(self, devices):
        """Transform device list into widgets, with caching to reduce recreation"""
        if not devices:
            return [widgets.Label(
                label="No devices found" if bluetooth.state != "absent" else "Service integration issue",
                halign="center",
                css_classes=["dim-label"],
            )]
        return [BluetoothDeviceItem(device) for device in devices]
    
    def enable_setup_mode_if_needed(self):
        """Enable setup mode only when the menu is actually opened and needs fresh device scan"""
        if not self._setup_mode_enabled:
            bluetooth.set_setup_mode(True)
            self._setup_mode_enabled = True


class BluetoothButton(QSButton):
    def __init__(self):
        menu = BluetoothMenu()

        def toggle_menu(x) -> None:
            menu.toggle()

        def get_label(state: str, devices: list[BluetoothDevice]) -> str:
            if state == "absent":
                return "Bluetooth"
            elif len(devices) == 0:
                return "No Connection"
            elif len(devices) >= 1:
                name = devices[0].alias
                return name[:14] + "..." if len(name) > 12 else name
            return "Bluetooth"

        super().__init__(
            label=bluetooth.bind_many(
                ["state", "connected_devices"],
                get_label,
            ),
            icon_name="bluetooth-active-symbolic",
            on_activate=toggle_menu,
            on_deactivate=toggle_menu,
            active=bluetooth.bind("powered"),
            menu=menu,
        )
        # utils.Poll(
        #     1000, lambda x: self.set_label(get_label(bluetooth.connected_devices))
        # )


def bluetooth_control() -> list[QSButton]:
    return [BluetoothButton()]  # Always show the button
