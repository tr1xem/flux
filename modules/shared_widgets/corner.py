from enum import Enum
from typing import Literal

import cairo
from gi.repository import Gtk
from ignis.base_widget import BaseWidget
from ignis.gobject import IgnisProperty


class CornerOrientation(Enum):
    """Enumeration for corner orientations."""

    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4


class Corner(Gtk.DrawingArea, BaseWidget):
    """
    Bases: :class:`Gtk.DrawingArea`

    A corner widget that renders rounded corners for use in bars and panels.

    Args:
        orientation: The corner orientation, either as a string or CornerOrientation enum.
        size: Tuple of (width, height) for the corner size.
        **kwargs: Properties to set.

    .. code-block:: python

        Corner(
            orientation="top-left",
            size=(20, 20),
            class_name="corner-widget"
        )
    """

    __gtype_name__ = "IgnisCorner"
    __gproperties__ = {**BaseWidget.gproperties}

    @staticmethod
    def render_shape(
        cr: cairo.Context,
        width: float,
        height: float,
        orientation: CornerOrientation = CornerOrientation.TOP_LEFT,
    ) -> None:
        """
        Render the corner shape to the given Cairo context.

        Args:
            cr: The Cairo context to draw on.
            width: Width of the drawing area.
            height: Height of the drawing area.
            orientation: The corner orientation to render.
        """
        cr.save()
        match orientation:
            case CornerOrientation.TOP_LEFT:
                cr.move_to(0, height)
                cr.line_to(0, 0)
                cr.line_to(width, 0)
                cr.curve_to(0, 0, 0, height, 0, height)
            case CornerOrientation.TOP_RIGHT:
                cr.move_to(width, height)
                cr.line_to(width, 0)
                cr.line_to(0, 0)
                cr.curve_to(width, 0, width, height, width, height)
            case CornerOrientation.BOTTOM_LEFT:
                cr.move_to(0, 0)
                cr.line_to(0, height)
                cr.line_to(width, height)
                cr.curve_to(0, height, 0, 0, 0, 0)
            case CornerOrientation.BOTTOM_RIGHT:
                cr.move_to(width, 0)
                cr.line_to(width, height)
                cr.line_to(0, height)
                cr.curve_to(width, height, width, 0, width, 0)
        cr.close_path()
        cr.restore()

    def __init__(
        self,
        orientation: Literal["top-left", "top-right", "bottom-left", "bottom-right"]
        | CornerOrientation = CornerOrientation.TOP_RIGHT,
        size: tuple[int, int] = (50, 50),
        **kwargs,
    ):
        Gtk.DrawingArea.__init__(self)
        self._orientation = self._get_enum_member(CornerOrientation, orientation)

        BaseWidget.__init__(self, **kwargs)

        self.set_size_request(size[0], size[1])
        self.set_draw_func(self._on_draw)

    def _get_enum_member(self, enum_class, value):
        """
        Convert string values to enum members.

        Args:
            enum_class: The enum class to convert to.
            value: The value to convert, either a string or enum member.

        Returns:
            The corresponding enum member.

        Raises:
            ValueError: If the string value doesn't match any enum member.
            TypeError: If the value is neither string nor enum member.
        """
        if isinstance(value, enum_class):
            return value

        if isinstance(value, str):
            enum_name = value.upper().replace("-", "_")
            try:
                return enum_class[enum_name]
            except KeyError:
                valid_values = [e.name.lower().replace("_", "-") for e in enum_class]
                raise ValueError(
                    f"Invalid value '{value}'. Expected one of: {valid_values}"
                )

        raise TypeError(
            f"Expected string or {enum_class.__name__}, got {type(value).__name__}"
        )

    @IgnisProperty
    def orientation(self) -> CornerOrientation:
        """The corner orientation."""
        return self._orientation

    @orientation.setter
    def orientation(
        self,
        value: Literal["top-left", "top-right", "bottom-left", "bottom-right"]
        | CornerOrientation,
    ) -> None:
        self._orientation = self._get_enum_member(CornerOrientation, value)
        self.queue_draw()

    def _on_draw(
        self,
        drawing_area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
        user_data=None,
    ) -> None:
        """
        Handle the draw event for the corner widget.

        Args:
            drawing_area: The drawing area widget.
            cr: The Cairo context.
            width: Width of the drawing area.
            height: Height of the drawing area.
            user_data: Additional user data (unused).
        """
        color = self.get_color()

        cr.save()

        self.render_shape(cr, width, height, self._orientation)
        cr.clip()

        if color:
            cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
        cr.paint()

        cr.restore()
