from typing import Callable

from ignis import widgets
from ignis.gobject import Binding

from .row import SettingsRow


class DropdownRow(SettingsRow):
    def __init__(
        self,
        items: list[str],
        selected: int | Binding = 0,
        on_selected: Callable | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        
        self._dropdown = widgets.DropDown(
            items=items,
            selected=selected,
            on_selected=on_selected,
            halign="end",
            valign="center",
            hexpand=True,
        )
        
        self.child.append(self._dropdown)