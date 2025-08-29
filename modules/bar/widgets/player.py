import asyncio

from ignis import widgets
from ignis.services.mpris import MprisPlayer, MprisService

mpris = MprisService.get_default()


class Player(widgets.Box):
    def __init__(self, player: MprisPlayer) -> None:
        self.playerContainer = widgets.CenterBox(
            css_classes=["bar-player"],
        )
        super().__init__(
            visible=True,
            child=[self.playerContainer],
        )
        self._player = player
        self.songName = widgets.Label(
            ellipsize="end",
            label=player.bind("title"),
            max_width_chars=12,
        )
        self.songArtist = widgets.Label(
            ellipsize="end",
            label=player.bind("artist"),
            max_width_chars=8,
        )
        self.mediaDetails = widgets.Box(
            vertical=True,
            hexpand=True,
            halign="start",
            child=[
                self.songName,
                self.songArtist,
            ],
        )
        self.albumArt = widgets.Picture(
            image=player.bind("art-url"),
        )

        self.control_buttons = widgets.Box(
            child=[
                # widgets.Scale(
                #     value=player.bind("position"),
                #     max=player.bind("length"),
                #     hexpand=True,
                #     # css_classes=[self.get_css("media-scale")],
                #     on_change=lambda x: asyncio.create_task(
                #         self._player.set_position_async(x.value)
                #     ),
                #     visible=player.bind("position", lambda value: value != -1),
                # ),
                widgets.Button(
                    child=widgets.Icon(
                        image="media-skip-backward-symbolic",
                        pixel_size=20,
                    ),
                    # css_classes=[self.get_css("media-skip-button")],
                    on_click=lambda x: asyncio.create_task(player.previous_async()),
                    visible=player.bind("can_go_previous"),
                ),
                widgets.Button(
                    child=widgets.Icon(
                        image=player.bind(
                            "playback_status",
                            lambda value: "media-playback-pause-symbolic"
                            if value == "Playing"
                            else "media-playback-start-symbolic",
                        ),
                        pixel_size=18,
                    ),
                    on_click=lambda x: asyncio.create_task(player.play_pause_async()),
                    visible=player.bind("can_play"),
                    css_classes=player.bind(
                        "playback_status",
                        lambda value: [
                            "playing",
                        ]
                        if value == "Playing"
                        else [
                            "paused",
                        ],
                    ),
                ),
                widgets.Button(
                    child=widgets.Icon(
                        image="media-skip-forward-symbolic",
                        pixel_size=20,
                    ),
                    # css_classes=[self.get_css("media-skip-button")],
                    on_click=lambda x: asyncio.create_task(player.next_async()),
                    visible=player.bind("can_go_next"),
                ),
            ]
        )

        self.playerContainer.start_widget = widgets.Box(
            child=[self.albumArt, self.mediaDetails]
        )
        # self.playerContainer.center_widget = self.mediaDetails
        self.playerContainer.end_widget = self.control_buttons
        # self.playerContainer.append(widgets.Label(label="Player"))
        # self.add_child(self.playerContainer)


class Media(widgets.EventBox):
    def __init__(self):
        self.players = dict()
        self.current_player = 0

        self.player_count = 0
        super().__init__(
            setup=lambda self: mpris.connect(
                "player_added", lambda x, player: self.__add_player(player)
            ),
            # vertical=True,
            css_classes=["player-container", "hidden-scrollbar"],
            on_scroll_down=lambda widget: self._next_player(),
            on_scroll_up=lambda widget: self._previous_player(),
        )

    def __add_player(self, obj: MprisPlayer) -> None:
        player = Player(obj)
        player_revealer = widgets.Revealer(
            child=player,
            reveal_child=self.player_count
            == 0,  # Reveal only if this is the first player
            # FIXME: Identify why other transitions are not working
            transition_type="slide_right",
            transition_duration=300,
        )
        self.players[self.player_count] = player_revealer
        self.player_count += 1

        # # Set the child to the first player when it's added
        # if self.player_count == 1:
        #     self.child = player_revealer
        #
        self.append(player_revealer)
        print(self.players)

    def _next_player(self):
        """Show next player on scroll down"""
        if self.player_count <= 1:
            return False

        # Hide current player
        self.players[self.current_player].reveal_child = False

        # Move to next player (wrap around to 0 if at end)
        self.current_player = (self.current_player + 1) % self.player_count

        # Show new current player
        self.players[self.current_player].reveal_child = True

        return True

    def _previous_player(self):
        """Show previous player on scroll up"""
        if self.player_count <= 1:
            return False

        # Hide current player
        self.players[self.current_player].reveal_child = False

        # Move to previous player (wrap around to end if at beginning)
        self.current_player = (self.current_player - 1) % self.player_count

        # Show new current player
        self.players[self.current_player].reveal_child = True

        return True
