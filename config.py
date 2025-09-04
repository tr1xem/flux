import os

from ignis import utils, widgets
from ignis.css_manager import CssInfoPath, CssManager
from ignis.icon_manager import IconManager
from ignis.options import options
from ignis.services.wallpaper import WallpaperService

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
        os.path.curdir + "./assets/example_wallpapers/example-1.jpeg"
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

    print(string)
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


class CornerAll(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            namespace=f"ignis_CORNER_{monitor_id}",
            exclusivity="exclusive",
            css_classes=["rec-unset"],
            anchor=["top", "right", "bottom", "left"],
            layer="bottom",
            child=widgets.CenterBox(
                vertical=True,
                start_widget=widgets.Box(
                    child=[
                        widgets.CenterBox(
                            vertical=False,
                            vexpand=True,
                            hexpand=True,
                            start_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="top-left",
                                        size=corner_size,
                                        css_classes=["corner-top"],
                                        halign="end",
                                        valign="start",
                                    )
                                ]
                            ),
                            end_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="top-right",
                                        size=corner_size,
                                        halign="end",
                                        valign="start",
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
                            vexpand=True,
                            hexpand=True,
                            start_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="bottom-left",
                                        size=corner_size,
                                        css_classes=["corner"],
                                        halign="end",
                                        valign="end",
                                    )
                                ]
                            ),
                            end_widget=widgets.Box(
                                child=[
                                    Corner(
                                        orientation="bottom-right",
                                        size=corner_size,
                                        halign="end",
                                        valign="end",
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
for monitor in range(utils.get_n_monitors()):
    ExpandedPlayerWindow(monitor)

for monitor in range(utils.get_n_monitors()):
    ControlCenter(monitor)
for monitor in range(utils.get_n_monitors()):
    Bar(monitor)

for monitor in range(utils.get_n_monitors()):
    NotificationPopup(monitor)

for monitor in range(utils.get_n_monitors()):
    CornerAll(monitor)
for monitor in range(utils.get_n_monitors()):
    Osd(monitor)

Settings()
Powermenu()
