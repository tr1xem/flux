from typing import Callable

from ignis import widgets
from ignis.gobject import Binding

from .row import SettingsRow


class SwitchRow(SettingsRow):
    def __init__(
        self,
        active: bool | Binding = False,
        on_change: Callable | None = None,
        **kwargs,
    ):
        self._switch = widgets.Switch(
            active=active,
            on_change=on_change,
            halign="end",
            valign="center",
            hexpand=True,
        )
        
        # Pass the additional widget as part of initialization
        super().__init__(additional_widgets=[self._switch], **kwargs)
        
        self.on_activate = lambda x: self._switch.emit(
            "activate"
        )  # if set "active" property animation will not work
