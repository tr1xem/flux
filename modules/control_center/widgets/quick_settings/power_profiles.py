from ignis import widgets
from ...qs_button import QSButton
from ...menu import Menu
from ignis.services.power_profiles import PowerProfilesService

power_profiles = PowerProfilesService.get_default()


class PowerProfileItem(widgets.Button):
    def __init__(self, profile: str):
        def get_profile_label(profile: str) -> str:
            profile_names = {
                "power-saver": "Power Saver",
                "balanced": "Balanced", 
                "performance": "Performance"
            }
            return profile_names.get(profile, profile.title())

        def get_profile_icon(profile: str) -> str:
            return f"power-profile-{profile}-symbolic"

        super().__init__(
            css_classes=["network-item", "unset"],
            on_click=lambda x: power_profiles.set_property("active_profile", profile),
            child=widgets.Box(
                child=[
                    widgets.Icon(
                        image=get_profile_icon(profile),
                    ),
                    widgets.Label(
                        label=get_profile_label(profile),
                        halign="start",
                    ),
                    widgets.Icon(
                        image="object-select-symbolic",
                        halign="end",
                        hexpand=True,
                        visible=power_profiles.bind(
                            "active_profile", 
                            transform=lambda active: active == profile
                        ),
                    ),
                ]
            ),
        )


class PowerProfilesMenu(Menu):
    def __init__(self):
        super().__init__(
            name="power_profiles",
            child=[
                widgets.Label(
                    label="Power Profile",
                    css_classes=["network-header-box"],
                    style="font-weight: bold; padding: 12px;",
                ),
                widgets.Box(
                    vertical=True,
                    child=[PowerProfileItem(profile) for profile in power_profiles.profiles],
                ),
            ],
        )


class PowerProfilesButton(QSButton):
    def __init__(self):
        menu = PowerProfilesMenu()

        def get_profile_label(profile: str) -> str:
            profile_names = {
                "power-saver": "Power Saver",
                "balanced": "Balanced", 
                "performance": "Performance"
            }
            return profile_names.get(profile, profile.title())

        def toggle_menu(x) -> None:
            menu.toggle()

        super().__init__(
            label=power_profiles.bind("active_profile", get_profile_label),
            icon_name=power_profiles.bind("icon_name"),
            on_activate=toggle_menu,
            on_deactivate=toggle_menu,
            active=power_profiles.bind("is_available"),
            menu=menu,
        )