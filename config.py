# Standard library imports
import datetime
import os
import sys

# Third party imports

# Setup path for local imports
sys.path.insert(0, os.path.dirname(__file__))

# Ignis imports
from ignis import utils, widgets
from ignis.css_manager import CssInfoPath, CssManager
from ignis.icon_manager import IconManager
from ignis.options import options
from ignis.services.wallpaper import WallpaperService
from ignis.variable import Variable

# Local module imports
from modules import (
    Bar,
    ControlCenter,
    NotificationPopup,
    Osd,
    Powermenu,
    Settings,
)
from modules.bar.widgets.player_expanded import ExpandedPlayerWindow
from modules.shared_widgets import CornerAll
from modules.shared_widgets.fixed import Fixed
from services.wallpaper_processor import on_depth_wall_toggle, on_wallpaper_change
from user_options import user_options

icon_manager = IconManager.get_default()

icon_manager.add_icons(os.path.join(utils.get_current_dir(), "assets", "icons"))
css_manager = CssManager.get_default()


WallpaperService.get_default()
if options.wallpaper.wallpaper_path is None:
    options.wallpaper.set_wallpaper_path(
        os.path.curdir + "./assets/example_wallpapers/example-1.jpeg"
    )


options.wallpaper.connect_option("wallpaper_path", lambda: on_wallpaper_change())
user_options.wallpaper.connect_option(
    "depth_wall_enabled", lambda: on_depth_wall_toggle()
)


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


corner_size = (30, 30)


def setup_datetime_widget():
    simple_datetime = widgets.Label(css_classes=["movable-datetime"], use_markup=True)

    time_variable = Variable(
        value=utils.Poll(
            1000,
            lambda x: datetime.datetime.now().strftime("%I:%M"),
        ).bind("output")
    )

    simple_datetime.label = time_variable.bind("value")

    fix = Fixed(
        hexpand=True,
        vexpand=True,
        child=[
            (
                simple_datetime,
                (user_options.datetime.x_position, user_options.datetime.y_position),
            )
        ],
        css_classes=["fixed-label"],
    )

    datetime_window = widgets.Window(
        namespace="ignis_DATETIME",
        exclusivity="ignore",
        anchor=["top", "right", "bottom", "left"],
        css_classes=["rec-unset"],
        layer="bottom",
        child=fix,
    )

    def move():
        fix.move(
            simple_datetime,
            user_options.datetime.x_position,
            user_options.datetime.y_position,
        )

    def update_datetime_visibility():
        enabled = user_options.desktop_widgets.datetime_enabled
        datetime_window.set_visible(enabled)

    user_options.datetime.connect("changed", lambda *_: move())
    user_options.desktop_widgets.connect_option(
        "datetime_enabled", lambda: update_datetime_visibility()
    )

    # Set initial visibility
    update_datetime_visibility()

    return simple_datetime, fix


def setup_depth_wall():
    depth_picture = widgets.Picture(
        image=user_options.wallpaper.bind("depth_wall"),
        hexpand=True,
        vexpand=True,
        content_fit="cover",
        css_classes=["depth-wallpaper"],
    )

    depth_window = widgets.Window(
        namespace="ignis_fixed_d2",
        exclusivity="ignore",
        anchor=["top", "right", "bottom", "left"],
        css_classes=["rec-unset"],
        layer="bottom",
        child=depth_picture,
    )

    def update_depth_window_visibility():
        enabled = user_options.wallpaper.depth_wall_enabled
        path = user_options.wallpaper.depth_wall

        if enabled and path:
            depth_window.set_visible(True)
        else:
            depth_window.set_visible(False)

    user_options.wallpaper.connect_option(
        "depth_wall", lambda: update_depth_window_visibility()
    )
    user_options.wallpaper.connect_option(
        "depth_wall_enabled", lambda: update_depth_window_visibility()
    )

    update_depth_window_visibility()
    return depth_window


# Widget Setup
simple_datetime, fix = setup_datetime_widget()
depth_window = setup_depth_wall()

# Widget Initialization
for monitor in range(utils.get_n_monitors()):
    ExpandedPlayerWindow(monitor)
    ControlCenter(monitor)
    Bar(monitor)
    NotificationPopup(monitor)
    CornerAll(monitor)
    Osd(monitor)

Settings()
Powermenu()
