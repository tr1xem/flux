import asyncio
from typing import Optional

from ignis import widgets
from ignis.services.mpris import MprisPlayer, MprisService

mpris = MprisService.get_default()


class Player(widgets.EventBox):
    def __init__(self) -> None:
        super().__init__(
            css_classes=["bar-player"],
            spacing=8,
        )

        self._player: Optional[MprisPlayer] = None

        self.title_label = widgets.Label(
            ellipsize="end",
            halign="start",
            css_classes=["media-title"],
            label="No Media Playing",
            max_width_chars=25,
        )

        self.play_pause_button = widgets.Button(
            css_classes=["media-controls"],
            child=widgets.Icon(
                image="play-symbolic",
                pixel_size=20,
            ),
            on_click=lambda x: self._play_pause(),
            sensitive=False,
        )

        self.append(self.title_label)
        self.append(self.play_pause_button)

        mpris.connect("player_added", lambda x, player: self._set_player(player))

        # Check if there's already an active player
        if mpris.players:
            self._set_player(mpris.players[0])

    def _set_player(self, player: MprisPlayer) -> None:
        if self._player:
            return  # Already have a player

        self._player = player

        # Update title binding
        self.title_label.label = player.bind("title", lambda x: x or "Unknown Title")

        # Update play/pause button
        self.play_pause_button.child.image = player.bind(
            "playback_status",
            lambda status: "pause-symbolic" if status == "Playing" else "play-symbolic",
        )
        self.play_pause_button.sensitive = True

        # Handle player removal when it closes
        player.connect("closed", lambda x: self._clear_player())

    def _clear_player(self) -> None:
        self._player = None
        self.title_label.label = "No Media Playing"
        self.play_pause_button.child.image = "play-symbolic"
        self.play_pause_button.sensitive = False

    def _play_pause(self) -> None:
        if self._player:
            asyncio.create_task(self._player.play_pause_async())
