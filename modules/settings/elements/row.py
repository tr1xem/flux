from ignis import widgets


class SettingsRow(widgets.ListBoxRow):
    def __init__(
        self,
        label: str | None = None,
        sublabel: str | None = None,
        **kwargs,
    ):
        super().__init__(
            css_classes=["settings-row"],
            child=widgets.Box(
                child=[
                    widgets.Box(
                        vertical=True,
                        spacing=5,
                        child=[
                            widgets.Label(
                                label=label,
                                css_classes=["settings-row-label"],
                                halign="start",
                                vexpand=True,
                                wrap=True,
                                max_width_chars=25,
                                visible=True if label else False,
                            ),
                            widgets.Label(
                                label=sublabel,
                                css_classes=["settings-row-sublabel"],
                                halign="start",
                                vexpand=True,
                                wrap=True,
                                max_width_chars=35,
                                visible=True if sublabel else False,
                            ),
                        ],
                    )
                ]
            ),
            **kwargs,
        )
