# Standard library imports
import os
import sys

# Third party imports

# Setup path for local imports
sys.path.insert(0, os.path.dirname(__file__))

# Ignis imports
from ignis import utils
from ignis.css_manager import CssInfoPath, CssManager
from ignis.icon_manager import IconManager
from ignis.options import options
from ignis.services.wallpaper import WallpaperService

# Local module imports
from modules import (
    Bar,
    ControlCenter,
    NotificationPopup,
    Osd,
    Powermenu,
    Settings,
    TimeWidget,
    DateWidget,
    Depth,
    CornerAll,
)
from modules.bar.widgets.player_expanded import ExpandedPlayerWindow
from services.wallpaper_processor import on_depth_wall_toggle, on_wallpaper_change
from user_options import user_options

icon_manager = IconManager.get_default()

icon_manager.add_icons(os.path.join(utils.get_current_dir(), "assets", "icons"))
css_manager = CssManager.get_default()


WallpaperService.get_default()
if options.wallpaper.wallpaper_path is None or not os.path.exists(
    options.wallpaper.wallpaper_path
):
    options.wallpaper.set_wallpaper_path(
        os.path.curdir + "./assets/example_wallpapers/example-1.jpeg"
    )


options.wallpaper.connect_option("wallpaper_path", lambda: on_wallpaper_change())
# Connect to rembg options
if hasattr(user_options, "rembg"):
    user_options.rembg.connect_option("enabled", lambda: on_depth_wall_toggle())


def format_scss_var(name: str, val: str) -> str:
    return f"${name}: {val};\n"


def patch_style_scss(path: str) -> str:
    with open(path) as file:
        contents = file.read()

    scss_colors = ""

    for key, value in user_options.material.colors.items():
        scss_colors += format_scss_var(key, value)

    # Add opacity variables based on blur setting
    blur_enabled = getattr(user_options.material, "blur_enabled", True)
    if blur_enabled:
        opacity_high = "0.7"
        opacity_medium = "0.5"
        opacity_low = "0.3"
    else:
        opacity_high = "1"
        opacity_medium = "1"
        opacity_low = "1"

    opacity_vars = (
        format_scss_var("opacity-high", opacity_high)
        + format_scss_var("opacity-medium", opacity_medium)
        + format_scss_var("opacity-low", opacity_low)
    )

    string = (
        format_scss_var("darkmode", str(user_options.material.dark_mode).lower())
        + scss_colors
        + opacity_vars
        + contents
    )
    return utils.sass_compile(
        string=string, extra_args=["--load-path", utils.get_current_dir()]
    )


css_manager.apply_css(
    CssInfoPath(
        name="main",
        compiler_function=patch_style_scss,
        path=os.path.join(utils.get_current_dir(), "main.scss"),
        # priority="user",
    )
)


# # Widget Initialization
# Single instance widgets (created only once on monitor 0)
TimeWidget(0)  # Calendar popup - single instance
ExpandedPlayerWindow(0)  # Media player popup - single instance

# Per-monitor widgets
for monitor in range(utils.get_n_monitors()):
    DateWidget(monitor)
    Depth(monitor)
    ControlCenter(monitor)
    Bar(monitor)
    NotificationPopup(monitor)
    CornerAll(monitor)
    Osd(monitor)

Settings()
Powermenu()
