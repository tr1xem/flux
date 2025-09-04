from ignis import widgets


class SettingsRow(widgets.Box):
    def __init__(
        self,
        label: str | None = None,
        sublabel: str | None = None,
        use_markup: bool = False,
        style: str | None = None,
        additional_widgets: list | None = None,
        **kwargs,
    ):
        self._label_box = widgets.Box(
            vertical=True,
            spacing=5,
            child=[
                widgets.Label(
                    label=label,
                    css_classes=["settings-row-label"],
                    halign="start",
                    use_markup=use_markup,
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
                    use_markup=use_markup,
                    wrap=True,
                    max_width_chars=35,
                    visible=True if sublabel else False,
                ),
            ],
        )
        
        children = [self._label_box]
        if additional_widgets:
            children.extend(additional_widgets)
        
        init_kwargs = {
            "css_classes": ["settings-row"],
            "child": children,
            **kwargs,
        }
        if style is not None:
            init_kwargs["style"] = style
        
        super().__init__(**init_kwargs)
