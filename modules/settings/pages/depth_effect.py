from user_options import user_options

from ..elements import DropdownRow, SettingsEntry, SettingsGroup, SettingsPage, SpinRow, SwitchRow


class DepthEffectEntry(SettingsEntry):
    def __init__(self):
        page = SettingsPage(
            name="Depth Effect",
            groups=[
                SettingsGroup(
                    name="Background Removal Settings",
                    rows=[
                        SwitchRow(
                            label="Enable depth wallpaper",
                            active=user_options.rembg.bind("enabled"),
                            on_change=lambda x, state: user_options.rembg.set_enabled(state),
                        ),
                        DropdownRow(
                            label="AI Model",
                            sublabel="u2net is faster, isnet-general-use is more accurate",
                            items=["u2net", "isnet-general-use"],
                            selected=user_options.rembg.bind("model", transform=lambda model: ["u2net", "isnet-general-use"].index(model) if model in ["u2net", "isnet-general-use"] else 0),
                            on_selected=lambda dropdown: user_options.rembg.set_model(dropdown.selected),
                        ),
                        SwitchRow(
                            label="Alpha matting",
                            sublabel="Better edge detail but slower processing",
                            active=user_options.rembg.bind("alpha_matting"),
                            on_change=lambda x, state: user_options.rembg.set_alpha_matting(state),
                        ),
                    ],
                ),
                SettingsGroup(
                    name="Alpha Matting Settings",
                    rows=[
                        SpinRow(
                            label="Foreground threshold",
                            sublabel="Higher values = more aggressive foreground detection",
                            value=user_options.rembg.bind("foreground_threshold"),
                            on_change=lambda x, value: user_options.rembg.set_foreground_threshold(value),
                            min=0,
                            max=255,
                            step=1,
                        ),
                        SpinRow(
                            label="Background threshold",
                            sublabel="Lower values = more aggressive background removal", 
                            value=user_options.rembg.bind("background_threshold"),
                            on_change=lambda x, value: user_options.rembg.set_background_threshold(value),
                            min=0,
                            max=255,
                            step=1,
                        ),
                        SpinRow(
                            label="Erode size",
                            sublabel="Edge smoothing amount",
                            value=user_options.rembg.bind("erode_size"),
                            on_change=lambda x, value: user_options.rembg.set_erode_size(value),
                            min=0,
                            max=50,
                            step=1,
                        ),
                    ],
                ),
            ],
        )
        super().__init__(
            label="Depth Effect",
            icon="applications-graphics-symbolic",
            page=page,
        )