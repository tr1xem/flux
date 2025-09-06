from ignis import widgets
from modules.shared_widgets.corner import Corner


class CornerAll(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        corner_size = (30, 30)

        # Create corner widgets and set their size requests
        top_left_corner = Corner(
            orientation="top-left",
            css_classes=["corner-top"],
            halign="end",
            valign="start",
        )
        top_left_corner.set_size_request(corner_size[0], corner_size[1])

        top_right_corner = Corner(
            orientation="top-right",
            halign="end",
            valign="start",
            css_classes=["corner-top"],
        )
        top_right_corner.set_size_request(corner_size[0], corner_size[1])

        bottom_left_corner = Corner(
            orientation="bottom-left",
            css_classes=["corner"],
            halign="end",
            valign="end",
        )
        bottom_left_corner.set_size_request(corner_size[0], corner_size[1])

        bottom_right_corner = Corner(
            orientation="bottom-right",
            halign="end",
            valign="end",
            css_classes=["corner"],
        )
        bottom_right_corner.set_size_request(corner_size[0], corner_size[1])

        super().__init__(
            namespace=f"ignis_CORNER_{monitor_id}",
            exclusivity="exclusive",
            css_classes=["rec-unset"],
            anchor=["top", "right", "bottom", "left"],
            layer="bottom",
            child=widgets.CenterBox(
                vertical=True,
                start_widget=widgets.Box(
                    child=[
                        widgets.CenterBox(
                            vertical=False,
                            vexpand=True,
                            hexpand=True,
                            start_widget=widgets.Box(child=[top_left_corner]),
                            end_widget=widgets.Box(
                                child=[top_right_corner],
                            ),
                        ),
                    ]
                ),
                end_widget=widgets.Box(
                    child=[
                        widgets.CenterBox(
                            vertical=False,
                            vexpand=True,
                            hexpand=True,
                            start_widget=widgets.Box(child=[bottom_left_corner]),
                            end_widget=widgets.Box(
                                child=[bottom_right_corner],
                            ),
                        ),
                    ]
                ),
            ),
        )
