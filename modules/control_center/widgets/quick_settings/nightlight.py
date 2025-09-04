import asyncio

from ignis.utils import exec_sh_async

from ...qs_button import QSButton


class NightModeButton(QSButton):
    __gtype_name__ = "NightModeButton"

    def __init__(self):
        super().__init__(
            label="Night Mode",
            icon_name="stock_weather-night-clear",
            on_activate=lambda x: asyncio.create_task(self.activate_night_mode()),
            on_deactivate=lambda x: asyncio.create_task(self.deactivate_night_mode()),
            active=False,
        )

    async def activate_night_mode(self):
        self.set_active(True)
        await exec_sh_async("hyprsunset --temperature 4000")

    async def deactivate_night_mode(self):
        self.set_active(False)
        await exec_sh_async("pkill hyprsunset")
