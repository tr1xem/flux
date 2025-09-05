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

    class Wallpaper(OptionsGroup):
        depth_wall: str = ""
        depth_wall_enabled: bool = True

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


user_options = UserOptions()
for app in SCREENSHOT_APPS:
    if app not in user_options.default.screenshot_app:
        user_options.default.screenshot_app.append(app)
