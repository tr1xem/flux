import asyncio

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
                        transform=lambda value: [BluetoothDeviceItem(i) for i in value]
                        if value
                        else [
                            widgets.Label(
                                label="No devices found"
                                if bluetooth.state != "absent"
                                else "Service integration issue",
                                halign="center",
                                css_classes=["dim-label"],
                            )
                        ],
                    ),
                ),
            ],
        )


class BluetoothButton(QSButton):
    def __init__(self):
        menu = BluetoothMenu()

        def toggle_menu(x) -> None:
            bluetooth.set_setup_mode(True)
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
