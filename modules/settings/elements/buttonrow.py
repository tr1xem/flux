from ignis import widgets
from .row import SettingsRow


class ButtonRow(SettingsRow):
    def __init__(
        self,
        label: str | None = None,
        sublabel: str | None = None,
        button_label: str = "Button",
        on_click=None,
        **kwargs,
    ):
        # Create button with proper alignment container
        button_container = widgets.Box(
            halign="end",
            hexpand=True,
            child=[
                widgets.Button(
                    label=button_label,
                    on_click=on_click if on_click else lambda *_: None,
                    css_classes=["settings-button"],
                )
            ]
        )
        
        super().__init__(
            label=label,
            sublabel=sublabel,
            additional_widgets=[button_container],
            **kwargs,
        )