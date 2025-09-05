from user_options import user_options

from ..elements import SettingsEntry, SettingsGroup, SettingsPage, SpinRow


class DraggablesEntry(SettingsEntry):
    def __init__(self):
        page = SettingsPage(
            name="DateTime Position",
            groups=[
                SettingsGroup(
                    name="Position Controls",
                    rows=[
                        SpinRow(
                            label="DateTime X Position",
                            sublabel="Horizontal position of the datetime widget (0-1820)",
                            value=user_options.datetime.bind("x_position"),
                            min=0,
                            max=1820,
                            step=5,
                            on_change=(
                                lambda x, value: user_options.datetime.set_x_position(
                                    int(value)
                                )
                            ),
                        ),
                        SpinRow(
                            label="DateTime Y Position",
                            sublabel="Vertical position of the datetime widget (0-980)",
                            value=user_options.datetime.bind("y_position"),
                            min=0,
                            max=980,
                            step=5,
                            on_change=(
                                lambda x, value: user_options.datetime.set_y_position(
                                    int(value)
                                )
                            ),
                        ),
                    ],
                ),
            ],
        )
        super().__init__(
            label="DateTime Position",
            icon="preferences-system-time-symbolic",
            page=page,
        )

