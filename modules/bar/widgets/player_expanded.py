import asyncio
import os

import ignis
from ignis import utils, widgets
from ignis.css_manager import CssInfoString, CssManager
from ignis.services.applications import ApplicationsService
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.window_manager import WindowManager
from jinja2 import Template
from services.material import MaterialService

from .menu import opened_menu

applications = ApplicationsService.get_default()


mpris = MprisService.get_default()
css_manager = CssManager.get_default()
material = MaterialService.get_default()

window_manager = WindowManager.get_default()

MEDIA_TEMPLATE = utils.get_current_dir() + "/media.scss"
MEDIA_SCSS_CACHE_DIR = ignis.CACHE_DIR + "/media"  # type: ignore
MEDIA_ART_FALLBACK = (
    utils.get_current_dir() + "/../../../assets/icons/images/player.png"
)
os.makedirs(MEDIA_SCSS_CACHE_DIR, exist_ok=True)


PLAYER_ICONS = {
    "spotify": "spotify-symbolic",
    "firefox": "firefox-browser-symbolic",
    "chrome": "chrome-symbolic",
    None: "folder-music-symbolic",
}


class Player(widgets.Revealer):
    def __init__(self, player: MprisPlayer) -> None:
        self._player = player
        self._colors_path = f"{MEDIA_SCSS_CACHE_DIR}/{self.clean_desktop_entry()}.scss"
        player.connect("closed", lambda x: self.destroy())
        player.connect("notify::art-url", lambda x, y: self.load_colors())
        self.load_colors()

        super().__init__(
            transition_type="slide_down",
            reveal_child=False,
            css_classes=[self.get_css("media")],
            child=widgets.Overlay(
                child=widgets.Box(css_classes=[self.get_css("media-image")]),
                overlays=[
                    widgets.Box(
                        hexpand=True,
                        vexpand=True,
                        css_classes=[self.get_css("media-image-gradient")],
                    ),
                    widgets.Icon(
                        icon_name=self.get_player_icon(),
                        pixel_size=22,
                        halign="start",
                        valign="start",
                        css_classes=[self.get_css("media-player-icon")],
                    ),
                    widgets.Box(
                        vertical=True,
                        hexpand=True,
                        css_classes=[self.get_css("media-content")],
                        child=[
                            widgets.Box(
                                vexpand=True,
                                valign="center",
                                child=[
                                    widgets.Box(
                                        hexpand=True,
                                        vertical=True,
                                        child=[
                                            widgets.Label(
                                                ellipsize="end",
                                                label=player.bind("title"),
                                                max_width_chars=30,
                                                halign="start",
                                                css_classes=[
                                                    self.get_css("media-title")
                                                ],
                                            ),
                                            widgets.Label(
                                                label=player.bind("artist"),
                                                max_width_chars=30,
                                                ellipsize="end",
                                                halign="start",
                                                css_classes=[
                                                    self.get_css("media-artist")
                                                ],
                                            ),
                                        ],
                                    ),
                                    widgets.Button(
                                        child=widgets.Icon(
                                            image=player.bind(
                                                "playback_status",
                                                lambda value: "pause-symbolic"
                                                if value == "Playing"
                                                else "play-symbolic",
                                            ),
                                            pixel_size=18,
                                        ),
                                        on_click=lambda x: asyncio.create_task(
                                            player.play_pause_async()
                                        ),
                                        visible=player.bind("can_play"),
                                        css_classes=player.bind(
                                            "playback_status",
                                            lambda value: [
                                                self.get_css("media-playback-button"),
                                                "playing",
                                            ]
                                            if value == "Playing"
                                            else [
                                                self.get_css("media-playback-button"),
                                                "paused",
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    widgets.Box(
                        vexpand=True,
                        valign="end",
                        style="padding: 1rem;",
                        child=[
                            widgets.Scale(
                                value=player.bind("position"),
                                max=player.bind("length"),
                                hexpand=True,
                                css_classes=[self.get_css("media-scale")],
                                on_change=lambda x: asyncio.create_task(
                                    self._player.set_position_async(x.value)
                                ),
                                visible=player.bind(
                                    "position", lambda value: value != -1
                                ),
                            ),
                            widgets.Button(
                                child=widgets.Icon(
                                    image="rewind-symbolic",
                                    pixel_size=20,
                                ),
                                css_classes=[self.get_css("media-skip-button")],
                                on_click=lambda x: asyncio.create_task(
                                    player.previous_async()
                                ),
                                visible=player.bind("can_go_previous"),
                                style="margin-left: 1rem;",
                            ),
                            widgets.Button(
                                child=widgets.Icon(
                                    image="fwd-symbolic",
                                    pixel_size=20,
                                ),
                                css_classes=[self.get_css("media-skip-button")],
                                on_click=lambda x: asyncio.create_task(
                                    player.next_async()
                                ),
                                visible=player.bind("can_go_next"),
                                style="margin-left: 1rem;",
                            ),
                        ],
                    ),
                ],
            ),
        )

    def get_player_icon(self):
        if (
            applications.search(applications.apps, query=self.clean_desktop_entry())
            is not None
        ):  # pyright: ignore[reportOptionalMemberAccess]
            return applications.search(
                applications.apps,
                query=self.clean_desktop_entry(),  # pyright: ignore[reportOptionalMemberAccess]
            )[0].icon
        elif applications.search(applications.apps, query=self._player.identity):  # pyright: ignore[reportOptionalMemberAccess]
            return applications.search(applications.apps, query=self._player.identity)[  # pyright: ignore[reportOptionalMemberAccess]
                0
            ].icon
        else:
            return "folder-music-symbolic"

    def destroy(self) -> None:
        self.set_reveal_child(False)
        utils.Timeout(self.transition_duration, super().unparent)

    def get_css(self, class_name: str) -> str:
        return f"{class_name}-{self.clean_desktop_entry()}"

    def load_colors(self) -> None:
        if not self._player.art_url:
            art_url = MEDIA_ART_FALLBACK
        else:
            art_url = self._player.art_url

        colors = material.get_colors_from_img(art_url, True)
        colors["art_url"] = art_url
        colors["desktop_entry"] = self.clean_desktop_entry()

        with open(MEDIA_TEMPLATE) as file:
            template_rendered = Template(file.read()).render(colors)

        if self._player.desktop_entry in css_manager.list_css_info_names():
            css_manager.remove_css(self.clean_desktop_entry())

        css_manager.apply_css(
            CssInfoString(
                name=self.clean_desktop_entry(),
                compiler_function=lambda string: utils.sass_compile(string=string),
                string=template_rendered,
            )
        )

    def clean_desktop_entry(self) -> str:
        desktop_entry = self._player.desktop_entry
        if desktop_entry is not None:
            import os

            filename = os.path.basename(desktop_entry)

            # Remove .desktop extension if present
            if filename.endswith(".desktop"):
                filename = filename[:-8]

            # Replace dots with dashes
            result = filename.replace(".", "-")

            return result

        else:
            return self._player.identity.replace(".", "-")


class Media(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            setup=lambda self: mpris.connect(
                "player_added", lambda x, player: self.__add_player(player)
            ),
            css_classes=["rec-unset"],
        )

    def __add_player(self, obj: MprisPlayer) -> None:
        player = Player(obj)
        self.append(player)
        player.set_reveal_child(True)


class ExpandedPlayerWindow(widgets.RevealerWindow):
    def __init__(self, monitor_id: int = 0):
        revealer = widgets.Revealer(
            transition_type="slide_down",
            child=widgets.Box(
                vertical=True,
                css_classes=["media-window"],
                child=[
                    widgets.Box(
                        vertical=True,
                        child=[
                            Media(),
                        ],
                    ),
                    # NotificationCenter(),
                ],
            ),
            transition_duration=500,
            reveal_child=True,
        )

        self.closeButton = widgets.Button(
            vexpand=True,
            hexpand=True,
            css_classes=["unset"],
            on_click=lambda x: window_manager.close_window(f"ignis_MEDIA_{monitor_id}"),
        )
        super().__init__(
            visible=False,
            popup=True,
            monitor=monitor_id,
            kb_mode="on_demand",
            layer="top",
            css_classes=["unset"],
            anchor=["top", "left", "bottom", "right"],
            namespace=f"ignis_MEDIA_{monitor_id}",
            child=widgets.CenterBox(
                hexpand=True,
                halign="fill",
                vexpand=True,
                vertical=False,
                start_widget=widgets.Button(
                    vexpand=True,
                    hexpand=True,
                    css_classes=["unset"],
                    on_click=lambda x: window_manager.close_window(
                        f"ignis_MEDIA_{monitor_id}"
                    ),
                ),
                center_widget=widgets.Box(
                    vertical=True, child=[revealer, self.closeButton]
                ),
                end_widget=widgets.Button(
                    vexpand=True,
                    hexpand=True,
                    css_classes=["unset"],
                    on_click=lambda x: window_manager.close_window(
                        f"ignis_MEDIA_{monitor_id}"
                    ),
                ),
            ),
            setup=lambda self: self.connect(
                "notify::visible", lambda x, y: opened_menu.set_value("")
            ),
            revealer=revealer,
        )
