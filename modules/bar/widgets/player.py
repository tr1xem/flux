import asyncio

from ignis import utils, widgets
from ignis.services.mpris import MprisPlayer, MprisService

mpris = MprisService.get_default()


class Player(widgets.Box):
    def __init__(self, player: MprisPlayer) -> None:
        self.playerContainer = widgets.Box(
            css_classes=["bar-player"],
        )
        super().__init__(
            visible=True,
            child=[self.playerContainer],
        )
        player.connect("closed", lambda x: self.destroy())
        self._player = player
        self.songName = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-title"],
            label=player.bind("title"),
            max_width_chars=22,
        )
        self.songArtist = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-artist"],
            label=player.bind("artist"),
            max_width_chars=25,
        )
        self.mediaDetails = widgets.Box(
            vertical=True,
            hexpand=True,
            homogeneous=True,
            halign="start",
            child=[
                self.songName,
                self.songArtist,
            ],
        )
        self.albumArt = widgets.Picture(
            css_classes=["media-album-art"],
            image=player.bind("art-url"),
        )

        self.control_buttons = widgets.Box(
            child=[
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="media-skip-backward-symbolic",
                        pixel_size=25,
                    ),
                    # css_classes=[self.get_css("media-skip-button")],
                    on_click=lambda x: asyncio.create_task(player.previous_async()),
                    visible=player.bind("can_go_previous"),
                ),
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image=player.bind(
                            "playback_status",
                            lambda value: "media-playback-pause-symbolic"
                            if value == "Playing"
                            else "media-playback-start-symbolic",
                        ),
                        pixel_size=25,
                    ),
                    on_click=lambda x: asyncio.create_task(player.play_pause_async()),
                    visible=player.bind("can_play"),
                ),
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="media-skip-forward-symbolic",
                        pixel_size=25,
                    ),
                    # css_classes=[self.get_css("media-skip-button")],
                    on_click=lambda x: asyncio.create_task(player.next_async()),
                    visible=player.bind("can_go_next"),
                ),
            ],
        )

        self.playerContainer.append(
            widgets.Box(
                hexpand=True,
                child=[self.albumArt, self.mediaDetails, self.control_buttons],
            )
        )
        # self.playerContainer.end_widget = self.control_buttons

    def destroy(self) -> None:
        self.get_parent().get_parent().switch_players(1)
        self.get_parent().get_parent().remove_player(self.get_parent())
        super().unparent()


class Media(widgets.EventBox):
    def __init__(self):
        self.players = []
        self.current = 0

        super().__init__(
            setup=lambda self: mpris.connect(
                "player_added", lambda x, p: self.add_player(p)
            ),
            css_classes=["player-container"],
            on_scroll_down=lambda w: self.switch_players(1),
            on_scroll_up=lambda w: self.switch_players(-1),
        )

    def add_player(self, obj: MprisPlayer) -> None:
        revealer = widgets.Revealer(
            child=Player(obj),
            reveal_child=False,
            transition_type="slide_right",
            transition_duration=250,
        )
        revealer.mpris_player = obj
        self.players.append(revealer)
        self.append(revealer)
        self.switch_to_player(len(self.players) - 1)

    @utils.debounce(100)  # delay for 500 ms (0.5 s)
    def switch_players(self, direction=1):
        if len(self.players) <= 1:
            pass
        self.players[self.current].reveal_child = False
        self.current = (self.current + direction) % len(self.players)
        self.players[self.current].reveal_child = True

    def switch_to_player(self, index):
        if not (0 <= index < len(self.players)):
            pass
        if len(self.players) > 0 and 0 <= self.current < len(self.players):
            self.players[self.current].reveal_child = False
        self.current = index
        self.players[self.current].reveal_child = True

    def remove_player(self, revealer):
        if revealer not in self.players:
            return
        if self.players.index(revealer) == self.current and len(self.players) > 1:
            self.switch_players(1)
        self.remove(revealer)
        self.players.remove(revealer)
        if self.current >= len(self.players):
            self.current = max(0, len(self.players) - 1)
