from user_options import user_options

from ..elements import SettingsEntry, SettingsGroup, SettingsPage, SwitchRow


class DesktopWidgetsEntry(SettingsEntry):
    def __init__(self):
        page = SettingsPage(
            name="Desktop Widgets",
            groups=[
                SettingsGroup(
                    name="Bottom Layer Widgets",
                    rows=[
                        SwitchRow(
                            label="DateTime Widget",
                            sublabel="Show movable datetime widget on desktop",
                            active=user_options.desktop_widgets.bind("datetime_enabled"),
                            on_change=(
                                lambda x, state: user_options.desktop_widgets.set_datetime_enabled(state)
                            ),
                        ),
                    ],
                ),
            ],
        )
        super().__init__(
            label="Desktop Widgets",
            icon="preferences-desktop-wallpaper-symbolic",
            page=page,
        )