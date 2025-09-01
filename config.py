import os

# IGNIS IMPORTS
from ignis import utils
from ignis.css_manager import CssInfoPath, CssManager
from ignis.icon_manager import IconManager

# CUSTOM WIDGETS
from modules.bar.bar import Bar
from modules.notification_popup.notification import NotificationPopup

icon_manager = IconManager.get_default()

icon_manager.add_icons(os.path.join(utils.get_current_dir(), "assets", "icons"))
css_manager = CssManager.get_default()

css_manager.apply_css(
    CssInfoPath(
        name="main",
        compiler_function=lambda path: utils.sass_compile(path=path),
        path=os.path.join(utils.get_current_dir(), "main.scss"),
        priority="user",
    )
)
css_manager.widgets_style_priority = "user"  # pyright: ignore[reportAttributeAccessIssue]

# WallpaperService.get_default()
# options.wallpaper.set_wallpaper_path(
#     os.path.expanduser(
#         "~/Pictures/Wallpapers/stars-wallpaper-3840x2160-gradients-cosmic-art-27056.jpg"
#     )
# )
#

Bar(0)
NotificationPopup(0)
