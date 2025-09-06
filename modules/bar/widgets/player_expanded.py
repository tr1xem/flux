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

def toggle_expanded_player(monitor: int):
    """Toggle or switch the expanded player window to the specified monitor"""
    window_name = "ignis_MEDIA_0"
    window = window_manager.get_window(window_name)
    
    if window and hasattr(window, 'visible') and hasattr(window, 'monitor'):
        if window.visible and window.monitor == monitor:
            # Same monitor and visible - toggle off
            window.visible = False
        else:
            # Different monitor or not visible - switch and show
            if window.monitor != monitor:
                window.set_monitor(monitor)
            window.visible = True

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
        self._signal_connections = []
        
        # Initialize the widget first before doing anything else
        super().__init__(
            transition_type="slide_down",
            reveal_child=False,
            css_classes=[self.get_css("media")],
            child=self._create_widget_content()
        )
        
        # Now set up signal connections after widget is initialized
        closed_id = player.connect("closed", self._on_closed)
        art_url_id = player.connect("notify::art-url", self._on_art_url_changed)
        self._signal_connections.extend([closed_id, art_url_id])
        
        self.load_colors()
    
    def _create_widget_content(self):
        """Create the widget content - separated to ensure proper initialization order"""
        return widgets.Overlay(
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
                                            label=self._player.bind("title"),
                                            max_width_chars=30,
                                            halign="start",
                                            css_classes=[
                                                self.get_css("media-title")
                                            ],
                                        ),
                                        widgets.Label(
                                            label=self._player.bind("artist"),
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
                                        image=self._player.bind(
                                            "playback_status",
                                            lambda value: "pause-symbolic"
                                            if value == "Playing"
                                            else "play-symbolic",
                                        ),
                                        pixel_size=18,
                                    ),
                                    on_click=self._on_play_pause_clicked,
                                    visible=self._player.bind("can_play"),
                                    css_classes=self._player.bind(
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
                            value=self._player.bind("position"),
                            max=self._player.bind("length"),
                            hexpand=True,
                            css_classes=[self.get_css("media-scale")],
                            on_change=self._on_scale_changed,
                            visible=self._player.bind(
                                "position", lambda value: value != -1
                            ),
                        ),
                        widgets.Button(
                            child=widgets.Icon(
                                image="rewind-symbolic",
                                pixel_size=20,
                            ),
                            css_classes=[self.get_css("media-skip-button")],
                            on_click=self._on_previous_clicked,
                            visible=self._player.bind("can_go_previous"),
                            style="margin-left: 1rem;",
                        ),
                        widgets.Button(
                            child=widgets.Icon(
                                image="fwd-symbolic",
                                pixel_size=20,
                            ),
                            css_classes=[self.get_css("media-skip-button")],
                            on_click=self._on_next_clicked,
                            visible=self._player.bind("can_go_next"),
                            style="margin-left: 1rem;",
                        ),
                    ],
                ),
            ],
        )

    def _on_closed(self, player):
        """Handle player closed signal - method reference instead of lambda"""
        self.destroy()

    def _on_art_url_changed(self, player, param):
        """Handle art URL change - method reference instead of lambda"""
        self.load_colors()

    def _on_play_pause_clicked(self, button):
        """Handle play/pause button click - method reference instead of lambda"""
        asyncio.create_task(self._player.play_pause_async())

    def _on_scale_changed(self, scale):
        """Handle scale position change - method reference instead of lambda"""
        asyncio.create_task(self._player.set_position_async(scale.value))

    def _on_previous_clicked(self, button):
        """Handle previous button click - method reference instead of lambda"""
        asyncio.create_task(self._player.previous_async())

    def _on_next_clicked(self, button):
        """Handle next button click - method reference instead of lambda"""
        asyncio.create_task(self._player.next_async())

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
                                                label=self._player.bind("title"),
                                                max_width_chars=30,
                                                halign="start",
                                                css_classes=[
                                                    self.get_css("media-title")
                                                ],
                                            ),
                                            widgets.Label(
                                                label=self._player.bind("artist"),
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
                                            image=self._player.bind(
                                                "playback_status",
                                                lambda value: "pause-symbolic"
                                                if value == "Playing"
                                                else "play-symbolic",
                                            ),
                                            pixel_size=18,
                                        ),
                                        on_click=self._on_play_pause_clicked,
                                        visible=self._player.bind("can_play"),
                                        css_classes=self._player.bind(
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
                                value=self._player.bind("position"),
                                max=self._player.bind("length"),
                                hexpand=True,
                                css_classes=[self.get_css("media-scale")],
                                on_change=self._on_scale_changed,
                                visible=self._player.bind(
                                    "position", lambda value: value != -1
                                ),
                            ),
                            widgets.Button(
                                child=widgets.Icon(
                                    image="rewind-symbolic",
                                    pixel_size=20,
                                ),
                                css_classes=[self.get_css("media-skip-button")],
                                on_click=self._on_previous_clicked,
                                visible=self._player.bind("can_go_previous"),
                                style="margin-left: 1rem;",
                            ),
                            widgets.Button(
                                child=widgets.Icon(
                                    image="fwd-symbolic",
                                    pixel_size=20,
                                ),
                                css_classes=[self.get_css("media-skip-button")],
                                on_click=self._on_next_clicked,
                                visible=self._player.bind("can_go_next"),
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
        # Store references before clearing them
        player = self._player
        
        # Disconnect all signal connections to prevent memory leaks  
        if player:
            for connection_id in self._signal_connections:
                try:
                    player.disconnect(connection_id)
                except:
                    pass  # Connection might already be disconnected
        self._signal_connections.clear()
        
        # Clean up CSS to prevent accumulation
        if player:
            css_name = self.clean_desktop_entry()
            if css_name in css_manager.list_css_info_names():
                css_manager.remove_css(css_name)
        
        # Clear any cached colors file
        if os.path.exists(self._colors_path):
            try:
                os.remove(self._colors_path)
            except OSError:
                pass
                
        self.set_reveal_child(False)
        utils.Timeout(self.transition_duration, lambda: self.unparent() if self.get_parent() else None)

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

        css_name = self.clean_desktop_entry()
        # Always remove existing CSS before applying new one to prevent accumulation
        if css_name in css_manager.list_css_info_names():
            css_manager.remove_css(css_name)

        css_manager.apply_css(
            CssInfoString(
                name=css_name,
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
            css_classes=["rec-unset"],
        )
        self._player_widgets = {}  # Track player widgets for cleanup
        
        # Connect to player_added event using method reference
        mpris.connect("player_added", self._on_player_added)

    def _on_player_added(self, service, player):
        """Handle player_added signal - method reference instead of lambda"""
        self.__add_player(player)

    def _on_media_player_closed(self, player):
        """Handle player closed signal - method reference instead of lambda"""
        self.__remove_player(player)

    def __add_player(self, obj: MprisPlayer) -> None:
        # Check if we already have a widget for this player
        if obj in self._player_widgets:
            return
            
        player = Player(obj)
        self._player_widgets[obj] = player
        self.append(player)
        player.set_reveal_child(True)
        
        # Connect to player removal to clean up widget using method reference
        obj.connect("closed", self._on_media_player_closed)
    
    def __remove_player(self, obj: MprisPlayer) -> None:
        if obj in self._player_widgets:
            player_widget = self._player_widgets[obj]
            # The Player widget's destroy method will handle cleanup
            player_widget.destroy()
            del self._player_widgets[obj]


class ExpandedPlayerWindow(widgets.RevealerWindow):
    def __init__(self, monitor_id: int = 0):
        # Always use monitor 0 for single instance, but store requested monitor
        self.requested_monitor = monitor_id
        
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
            on_click=lambda x: window_manager.close_window("ignis_MEDIA_0"),
        )
        
        super().__init__(
            visible=False,
            popup=True,
            monitor=0,  # Always start on monitor 0 for single instance
            kb_mode="on_demand",
            layer="top",
            css_classes=["unset"],
            anchor=["top", "left", "bottom", "right"],
            namespace="ignis_MEDIA_0",  # Always use 0 for single instance
            child=widgets.CenterBox(
                hexpand=True,
                halign="fill",
                vexpand=True,
                vertical=False,
                start_widget=widgets.Button(
                    vexpand=True,
                    hexpand=True,
                    css_classes=["unset"],
                    on_click=lambda x: window_manager.close_window("ignis_MEDIA_0"),
                ),
                center_widget=widgets.Box(
                    vertical=True, child=[revealer, self.closeButton]
                ),
                end_widget=widgets.Button(
                    vexpand=True,
                    hexpand=True,
                    css_classes=["unset"],
                    on_click=lambda x: window_manager.close_window("ignis_MEDIA_0"),
                ),
            ),
            setup=lambda self: self.connect(
                "notify::visible", lambda x, y: opened_menu.set_value("")
            ),
            revealer=revealer,
        )
