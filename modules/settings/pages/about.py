import glob
import os
import re
import shutil

from ignis import widgets
from ignis._version import __version__
from ignis.services.fetch import FetchService

from user_options import user_options

from ..elements import SettingsEntry, SettingsGroup, SettingsPage, SettingsRow

fetch = FetchService.get_default()


def get_os_logo(dark_mode: bool) -> str | None:
    if dark_mode:
        return fetch.os_logo_text_dark or fetch.os_logo_dark or fetch.os_logo
    else:
        return fetch.os_logo_text or fetch.os_logo


total, used, free = shutil.disk_usage("/")
partition_size = total / (1024**3)


def get_wifi_driver_name():
    wireless_interfaces = glob.glob("/sys/class/net/*/wireless")
    if not wireless_interfaces:
        return None

    wifi_if = wireless_interfaces[0].split("/")[-2]

    driver_link = f"/sys/class/net/{wifi_if}/device/driver"
    if os.path.islink(driver_link):
        driver_path = os.readlink(driver_link)
        driver_name = driver_path.split("/")[-1]
        return driver_name
    return None


def is_secure_boot_enabled():
    path = "/sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"
    if not os.path.exists(path):
        return None  # Not booted in UEFI mode, or efivars not available
    try:
        with open(path, "rb") as f:
            data = f.read()
            return data[4] == 1  # 5th byte
    except Exception:
        return None


class AboutEntry(SettingsEntry):
    def __init__(self):
        page = SettingsPage(
            name="About",
            groups=[
                widgets.Icon(
                    icon_name=user_options.material.bind(
                        "dark_mode",
                        transform=lambda value: get_os_logo(value),
                    ),
                    pixel_size=200,
                ),
                SettingsGroup(
                    name="System Info",
                    rows=[
                        widgets.Grid(
                            column_num=2,
                            hexpand=True,
                            child=[
                                SettingsRow(
                                    width_request=330,
                                    label="Operating System",
                                    sublabel=fetch.os_name,
                                ),
                                SettingsRow(label="Hostname", sublabel=fetch.hostname),
                                SettingsRow(
                                    label="Ignis Version", sublabel=__version__
                                ),
                                SettingsRow(
                                    label="Session type", sublabel=fetch.session_type
                                ),
                                SettingsRow(
                                    label="Wayland compositor",
                                    sublabel=fetch.current_desktop,
                                ),
                                SettingsRow(label="Kernel", sublabel=fetch.kernel),
                            ],
                        ),
                    ],
                ),
                SettingsGroup(
                    name="Hardware Info",
                    rows=[
                        widgets.Grid(
                            column_num=2,
                            hexpand=True,
                            child=[
                                SettingsRow(
                                    width_request=330,
                                    label="    CPU",
                                    sublabel=fetch.cpu,
                                ),
                                SettingsRow(
                                    label="    RAM",
                                    sublabel=f"{fetch.mem_total / 1024 / 1024:.1f} GB",
                                ),
                                SettingsRow(
                                    label="🖴   Root Partition",
                                    sublabel=f"{partition_size} GB",
                                ),
                                SettingsRow(
                                    label="󱚾    Wifi Driver",
                                    sublabel=get_wifi_driver_name(),
                                ),
                                SettingsRow(
                                    label="Motherboard", sublabel=fetch.board_vendor
                                ),
                                SettingsRow(
                                    label="UEFI Version", sublabel=fetch.board_name
                                ),
                                SettingsRow(
                                    label="Secure Boot",
                                    sublabel="Enabled"
                                    if is_secure_boot_enabled()
                                    else "Disabled",
                                ),
                            ],
                        )
                    ],
                ),
            ],
        )
        super().__init__(
            label="About",
            icon="help-about-symbolic",
            page=page,
        )
