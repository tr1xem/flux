import asyncio
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


# Global registry to track all color scheme buttons
_color_scheme_buttons = []


class ColorSchemeButton(widgets.Button):
    def __init__(self, scheme_name: str):
        self.scheme_name = scheme_name
        self._active = False

        super().__init__(
            child=widgets.Label(
                label=scheme_name,
                css_classes=["color-scheme-button-label"],
            ),
            on_click=self._on_click,
            css_classes=["color-scheme-button"],
            hexpand=True,
        )

        # Add to global registry
        _color_scheme_buttons.append(self)

        # Set initial active state
        self._update_active_state()

        # Bind to user_options to update active state
        user_options.material.bind("color_scheme", self._update_active_state)

    def _on_click(self, *args) -> None:
        """Handle button click"""
        print(f"Button clicked: {self.scheme_name}")
        user_options.material.set_color_scheme(self.scheme_name)
        print(f"Set color scheme to: {self.scheme_name}")

        # Manually update all buttons since binding might not trigger immediately
        for button in _color_scheme_buttons:
            button._update_active_state()

        # Also update matugen with the new scheme if we have a wallpaper
        if options.wallpaper.wallpaper_path:
            scheme_type = get_matugen_scheme_type(self.scheme_name)
            asyncio.create_task(
                utils.exec_sh_async(
                    f"/usr/bin/matugen image -t {scheme_type} {options.wallpaper.wallpaper_path}"
                )
            )

    def _update_active_state(self, *args) -> None:
        """Update active state based on current color scheme"""
        current_scheme = user_options.material.color_scheme
        is_active = current_scheme == self.scheme_name

        print(
            f"Button {self.scheme_name}: current={current_scheme}, is_active={is_active}, was_active={self._active}"
        )

        if is_active != self._active:
            self._active = is_active
            if is_active:
                print(f"Adding active class to {self.scheme_name}")
                self.add_css_class("active")
            else:
                print(f"Removing active class from {self.scheme_name}")
                self.remove_css_class("active")


def create_color_scheme_buttons() -> widgets.Box:
    """Create horizontal layout of color scheme buttons"""
    # Clear previous button registry
    _color_scheme_buttons.clear()

    main_box = widgets.Box(vertical=True, spacing=8)

    # Create buttons in rows of 3
    buttons_per_row = 3
    for i in range(0, len(COLOR_SCHEME_OPTIONS), buttons_per_row):
        row = widgets.Box(homogeneous=True, spacing=8)

        for j in range(buttons_per_row):
            if i + j < len(COLOR_SCHEME_OPTIONS):
                button = ColorSchemeButton(COLOR_SCHEME_OPTIONS[i + j])
                row.append(button)

        main_box.append(row)

    return main_box


def on_scheme_selected(scheme_name: str) -> None:
    """Handle color scheme selection from menu"""
    user_options.material.set_color_scheme(scheme_name)
    # Also update matugen with the new scheme if we have a wallpaper
    if options.wallpaper.wallpaper_path:
        scheme_type = get_matugen_scheme_type(scheme_name)
        asyncio.create_task(
            utils.exec_sh_async(
                f"/usr/bin/matugen image -t {scheme_type} {options.wallpaper.wallpaper_path}"
            )
        )


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
                        widgets.ListBoxRow(
                            css_classes=["settings-row"],
                            child=widgets.Box(
                                vertical=True,
                                spacing=10,
                                child=[
                                    widgets.Label(
                                        label="Color scheme",
                                        css_classes=["settings-row-label"],
                                        halign="start",
                                        wrap=True,
                                        max_width_chars=25,
                                    ),
                                    create_color_scheme_buttons(),
                                ],
                            ),
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
                                    asyncio.create_task(
                                        utils.exec_sh_async(
                                            f"/usr/bin/matugen image -t {get_matugen_scheme_type(user_options.material.color_scheme)} {file.get_path()}"
                                        )
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
