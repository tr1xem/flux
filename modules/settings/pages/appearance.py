import asyncio
import os
import sys
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "services"))
from ignis import utils, widgets
from ignis.css_manager import CssManager
from ignis.options import options
from PIL import Image

from services.material import MaterialService
from user_options import user_options

from services import image_processor
from ..elements import FileRow, SettingsEntry, SettingsGroup, SettingsPage, SwitchRow

material = MaterialService.get_default()
css_manager = CssManager.get_default()
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


downscale_img: str = ""


def downscale_image_to_preview_size(
    image_path: str, target_width: int = 480, target_height: int = 270
) -> str:
    """
    Downscale an image to match the appearance preview dimensions.
    Default dimensions are 1920//4 x 1080//4 (480x270) to match the wallpaper preview.
    Returns the path to the downscaled image, or the original path if scaling fails.
    """
    return image_processor.scale_for_preview(image_path, target_width, target_height)

    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size

            original_aspect = original_width / original_height
            target_aspect = target_width / target_height

            if original_aspect > target_aspect:
                new_height = target_height
                new_width = int(target_height * original_aspect)
            else:
                new_width = target_width
                new_height = int(target_width / original_aspect)

            if new_width < original_width or new_height < original_height:
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(temp_fd)
                resized.save(temp_path, "PNG", optimize=True)

                downscale_img = temp_path
                return temp_path
            else:
                downscale_img = image_path
                return image_path

    except Exception:
        return image_path


_color_scheme_buttons = []


def create_color_scheme_dropdown() -> widgets.DropDown:
    """Create color scheme dropdown"""
    current_scheme = user_options.material.color_scheme
    selected_index = get_scheme_index(current_scheme)

    dropdown = widgets.DropDown(
        items=COLOR_SCHEME_OPTIONS,
        css_classes=["settings-color-scheme"],
        selected=COLOR_SCHEME_OPTIONS[selected_index],
    )

    def on_dropdown_changed(*args):
        selected_scheme = dropdown.selected
        user_options.material.set_color_scheme(selected_scheme)

    dropdown.connect("notify::selected", on_dropdown_changed)

    return dropdown


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
                                image=options.wallpaper.bind(
                                    "wallpaper_path",
                                    transform=lambda path: downscale_image_to_preview_size(
                                        path
                                    )
                                    if path
                                    else None,
                                ),
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
                                    create_color_scheme_dropdown(),
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
                        SwitchRow(
                            label="Depth wallpaper",
                            active=user_options.wallpaper.bind("depth_wall_enabled"),
                            on_change=lambda x,
                            state: user_options.wallpaper.set_depth_wall_enabled(state),
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
                                    options.wallpaper.set_wallpaper_path(
                                        file.get_path()
                                    ),
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
