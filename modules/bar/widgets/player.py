import asyncio

from ignis import widgets
from ignis.services.mpris import MprisPlayer, MprisService

mpris = MprisService.get_default()


class Player(widgets.Revealer):
    def __init__(self, player: MprisPlayer) -> None:
        self.playerContainer = widgets.Box(
            css_classes=["bar-player"],
        )
        super().__init__(
            reveal_child=True,
            child=self.playerContainer,
        )
        self._player = player
        self.mediaDetails = widgets.Box(vertical=True)
        self.songName = widgets.Label(
            ellipsize="end",
            label=player.bind("title"),
            max_width_chars=30,
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

        self.playerContainer.append(self.albumArt)
        self.playerContainer.append(self.songName)
        self.playerContainer.append(self.control_buttons)
        # self.playerContainer.append(widgets.Label(label="Player"))
        # self.add_child(self.playerContainer)


class Media(widgets.Box):
    def __init__(self):
        super().__init__(
            vertical=False,
            setup=lambda self: mpris.connect(
                "player_added", lambda x, player: self.__add_player(player)
            ),
            css_classes=["rec-unset"],
        )

    def __add_player(self, obj: MprisPlayer) -> None:
        player = Player(obj)
        self.append(player)
        player.set_reveal_child(True)
