import os

from ignis import CACHE_DIR, DATA_DIR  # type: ignore
from ignis.options_manager import OptionsGroup, OptionsManager, TrackedList

USER_OPTIONS_FILE = f"{DATA_DIR}/user_options.json"
OLD_USER_OPTIONS_FILE = f"{CACHE_DIR}/user_options.json"


SCREENSHOT_APPS = [
    "grimblast",
    "gnome-screenshot",
    "hyprshot",
    "Flameshot",
    "flameshot",
    "wf-recorder",
]


# FIXME: remove someday
def _migrate_old_options_file() -> None:
    with open(OLD_USER_OPTIONS_FILE) as f:
        data = f.read()

    with open(USER_OPTIONS_FILE, "w") as f:
        f.write(data)


class UserOptions(OptionsManager):
    def __init__(self):
        if not os.path.exists(USER_OPTIONS_FILE) and os.path.exists(
            OLD_USER_OPTIONS_FILE
        ):
            _migrate_old_options_file()

        try:
            super().__init__(file=USER_OPTIONS_FILE)
        except FileNotFoundError:
            pass

    class User(OptionsGroup):
        avatar: str = f"/var/lib/AccountsService/icons/{os.getenv('USER')}"

    class Settings(OptionsGroup):
        last_page: int = 0

    class Material(OptionsGroup):
        dark_mode: bool = True
        blur_enabled: bool = True
        color_scheme: str = "Tonal Spot"
        colors: dict[str, str] = {}

    class Time(OptionsGroup):
        x_position: int = 400
        y_position: int = 90
        color: str = "#FFFFFF"
        use_custom_color: bool = False
        font_size: int = 24

    class Date(OptionsGroup):
        x_position: int = 400
        y_position: int = 140
        color: str = "#FFFFFF"
        use_custom_color: bool = False
        font_size: int = 18

    class DesktopWidgets(OptionsGroup):
        time_enabled: bool = True
        date_enabled: bool = True
        positioning_mode: bool = False  # When True, widgets move to top layer for repositioning
        time_positioning_mode: bool = False  # When True, time widget moves to top layer for repositioning
        date_positioning_mode: bool = False  # When True, date widget moves to top layer for repositioning

    class Wallpaper(OptionsGroup):
        depth_wall: str = ""

    class Rembg(OptionsGroup):
        enabled: bool = True
        model: str = "u2net"
        alpha_matting: bool = True
        foreground_threshold: int = 240
        background_threshold: int = 10
        erode_size: int = 15

    class Default(OptionsGroup):
        screenshot_app: list[str] = TrackedList()

    default = Default()
    user = User()
    settings = Settings()
    material = Material()
    time = Time()
    date = Date()
    desktop_widgets = DesktopWidgets()
    wallpaper = Wallpaper()
    rembg = Rembg()


user_options = UserOptions()

# Initialize rembg options with default values if not present
if not hasattr(user_options.rembg, "enabled"):
    user_options.rembg.enabled = True
if not hasattr(user_options.rembg, "model"):
    user_options.rembg.model = "u2net"
if not hasattr(user_options.rembg, "alpha_matting"):
    user_options.rembg.alpha_matting = True
if not hasattr(user_options.rembg, "foreground_threshold"):
    user_options.rembg.foreground_threshold = 240
if not hasattr(user_options.rembg, "background_threshold"):
    user_options.rembg.background_threshold = 10
if not hasattr(user_options.rembg, "erode_size"):
    user_options.rembg.erode_size = 15
for app in SCREENSHOT_APPS:
    if app not in user_options.default.screenshot_app:
        user_options.default.screenshot_app.append(app)
