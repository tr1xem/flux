import os
import sys

# Add current directory to Python path for local imports
sys.path.insert(0, os.path.dirname(__file__))

# IGNIS IMPORTS
from ignis import utils
from ignis.css_manager import CssInfoPath, CssManager
from ignis.icon_manager import IconManager

# CUSTOM WIDGETS
from modules.bar.bar import Bar
from modules.bar.widgets.player_expanded import ExpandedPlayerWindow
from modules.osd.osd import osd_window

# from modules.bar.widgets.player import
from modules.notification_popup.notification import NotificationPopup
from user_options import user_options

# Import volume OSD service to start monitoring
try:
    from services.volume_osd import volume_osd_service
except ImportError:
    pass  # Service not available

icon_manager = IconManager.get_default()

icon_manager.add_icons(os.path.join(utils.get_current_dir(), "assets", "icons"))
css_manager = CssManager.get_default()


# WallpaperService.get_default()
# options.wallpaper.set_wallpaper_path(
#     os.path.expanduser(
#         "~/Pictures/Wallpapers/stars-wallpaper-3840x2160-gradients-cosmic-art-27056.jpg"
#     )
# )
#
def format_scss_var(name: str, val: str) -> str:
    return f"${name}: {val};\n"


def patch_style_scss(path: str) -> str:
    with open(path) as file:
        contents = file.read()

    scss_colors = ""

    for key, value in user_options.material.colors.items():
        scss_colors += format_scss_var(key, value)

    string = (
        format_scss_var("darkmode", str(user_options.material.dark_mode).lower())
        + scss_colors
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
        priority="user",
    )
)
css_manager.widgets_style_priority = "user"  # pyright: ignore[reportAttributeAccessIssue]

ExpandedPlayerWindow()
Bar(0)
NotificationPopup(0)

# Initialize OSD window (imported from modules.osd.osd)
# Volume OSD service is automatically started via import
