import os

from ignis import utils, widgets
from ignis.options import options

from services.material import MaterialService
from user_options import user_options

from ..elements import FileRow, SettingsEntry, SettingsGroup, SettingsPage, SwitchRow

material = MaterialService.get_default()

# Color scheme options
COLOR_SCHEME_OPTIONS = [
    "Tonal Spot",
    "Expressive", 
    "Neutral",
    "Vibrant",
    "Fidelity",
    "Monochrome",
    "Content",
    "Rainbow",
    "Fruit Salad",
]

# Mapping from our color scheme names to matugen scheme types
MATUGEN_SCHEME_MAPPING = {
    "Tonal Spot": "scheme-tonal-spot",
    "Expressive": "scheme-expressive",
    "Neutral": "scheme-neutral",
    "Vibrant": "scheme-tonal-spot",  # Vibrant doesn't exist in matugen, use tonal-spot as fallback
    "Fidelity": "scheme-fidelity",
    "Monochrome": "scheme-monochrome", 
    "Content": "scheme-content",
    "Rainbow": "scheme-rainbow",
    "Fruit Salad": "scheme-fruit-salad",
}

def get_matugen_scheme_type(scheme_name: str) -> str:
    """Get the matugen scheme type for a given color scheme name"""
    return MATUGEN_SCHEME_MAPPING.get(scheme_name, "scheme-tonal-spot")

def get_scheme_index(scheme_name: str) -> int:
    """Get the index of a color scheme name in the options list"""
    try:
        return COLOR_SCHEME_OPTIONS.index(scheme_name)
    except ValueError:
        return 0  # Default to "Tonal Spot"

def on_scheme_selected(dropdown, selected_scheme: str) -> None:
    """Handle color scheme selection"""
    if selected_scheme in COLOR_SCHEME_OPTIONS:
        user_options.material.set_color_scheme(selected_scheme)
        # Also update matugen with the new scheme if we have a wallpaper
        if options.wallpaper.wallpaper_path:
            scheme_type = get_matugen_scheme_type(selected_scheme)
            utils.exec_sh(f"/usr/bin/matugen image -t {scheme_type} {options.wallpaper.wallpaper_path}")


class AppearanceEntry(SettingsEntry):
    def __init__(self):
        page = SettingsPage(
            name="Appearance",
            groups=[
                SettingsGroup(
                    name=None,
                    rows=[
                        widgets.ListBoxRow(
                            css_classes=["settings-wallpaper"],
                            child=widgets.Picture(
                                image=options.wallpaper.bind("wallpaper_path"),
                                width=1920 // 4,
                                height=1080 // 4,
                                halign="center",
                                style="border-radius: 1rem;",
                                content_fit="cover",
                            ),
                            selectable=False,
                            activatable=False,
                        ),
                        SwitchRow(
                            label="Dark mode",
                            active=user_options.material.bind("dark_mode"),
                            on_change=lambda x,
                            state: user_options.material.set_dark_mode(state),
                            style="margin-top: 1rem;",
                        ),
                        SwitchRow(
                            label="Blur effects",
                            active=user_options.material.bind("blur_enabled"),
                            on_change=lambda x,
                            state: user_options.material.set_blur_enabled(state),
                        ),
                        widgets.ListBoxRow(
                            css_classes=["settings-row"],
                            child=widgets.Box(
                                child=[
                                    widgets.Box(
                                        vertical=True,
                                        spacing=5,
                                        child=[
                                            widgets.Label(
                                                label="Color scheme",
                                                css_classes=["settings-row-label"],
                                                halign="start",
                                                vexpand=True,
                                                wrap=True,
                                                max_width_chars=25,
                                            ),
                                        ],
                                    ),
                                    widgets.DropDown(
                                        items=COLOR_SCHEME_OPTIONS,
                                        selected=user_options.material.color_scheme,
                                        on_selected=on_scheme_selected,
                                        halign="end",
                                        valign="center",
                                        hexpand=True,
                                    ),
                                ]
                            ),
                        ),
                        FileRow(
                            label="Wallpaper path",
                            button_label=os.path.basename(
                                options.wallpaper.wallpaper_path
                            )
                            if options.wallpaper.wallpaper_path
                            else None,
                            dialog=widgets.FileDialog(
                                on_file_set=lambda x, file: (
                                    material.generate_colors(file.get_path()),
                                    utils.exec_sh(
                                        f"/usr/bin/matugen image -t {get_matugen_scheme_type(user_options.material.color_scheme)} {file.get_path()}"
                                    ),
                                ),
                                initial_path=options.wallpaper.bind("wallpaper_path"),
                                filters=[
                                    widgets.FileFilter(
                                        mime_types=["image/jpeg", "image/png"],
                                        default=True,
                                        name="Images JPEG/PNG",
                                    )
                                ],
                            ),
                        ),
                    ],
                )
            ],
        )
        super().__init__(
            label="Appearance",
            icon="preferences-desktop-wallpaper-symbolic",
            page=page,
        )
