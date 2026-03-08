from ignis import widgets
from ignis.base_widget import BaseWidget

from .row import SettingsRow


class SettingsGroup(widgets.Box):
    def __init__(
        self, name: str | None, rows: list[SettingsRow | BaseWidget] = [], **kwargs
    ):
        super().__init__(
            vertical=True,
            spacing=10,
            css_classes=["settings-group"],
            child=[
                widgets.Label(
                    label=name,
                    css_classes=["settings-group-name"],
                    halign="start",
                    visible=True if name else False,
                ),
                widgets.Box(
                    css_classes=["settings-group-rows"],
                    spacing=3,
                    vertical=True,
                    child=[*rows],
                ),
            ],
            **kwargs,
        )
