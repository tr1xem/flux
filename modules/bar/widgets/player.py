import asyncio
import os
from typing import Optional

from ignis import utils, widgets
from ignis.services.mpris import MprisPlayer, MprisService

mpris = MprisService.get_default()


class Player(widgets.Box):
    def __init__(self, player: Optional[MprisPlayer] = None) -> None:
        self.playerContainer = widgets.Box(
            css_classes=["bar-player"],
        )
        super().__init__(
            visible=True,
            child=[self.playerContainer],
        )

        self._player = player
        self._is_no_media = player is None

        if player:
            player.connect("closed", lambda x: self.destroy())

        # Create UI elements based on whether we have a player or not
        if self._is_no_media:
            self._create_no_media_ui()
        else:
            self._create_player_ui()

    def _create_no_media_ui(self):
        """Create UI for when no media is playing"""
        self.songName = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-title", "no-media-title"],
            label="No Media Playing",
            max_width_chars=22,
        )

        # Add an empty artist label to maintain consistent layout
        self.songArtist = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-artist"],
            label="",  # Empty label to maintain layout
            max_width_chars=25,
        )

        self.mediaDetails = widgets.Box(
            vertical=True,
            hexpand=True,
            homogeneous=True,
            halign="start",
            child=[
                self.songName,
                self.songArtist,  # Include artist label for consistent layout
            ],
        )

        self.albumArt = widgets.Picture(
            css_classes=["media-album-art"],
            image=os.path.join(
                os.path.dirname(__file__), "../../../assets/icons/images/player.png"
            ),
        )

        # Non-functional control buttons for visual consistency
        self.control_buttons = widgets.Box(
            child=[
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="rewind-symbolic",
                        pixel_size=25,
                    ),
                    sensitive=False,
                ),
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="pause-symbolic",
                        pixel_size=25,
                    ),
                    sensitive=False,
                ),
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="fwd-symbolic",
                        pixel_size=25,
                    ),
                    sensitive=False,
                ),
            ],
        )

        self.playerContainer.append(
            widgets.Box(
                hexpand=True,
                child=[self.albumArt, self.mediaDetails, self.control_buttons],
            )
        )

    def _create_player_ui(self):
        """Create UI for when a media player is active"""
        if self._player is None:
            return

        self.songName = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-title"],
            label=self._player.bind("title", lambda x: x or "No Media Playing"),
            max_width_chars=22,
        )
        self.songArtist = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-artist"],
            label=self._player.bind("artist"),
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
            image=self._player.bind(
                "art-url",
                lambda x: x
                or os.path.join(
                    os.path.dirname(__file__), "../../../assets/icons/images/player.png"
                ),
            ),
        )

        self.control_buttons = widgets.Box(
            child=[
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="rewind-symbolic",
                        pixel_size=25,
                    ),
                    on_click=lambda x: asyncio.create_task(
                        self._player.previous_async()
                    )
                    if self._player
                    else None,
                    visible=self._player.bind("can_go_previous"),
                ),
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image=self._player.bind(
                            "playback_status",
                            lambda value: "pause-symbolic"
                            if value == "Playing"
                            else "play-symbolic",
                        ),
                        pixel_size=25,
                    ),
                    on_click=lambda x: asyncio.create_task(
                        self._player.play_pause_async()
                    )
                    if self._player
                    else None,
                    visible=self._player.bind("can_play"),
                ),
                widgets.Button(
                    css_classes=["media-controls"],
                    child=widgets.Icon(
                        image="fwd-symbolic",
                        pixel_size=25,
                    ),
                    on_click=lambda x: asyncio.create_task(self._player.next_async())
                    if self._player
                    else None,
                    visible=self._player.bind("can_go_next"),
                ),
            ],
        )

        self.playerContainer.append(
            widgets.Box(
                hexpand=True,
                child=[self.albumArt, self.mediaDetails, self.control_buttons],
            )
        )

    def destroy(self) -> None:
        if (
            not self._is_no_media
            and self.get_parent()
            and self.get_parent().get_parent()
        ):
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
            vertical=True,
            css_classes=["player-container"],
            on_scroll_down=lambda w: self.switch_players(1),
            on_scroll_up=lambda w: self.switch_players(-1),
        )

        # Initialize with no media player as a regular player
        self._add_no_media_player()

    def _add_no_media_player(self):
        """Add the no media player as a regular player in the list"""
        no_media_revealer = widgets.Revealer(
            child=Player(),  # Player with no MprisPlayer creates no-media UI
            transition_type="slide_up",
            reveal_child=True,
            transition_duration=500,
        )
        no_media_revealer.mpris_player = None
        no_media_revealer.is_no_media = True
        self.players.append(no_media_revealer)
        self.append(no_media_revealer)
        self.current = 0

    def add_player(self, obj: MprisPlayer) -> None:
        # Check if we currently only have the no media player
        has_only_no_media = (
            len(self.players) == 1
            and hasattr(self.players[0], "is_no_media")
            and self.players[0].is_no_media
        )

        revealer = widgets.Revealer(
            child=Player(obj),
            reveal_child=False,
            transition_type="slide_down",
            transition_duration=500,
        )
        revealer.mpris_player = obj
        revealer.is_no_media = False

        # Insert the new player after the current player
        insert_index = self.current + 1
        self.players.insert(insert_index, revealer)
        self.append(revealer)

        # Switch to the newly inserted player
        self.switch_to_player(insert_index)

    @utils.debounce(50)  # delay for 100 ms
    def switch_players(self, direction=1):
        print(self.players)

        next_index = (self.current + direction) % len(self.players)
        if self.players[next_index].is_no_media:
            return
        if direction == 1:
            self.players[self.current].transition_type = "slide_down"
        else:
            pass
            self.players[self.current].transition_type = "slide_up"
        self.players[self.current].reveal_child = False
        self.current = (self.current + direction) % len(self.players)
        # if self.players[self.current - 1].is_no_media:
        #     return
        if direction == 1:
            self.players[self.current].transition_type = "slide_up"
        else:
            self.players[self.current].transition_type = "slide_down"
        print(self.current)
        self.players[self.current].reveal_child = True

    def switch_to_player(self, index):
        if not (0 <= index < len(self.players)):
            return
        self.players[self.current].reveal_child = False
        # if len(self.players) > 0 and 0 <= self.current < len(self.players):
        self.current = index
        if self.players[self.current].is_no_media or index == 0:
            self.players[self.current].transition_type = "slide_down"
        else:
            self.players[self.current].transition_type = "slide_up"
        self.players[self.current].reveal_child = True

    def remove_player(self, revealer):
        if revealer not in self.players:
            return

        player_index = self.players.index(revealer)
        if self.current == player_index:
            if len(self.players) == 2:
                self.players[0].transition_type = "slide_down"
                self.switch_to_player(0)
                self.current = 0
                self.players.remove(revealer)
                self.remove(revealer)
            else:
                print(self.current)
                revealer.reveal_child = False
                self.players.remove(revealer)
                self.remove(revealer)

                if self.current >= len(self.players):
                    self.current = len(self.players) - 1  # Wrap to end
                self.switch_to_player(self.current)
        else:
            self.players.remove(revealer)
            self.remove(revealer)

            if player_index < self.current:
                self.current -= 1
