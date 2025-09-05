from collections.abc import Iterable

from gi.repository import Gtk
from ignis.base_widget import BaseWidget


class Fixed(Gtk.Fixed, BaseWidget):
    __gtype_name__ = "IgnisFixed"
    __gproperties__ = {**BaseWidget.gproperties}

    def __init__(
        self,
        child: Iterable[tuple[Gtk.Widget, tuple[int, int]]] | None = None,
        name: str | None = None,
        size: Iterable[int] | int | None = None,
        **kwargs,
    ):
        Gtk.Fixed.__init__(self)  # type: ignore
        BaseWidget.__init__(
            self,
            **kwargs,
        )

        for widget in child or ():
            self.put(widget[0], *widget[1])
