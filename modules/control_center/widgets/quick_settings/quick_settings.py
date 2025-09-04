from ignis import widgets
from ignis.services.network import NetworkService

from ...qs_button import QSButton
from .bluetooth import bluetooth_control
from .dark_mode import DarkModeButton
from .dnd import DNDButton
from .ethernet import ethernet_control
from .idle_inhibitor import IdleInhibitorButton
from .nightlight import NightModeButton
from .power_profiles import PowerProfilesButton
from .record import RecordButton
from .vpn import vpn_control
from .wifi import wifi_control

network = NetworkService.get_default()


class QuickSettings(widgets.Box):
    def __init__(self):
        super().__init__(vertical=True, css_classes=["qs-main-box"])
        network.wifi.connect("notify::devices", lambda x, y: self.__refresh())
        network.ethernet.connect("notify::devices", lambda x, y: self.__refresh())
        network.vpn.connect("notify::connections", lambda x, y: self.__refresh())

        self.__refresh()

    def __refresh(self) -> None:
        self.child = []
        self.__configure()

    def __configure(self) -> None:
        self.__qs_fabric(
            *wifi_control(),
            *ethernet_control(),
            *vpn_control(),
            *bluetooth_control(),
            DNDButton(),
            DarkModeButton(),
            PowerProfilesButton(),
            IdleInhibitorButton(),
            RecordButton(),
            NightModeButton(),
        )

    def __qs_fabric(self, *buttons: QSButton) -> None:
        for i in range(0, len(buttons), 2):
            self.__add_row(buttons, i)

    def __add_row(self, buttons: tuple[QSButton, ...], i: int) -> None:
        row = widgets.Box(homogeneous=True)
        if len(self.child) > 0:
            row.style = "margin-top: 0.5rem;"

        self.append(row)

        button1 = buttons[i]

        self.__add_button(row, button1, buttons, i)

        if i + 1 < len(buttons):
            button2 = buttons[i + 1]
            button2.style = "margin-left: 0.5rem;"
            self.__add_button(row, button2, buttons, i)

    def __add_button(
        self, row: widgets.Box, button: QSButton, buttons: tuple[QSButton, ...], i: int
    ) -> None:
        row.append(button)

        if button.menu:
            self.append(button.menu)

            if i == len(buttons) - 1 or i == len(buttons) - 2:
                button.menu.box.add_css_class("control-center-menu-last-row")
