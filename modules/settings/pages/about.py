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


def lookup_gpu_name(vendor_id, device_id):
    """Fast lookup GPU name in PCI database"""
    try:
        pci_ids_path = "/usr/share/hwdata/pci.ids"
        if not os.path.exists(pci_ids_path):
            return None

        vendor_hex = vendor_id.replace("0x", "").lower()
        device_hex = device_id.replace("0x", "").lower()

        with open(pci_ids_path, "r", encoding="utf-8", errors="ignore") as f:
            in_vendor = False
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                # Vendor line (no leading whitespace)
                if not line.startswith(("\t", " ")) and " " in stripped:
                    vendor_code = stripped.split()[0].lower()
                    in_vendor = vendor_code == vendor_hex

                # Device line (starts with tab, no subsystem)
                elif (
                    in_vendor and line.startswith("\t") and not line.startswith("\t\t")
                ):
                    parts = stripped.split(None, 1)
                    if len(parts) >= 2:
                        device_code = parts[0].lower()
                        if device_code == device_hex:
                            return parts[1]
        return None
    except Exception:
        return None


def detect_gpu_from_card(card_path):
    """Extract GPU info from a DRM card path"""
    try:
        device_path = os.path.join(card_path, "device")
        if not os.path.exists(device_path):
            return None

        # Read vendor and device IDs
        vendor_path = os.path.join(device_path, "vendor")
        device_id_path = os.path.join(device_path, "device")

        if not (os.path.exists(vendor_path) and os.path.exists(device_id_path)):
            return None

        with open(vendor_path, "r") as f:
            vendor_id = f.read().strip()
        with open(device_id_path, "r") as f:
            device_id = f.read().strip()

        # Get driver name
        driver_path = os.path.join(device_path, "driver")
        driver_name = None
        if os.path.islink(driver_path):
            driver_name = os.path.basename(os.readlink(driver_path))

        # Look up human-readable name
        gpu_name = lookup_gpu_name(vendor_id, device_id)

        return {
            "vendor_id": vendor_id,
            "device_id": device_id,
            "driver": driver_name,
            "name": gpu_name,
            "is_discrete": vendor_id.lower() in ["0x10de", "0x1002"],  # NVIDIA, AMD
            "is_integrated": vendor_id.lower() == "0x8086",  # Intel
        }
    except Exception:
        return None


def get_gpu_info():
    """Get GPU information, prioritizing discrete GPU over integrated"""
    try:
        drm_path = "/sys/class/drm"
        if not os.path.exists(drm_path):
            return "Not detected"

        discrete_gpu = None
        integrated_gpu = None

        # Scan all DRM cards
        for entry in os.listdir(drm_path):
            if entry.startswith("card") and "-" not in entry:  # Only card0, card1, etc.
                card_path = os.path.join(drm_path, entry)
                gpu_info = detect_gpu_from_card(card_path)

                if gpu_info and gpu_info["name"]:
                    if gpu_info["is_discrete"]:
                        discrete_gpu = gpu_info
                    elif gpu_info["is_integrated"]:
                        integrated_gpu = gpu_info

        # Prioritize discrete GPU
        gpu = discrete_gpu or integrated_gpu
        if gpu and gpu["name"]:
            # Extract only content inside brackets
            name = gpu["name"]
            bracket_match = re.search(r"\[([^\]]+)\]", name)
            if bracket_match:
                return bracket_match.group(1)
            return name
        else:
            return "Not detected"

    except Exception:
        return "Not detected"


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
                    pixel_size=250,
                ),
                SettingsGroup(
                    name="System Info",
                    rows=[
                        widgets.Grid(
                            column_num=2,
                            child=[
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>󰣇</span>  Operating System",
                                    use_markup=True,
                                    sublabel=fetch.os_name,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>󰌢</span>   Hostname",
                                    use_markup=True,
                                    sublabel=fetch.hostname,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>󰘦</span>   Ignis Version",
                                    use_markup=True,
                                    sublabel=__version__,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>󰍹</span>   Session type",
                                    use_markup=True,
                                    sublabel=fetch.session_type,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>   Wayland compositor",
                                    use_markup=True,
                                    sublabel=fetch.current_desktop,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>  Kernel",
                                    use_markup=True,
                                    sublabel=fetch.kernel,
                                ),
                            ],
                        ),
                    ],
                ),
                SettingsGroup(
                    name="Hardware Info",
                    rows=[
                        widgets.Grid(
                            column_num=2,
                            child=[
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>   CPU",
                                    use_markup=True,
                                    sublabel=fetch.cpu,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>󰢮</span>   GPU",
                                    use_markup=True,
                                    sublabel=get_gpu_info(),
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>   RAM",
                                    use_markup=True,
                                    sublabel=f"{fetch.mem_total / 1024 / 1024:.1f} GB",
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>🖴</span>  Root Partition",
                                    use_markup=True,
                                    sublabel=f"{partition_size:.1f} GB",
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'>󰤨</span>   Wifi Driver",
                                    use_markup=True,
                                    sublabel=get_wifi_driver_name(),
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>   Motherboard",
                                    use_markup=True,
                                    sublabel=fetch.board_vendor,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>   UEFI Version",
                                    use_markup=True,
                                    sublabel=fetch.board_name,
                                ),
                                SettingsRow(
                                    label="<span font='JetBrains Mono Nerd Font'></span>   Secure Boot",
                                    use_markup=True,
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
