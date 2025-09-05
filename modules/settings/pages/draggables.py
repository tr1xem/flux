import random
from user_options import user_options

from ..elements import SettingsEntry, SettingsGroup, SettingsPage, SpinRow, ButtonRow


class DraggablesEntry(SettingsEntry):
    def __init__(self):
        def randomize_time_position(*_):
            # Generate random positions within screen bounds (with some margin)
            random_x = random.randint(50, 1750)  # Leave margin from edges
            random_y = random.randint(50, 900)  # Leave margin from edges
            user_options.time.set_x_position(random_x)
            user_options.time.set_y_position(random_y)

        def randomize_date_position(*_):
            # Generate random positions within screen bounds (with some margin)
            random_x = random.randint(50, 1750)  # Leave margin from edges
            random_y = random.randint(50, 900)  # Leave margin from edges
            user_options.date.set_x_position(random_x)
            user_options.date.set_y_position(random_y)

        page = SettingsPage(
            name="Widget Positions",
            groups=[
                SettingsGroup(
                    name="Time Widget Position",
                    rows=[
                        SpinRow(
                            label="Time X Position",
                            sublabel="Horizontal position of the time widget (0-1820)",
                            value=user_options.time.bind("x_position"),
                            min=0,
                            max=1820,
                            step=5,
                            on_change=(
                                lambda x, value: user_options.time.set_x_position(
                                    int(value)
                                )
                            ),
                        ),
                        SpinRow(
                            label="Time Y Position",
                            sublabel="Vertical position of the time widget (0-980)",
                            value=user_options.time.bind("y_position"),
                            min=0,
                            max=980,
                            step=5,
                            on_change=(
                                lambda x, value: user_options.time.set_y_position(
                                    int(value)
                                )
                            ),
                        ),
                        ButtonRow(
                            label="Random Position",
                            sublabel="Set time widget to a random position on screen",
                            button_label="Randomize",
                            on_click=randomize_time_position,
                        ),
                    ],
                ),
                SettingsGroup(
                    name="Date Widget Position",
                    rows=[
                        SpinRow(
                            label="Date X Position",
                            sublabel="Horizontal position of the date widget (0-1820)",
                            value=user_options.date.bind("x_position"),
                            min=0,
                            max=1820,
                            step=5,
                            on_change=(
                                lambda x, value: user_options.date.set_x_position(
                                    int(value)
                                )
                            ),
                        ),
                        SpinRow(
                            label="Date Y Position",
                            sublabel="Vertical position of the date widget (0-980)",
                            value=user_options.date.bind("y_position"),
                            min=0,
                            max=980,
                            step=5,
                            on_change=(
                                lambda x, value: user_options.date.set_y_position(
                                    int(value)
                                )
                            ),
                        ),
                        ButtonRow(
                            label="Random Position",
                            sublabel="Set date widget to a random position on screen",
                            button_label="Randomize",
                            on_click=randomize_date_position,
                        ),
                    ],
                ),
            ],
        )
        super().__init__(
            label="Widget Positions",
            icon="preferences-system-time-symbolic",
            page=page,
        )
