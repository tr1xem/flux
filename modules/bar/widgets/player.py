import asyncio
from typing import List, Optional

from ignis import widgets
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.window_manager import WindowManager

from ...shared_widgets.circular_progress import CircularProgressBar

mpris = MprisService.get_default()

window_manager = WindowManager.get_default()


class Player(widgets.Box):
    def __init__(self) -> None:
        super().__init__(
            css_classes=["bar-player"],
            spacing=8,
            vexpand=True,
            hexpand=True,
        )

        self._players: List[MprisPlayer] = []
        self._current_player: Optional[MprisPlayer] = None
        self._window = window_manager.get_window("ignis_media")
        self._monitor = 0

        self.title_label = widgets.Label(
            valign="center",
            ellipsize="end",
            halign="start",
            css_classes=["media-title"],
            label="No Media Playing",
            max_width_chars=25,
        )

        self.play_pause_button = widgets.Button(
            css_classes=[
                "media-controls",
            ],
            child=widgets.Icon(
                css_classes=["media-icon-s"],
                image="play-symbolic",
                pixel_size=16,
            ),
            on_click=lambda x: self._play_pause(),
            sensitive=False,
        )
        self._progress_bar = CircularProgressBar(
            line_width=2,
            size=(20, 20),
            start_angle=270,
            end_angle=650,
            css_classes=["progress-player"],
        )
        self._progress_barOvelay = widgets.Overlay(
            child=self.play_pause_button,
            halign="center",
            overlays=[self._progress_bar],
            hexpand=True,
            vexpand=True,
        )
        self.eventBox = widgets.EventBox(
            hexpand=True,
            vexpand=True,
            on_click=lambda x: self.__on_click(x),
            child=[self.title_label],
        )

        self.append(widgets.Box(child=[self._progress_barOvelay]))
        # self.append(self._progress_bar)
        # self.append(self.play_pause_button)
        self.append(self.eventBox)

        mpris.connect("player_added", lambda x, player: self._add_player(player))

        # Check if there's already an active player
        for player in mpris.players:
            self._add_player(player)

    def _add_player(self, player: MprisPlayer) -> None:
        if player in self._players:
            return

        self._players.append(player)

        # Listen for playback status changes
        player.connect(
            "notify::playback-status", lambda p, _: self._on_playback_changed(p)
        )

        # Handle player removal when it closes
        player.connect("closed", lambda p: self._remove_player(p))

        # Switch to this player if it's currently playing or if we have no current player
        if player.playback_status == "Playing" or self._current_player is None:
            self._switch_to_player(player)

    def _remove_player(self, player: MprisPlayer) -> None:
        if player in self._players:
            self._players.remove(player)

            if self._current_player == player:
                # Find another playing player or fall back to any available player
                next_player = self._find_playing_player() or (
                    self._players[0] if self._players else None
                )
                if next_player:
                    self._switch_to_player(next_player)
                else:
                    self._clear_player()

    def _on_playback_changed(self, player: MprisPlayer) -> None:
        # Switch to this player if it just started playing
        if player.playback_status == "Playing" and self._current_player != player:
            self._switch_to_player(player)

    def _find_playing_player(self) -> Optional[MprisPlayer]:
        for player in self._players:
            if player.playback_status == "Playing":
                return player
        return None

    def _switch_to_player(self, player: MprisPlayer) -> None:
        self._current_player = player

        self._progress_bar.max_value = player.bind("length")
        self._progress_bar.value = player.bind("position")

        # Update title binding with artist
        def format_label():
            title = player.title or "Unknown Title"
            artist = player.artist
            return f"{title} • {artist}" if artist else title

        self.title_label.label = player.bind("title", lambda _: format_label())
        player.connect(
            "notify::artist",
            lambda *_: setattr(self.title_label, "label", format_label()),
        )

        # Update play/pause button
        self.play_pause_button.child.image = player.bind(
            "playback_status",
            lambda status: "pause-symbolic" if status == "Playing" else "play-symbolic",
        )
        self.play_pause_button.sensitive = True

    def _clear_player(self) -> None:
        self._current_player = None
        self.title_label.label = "No Media Playing"
        self.play_pause_button.child.image = "play-symbolic"
        self.play_pause_button.sensitive = False

    def _play_pause(self) -> None:
        if self._current_player:
            asyncio.create_task(self._current_player.play_pause_async())

    def __on_click(self, x) -> None:
        if self._window.monitor == self._monitor:
            self._window.visible = not self._window.visible
        else:
            self._window.set_monitor(self._monitor)
            self._window.visible = True
