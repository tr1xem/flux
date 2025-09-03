# import datetime
import os

# IGNIS IMPORTS
from ignis import utils, widgets
from ignis.css_manager import CssInfoPath, CssManager
from ignis.icon_manager import IconManager
from ignis.options import options
from ignis.services.wallpaper import WallpaperService

# from ignis.variable import Variable
# CUSTOM WIDGETS
# from modules.bar.widgets.player import
from modules import (
    Bar,
    ControlCenter,
    Corner,
    NotificationPopup,
    Osd,
    Powermenu,
    Settings,
)
from modules.bar.widgets.player_expanded import ExpandedPlayerWindow
from user_options import user_options

icon_manager = IconManager.get_default()

icon_manager.add_icons(os.path.join(utils.get_current_dir(), "assets", "icons"))
css_manager = CssManager.get_default()


WallpaperService.get_default()
if options.wallpaper.wallpaper_path is None:
    options.wallpaper.set_wallpaper_path(
        os.path.expanduser("~/Pictures/Wallpapers/astronaut-jellyfish-gruvbox.png")
    )


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
        # priority="user",
    )
)
# css_manager.widgets_style_priority = "user"  # pyright: ignore[reportAttributeAccessIssue]

ExpandedPlayerWindow()
ControlCenter()
Bar(0)
NotificationPopup(0)

corner_size = (30, 30)
window = widgets.Window(
    namespace="corner",
    exclusivity="exclusive",
    anchor=["top", "right", "bottom", "left"],
    layer="bottom",
    child=widgets.CenterBox(
        vertical=True,
        start_widget=widgets.Box(
            child=[
                widgets.CenterBox(
                    vertical=False,
                    vexpand=True,  # Expand vertically
                    hexpand=True,  # Expand horizontally
                    start_widget=widgets.Box(
                        child=[
                            Corner(
                                orientation="top-left",  # Shape points to top-right
                                size=corner_size,
                                css_classes=["corner-top"],
                                halign="end",  # Widget aligns to right
                                valign="start",  # Widget aligns to top
                            )
                        ]
                    ),
                    end_widget=widgets.Box(
                        child=[
                            Corner(
                                orientation="top-right",  # Shape points to top-right
                                size=corner_size,
                                halign="end",  # Widget aligns to right
                                valign="start",  # Widget aligns to top
                                css_classes=["corner-top"],
                            ),
                        ],
                    ),
                ),
            ]
        ),
        end_widget=widgets.Box(
            child=[
                widgets.CenterBox(
                    vertical=False,
                    vexpand=True,  # Expand vertically
                    hexpand=True,  # Expand horizontally
                    start_widget=widgets.Box(
                        child=[
                            Corner(
                                orientation="bottom-left",  # Shape points to top-right
                                size=corner_size,
                                css_classes=["corner"],
                                halign="end",  # Widget aligns to right
                                valign="end",  # Widget aligns to top
                            )
                        ]
                    ),
                    end_widget=widgets.Box(
                        child=[
                            Corner(
                                orientation="bottom-right",  # Shape points to top-right
                                size=corner_size,
                                halign="end",  # Widget aligns to right
                                valign="end",  # Widget aligns to top
                                css_classes=["corner"],
                            ),
                        ],
                    ),
                ),
            ]
        ),
    ),
)

# TODO: Implement a better way to do depth wallpapers

# pic = widgets.Picture(image="./removed-background.png", css_classes=["imag"])
# current_time = Variable(
#     value=utils.Poll(
#         1000,
#         lambda x: datetime.datetime.now().strftime("%I:%M"),
#     ).bind("output")
# )
#
# time = widgets.Label(
#     label=current_time.bind("value"),
#     css_classes=["d"],
#     halign="center",
# )
# widgets.Window(
#     namespace="ignis_m",
#     exclusivity="ignore",
#     anchor=["top", "right", "bottom", "left"],
#     layer="bottom",
#     child=widgets.Box(hexpand=True, halign="center", child=[time]),
# )
# widgets.Window(
#     namespace="ignis_ma",
#     exclusivity="ignore",
#     anchor=["top", "right", "bottom", "left"],
#     layer="bottom",
#     child=widgets.Box(hexpand=True, child=[pic]),
# )
Osd()
Settings()
Powermenu()
