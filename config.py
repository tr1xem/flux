import os

# IGNIS IMPORTS
from ignis import utils
from ignis.css_manager import CssInfoPath, CssManager
from ignis.options import options
from ignis.services.wallpaper import WallpaperService

# CUSTOM MODULES
from modules.bar.bar import Bar

css_manager = CssManager.get_default()

css_manager.apply_css(
    CssInfoPath(
        name="main",
        compiler_function=lambda path: utils.sass_compile(path=path),
        path=os.path.join(utils.get_current_dir(), "main.scss"),
    )
)

WallpaperService.get_default()
options.wallpaper.set_wallpaper_path(
    os.path.expanduser(
        "~/Pictures/Wallpapers/stars-wallpaper-3840x2160-gradients-cosmic-art-27056.jpg"
    )
)


Bar(0)
