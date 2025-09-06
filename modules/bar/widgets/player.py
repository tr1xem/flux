import asyncio
from typing import List, Optional

from ignis import widgets
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.window_manager import WindowManager

from ...shared_widgets.circular_progress import CircularProgressBar

mpris = MprisService.get_default()

window_manager = WindowManager.get_default()


class Player(widgets.Box):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            css_classes=["bar-player"],
            spacing=8,
            vexpand=True,
            hexpand=True,
        )

        self._players: List[MprisPlayer] = []
        self._current_player: Optional[MprisPlayer] = None
        self._player_connections: dict = {}  # Track signal connections per player
        self._current_bindings: list = []  # Track current player bindings
        self._window = window_manager.get_window(f"ignis_MEDIA_{monitor_id}")
        self._monitor = 0
        
        # Cache for formatted strings to avoid repeated formatting
        self._cached_title = ""
        self._cached_artist = ""
        self._cached_label = ""

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
            on_click=self._on_play_pause_click,
            sensitive=False,
        )
        self._progress_bar = CircularProgressBar(
            line_width=2,
            size=(23, 23),
            start_angle=270,
            pie=True,
            end_angle=650,
            css_classes=["progress-player"],
        )
        self._progress_barOvelay = widgets.Overlay(
            child=self._progress_bar,
            halign="center",
            overlays=[self.play_pause_button],
            hexpand=True,
            vexpand=True,
        )
        self.eventBox = widgets.EventBox(
            hexpand=True,
            vexpand=True,
            on_click=self._on_event_box_click,
            child=[self.title_label],
        )

        self.append(widgets.Box(child=[self._progress_barOvelay]))
        # self.append(self._progress_bar)
        # self.append(self.play_pause_button)
        self.append(self.eventBox)

        mpris.connect("player_added", self._on_player_added)

        # Check if there's already an active player
        for player in mpris.players:
            self._add_player(player)

    def _format_label(self, player: MprisPlayer) -> str:
        """Format player title and artist - moved to class level to avoid function redefinition"""
        title = player.title or "Unknown Title"
        artist = player.artist
        
        # Cache check to avoid repeated string formatting
        if self._cached_title == title and self._cached_artist == artist:
            return self._cached_label
        
        # Update cache
        self._cached_title = title
        self._cached_artist = artist
        self._cached_label = f"{title} • {artist}" if artist else title
        
        return self._cached_label

    def _on_player_added(self, service, player):
        """Handle player_added signal - method reference instead of lambda"""
        self._add_player(player)

    def _on_play_pause_click(self, button):
        """Handle play/pause button click - method reference instead of lambda"""
        self._play_pause()

    def _on_event_box_click(self, event_box):
        """Handle event box click - method reference instead of lambda"""
        self.__on_click(event_box)

    def _on_playback_changed(self, player, param=None):
        """Handle playback status change - method reference instead of lambda"""
        # Switch to this player if it just started playing
        if player.playback_status == "Playing" and self._current_player != player:
            self._switch_to_player(player)

    def _on_player_closed(self, player):
        """Handle player closed - method reference instead of lambda"""
        self._remove_player(player)

    def _on_length_changed(self, player, param=None):
        """Handle length property change - method reference instead of lambda"""
        if hasattr(self._progress_bar, '_max_value'):
            self._progress_bar._max_value = player.length or 1

    def _on_position_changed(self, player, param=None):
        """Handle position property change - method reference instead of lambda"""
        if hasattr(self._progress_bar, '_value'):
            self._progress_bar._value = player.position or 0

    def _on_title_changed(self, player, param=None):
        """Handle title change - method reference instead of lambda"""
        self.title_label.label = self._format_label(player)

    def _on_artist_changed(self, player, param=None):
        """Handle artist change - method reference instead of lambda"""
        self.title_label.label = self._format_label(player)

    def _add_player(self, player: MprisPlayer) -> None:
        if player in self._players:
            return

        self._players.append(player)

        # Store signal connections for this player using method references
        connections = []
        connections.append(player.connect("notify::playback-status", self._on_playback_changed))
        connections.append(player.connect("closed", self._on_player_closed))
        self._player_connections[player] = connections

        # Switch to this player if it's currently playing or if we have no current player
        if player.playback_status == "Playing" or self._current_player is None:
            self._switch_to_player(player)

    def _remove_player(self, player: MprisPlayer) -> None:
        if player in self._players:
            # Disconnect signal connections to prevent memory leaks
            if player in self._player_connections:
                for connection_id in self._player_connections[player]:
                    player.disconnect(connection_id)
                del self._player_connections[player]
                
            self._players.remove(player)

            if self._current_player == player:
                # Clear current bindings before switching
                self._clear_current_bindings()
                
                # Find another playing player or fall back to any available player
                next_player = self._find_playing_player() or (
                    self._players[0] if self._players else None
                )
                if next_player:
                    self._switch_to_player(next_player)
                else:
                    self._clear_player()

    def _find_playing_player(self) -> Optional[MprisPlayer]:
        for player in self._players:
            if player.playback_status == "Playing":
                return player
        return None

    def _clear_current_bindings(self) -> None:
        """Clear current player bindings to prevent memory leaks"""
        # Properly destroy bindings instead of just clearing the list
        for binding in self._current_bindings:
            if hasattr(binding, 'destroy'):
                binding.destroy()
            elif hasattr(binding, 'disconnect'):
                binding.disconnect()
        self._current_bindings.clear()

    def _switch_to_player(self, player: MprisPlayer) -> None:
        # Clear previous bindings first
        self._clear_current_bindings()
        
        self._current_player = player

        # Store new bindings for cleanup later
        max_value_binding = player.bind("length")
        value_binding = player.bind("position") 
        title_binding = player.bind("title", lambda _: self._format_label(player))
        playback_binding = player.bind("playback_status", lambda status: "pause-symbolic" if status == "Playing" else "play-symbolic")
        
        self._current_bindings.extend([max_value_binding, value_binding, title_binding, playback_binding])
        
        # Add signal connections to existing player connections for proper cleanup
        if player in self._player_connections:
            self._player_connections[player].extend([
                player.connect("notify::length", self._on_length_changed),
                player.connect("notify::position", self._on_position_changed),
                player.connect("notify::artist", self._on_artist_changed)
            ])

        # Set initial values
        self.title_label.label = title_binding
        self.play_pause_button.child.image = playback_binding
        self.play_pause_button.sensitive = True

    def _clear_player(self) -> None:
        self._clear_current_bindings()
        self._current_player = None
        self.title_label.label = "No Media Playing"
        self.play_pause_button.child.image = "play-symbolic"
        # Use property setters directly to avoid binding issues
        self._progress_bar._value = 1
        self._progress_bar._max_value = 1
        self.play_pause_button.sensitive = False

    def _play_pause(self) -> None:
        if self._current_player:
            asyncio.create_task(self._current_player.play_pause_async())

    def __on_click(self, x) -> None:
        # Simplified window handling
        try:
            window_manager.toggle_window(f"ignis_MEDIA_{self._monitor}")
        except:
            # Fallback if toggle is not available
            pass
