from collections.abc import Iterable

from gi.repository import Gtk
from ignis.base_widget import BaseWidget


class Fixed(Gtk.Fixed, BaseWidget):
    """
    Bases: :class:`Gtk.Fixed`

    A fixed container widget that allows positioning child widgets at specific coordinates.
    Unlike other container widgets that use automatic layout, Fixed positions children
    manually using absolute coordinates.

    Args:
        child: An iterable of tuples containing (widget, (x, y)) pairs for positioned children.
        name: Optional name for the widget.
        size: Size specification for the container.
        **kwargs: Properties to set.

    .. code-block:: python

        Fixed(
            child=[
                (Label(label="Top Left"), (10, 10)),
                (Button(label="Center"), (100, 50)),
                (Icon(image="settings"), (200, 200))
            ],
            css_classes=["fixed-container"]
        )
    """
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
