from ignis import widgets
from .corner import Corner


class CornerAll(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        corner_size = (30, 30)
        
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
                            start_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="top-left",
                                        size=corner_size,
                                        css_classes=["corner-top"],
                                        halign="end",
                                        valign="start",
                                    )
                                ]
                            ),
                            end_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="top-right",
                                        size=corner_size,
                                        halign="end",
                                        valign="start",
                                        css_classes=["corner-top"],
                                    ),
                                ],
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
                            start_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="bottom-left",
                                        size=corner_size,
                                        css_classes=["corner"],
                                        halign="end",
                                        valign="end",
                                    )
                                ]
                            ),
                            end_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="bottom-right",
                                        size=corner_size,
                                        halign="end",
                                        valign="end",
                                        css_classes=["corner"],
                                    ),
                                ],
                            ),
                        ),
                    ]
                ),
            ),
        )