from math import e, log

from ignis import utils, widgets
from ignis.services.audio import AudioService
from ignis.services.backlight import BacklightService
from ignis.variable import Variable
from ignis.window_manager import WindowManager

from ..shared_widgets import Corner

window_manager = WindowManager.get_default()


class OsdWindow(widgets.RevealerWindow):
    def __init__(self, state: dict, monitor_id: int = 0):
        self.state = state

        # Create percentage label
        percentage_label = widgets.Label(
            label=state["value"].bind("value", lambda v: f"{int(v * 100)}%"),
            css_classes=["osd-percentage"],
        )

        # Create icon
        icon = widgets.Icon(
            image=state["icon"].bind("value"),
            halign="center",
            valign="center",
            hexpand=True,
            vexpand=True,
            pixel_size=28,
            css_classes=["osd-icon"],
        )

        # Create scale/slider
        scale = widgets.Scale(
            on_change=lambda x: state["change"](x),
            min=0,
            max=1,
            step=0.05,
            css_classes=["osd-scale"],
            value=state["value"].bind("value"),
            vertical=True,
            inverted=True,
        )
        # Create main content box
        content = widgets.Box(
            vertical=True,
            spacing=8,
            css_classes=["osd-box"],
            child=[
                widgets.Box(
                    hexpand=True,
                    vexpand=True,
                    css_classes=["osd-icon-box"],
                    child=[icon],
                ),
                widgets.Box(
                    vertical=True,
                    child=[scale, percentage_label],
                    css_classes=["osd-slider-container"],
                ),
            ],
            # css_classes=["osd-content", state["name"]],
        )

        # Create revealer with content - start hidden
        self.content_revealer = widgets.Revealer(
            transition_type="slide_left",
            child=widgets.Box(
                vertical=True,
                child=[
                    widgets.Box(
                        css_classes=["osd-corner-up"],
                        child=[Corner(orientation="bottom-right", size=(40, 40))],
                    ),
                    content,
                    widgets.Box(
                        css_classes=["osd-corner-down"],
                        child=[Corner(orientation="top-right", size=(40, 40))],
                    ),
                ],
            ),
            transition_duration=300,
            reveal_child=False,  # Start hidden
        )

        # Bind visibility changes to trigger animation
        state["visible"].connect("notify::value", self._on_visibility_change)

        # Create click-to-dismiss buttons
        start_dismiss_button = widgets.Button(
            vexpand=True,
            hexpand=True,
            css_classes=["osd-dismiss"],
            on_click=lambda x: self._hide_osd(),
        )

        end_dismiss_button = widgets.Button(
            vexpand=True,
            hexpand=True,
            css_classes=["osd-dismiss"],
            on_click=lambda x: self._hide_osd(),
        )

        super().__init__(
            visible=False,  # Start hidden
            popup=True,
            kb_mode="none",
            layer="overlay",
            css_classes=["osd-window"],
            anchor=["top", "bottom", "right"],
            namespace=f"ignis_OSD_{state['name']}_{monitor_id}",
            child=widgets.CenterBox(
                hexpand=True,
                halign="fill",
                vexpand=True,
                vertical=True,
                start_widget=start_dismiss_button,
                center_widget=widgets.Box(
                    vertical=True,
                    valign="center",
                    halign="end",
                    child=[self.content_revealer],
                ),
                end_widget=end_dismiss_button,
            ),
            revealer=self.content_revealer,
        )

    def _on_visibility_change(self, variable, param):
        if variable.value:
            # Show window first, then animate revealer
            self.set_visible(True)
            utils.Timeout(50, lambda: self.content_revealer.set_reveal_child(True))
        else:
            # Hide revealer first, then hide window
            self.content_revealer.set_reveal_child(False)
            utils.Timeout(350, lambda: self.set_visible(False))

    def _hide_osd(self):
        self.state["visible"].value = False


class Osd:
    def __init__(self, monitor_id: int = 0):
        self.service_inits()
        self.monitor_id = monitor_id

        # Backlight
        self.brightness_multiplier = 9
        self.bl_state = {
            "name": "BL",
            "visible": Variable(value=False),
            "icon": Variable(value=""),
            "value": Variable(value=0.5),
            "change": lambda x: setattr(
                self.backlight,
                "brightness",
                log(1 + x.value * self.brightness_multiplier, e)
                / log(1 + self.brightness_multiplier, e)
                * self.backlight.max_brightness,
            ),
        }
        self.backlight.connect(
            "notify::brightness",
            lambda x, y: self.brightness_change(),
        )

        # Volume
        self.vol_state = {
            "name": "VOL",
            "visible": Variable(value=False),
            "icon": Variable(value=""),
            "value": Variable(value=0.5),
            "change": lambda x: setattr(
                self.audio.speaker,
                "volume",
                x.value * 100,
            ),
        }
        self.audio.speaker.connect(
            "notify::volume",
            lambda x, u: self.volume_change(x.volume / 100, x.is_muted),
        )
        self.audio.speaker.connect(
            "notify::is-muted",
            lambda x, u: self.volume_change(x.volume / 100, x.is_muted),
        )

        self.osd_windows = {}
        self.popup(self.bl_state)
        self.popup(self.vol_state)

    def service_inits(self):
        self.audio = AudioService.get_default()
        self.backlight = BacklightService.get_default()

    def volume_change(self, volume, muted):
        # Close brightness OSD if visible
        if self.bl_state["visible"].value:
            self.bl_state["visible"].value = False

        volume *= 100
        if volume <= 0 or type(volume) is not float or muted:
            self.vol_state["icon"].value = "audio-volume-muted-symbolic"
        elif volume > 0 and volume <= 33:
            self.vol_state["icon"].value = "audio-volume-low-symbolic"
        elif volume > 33 and volume <= 66:
            self.vol_state["icon"].value = "audio-volume-medium-symbolic"
        elif volume > 66 and volume <= 100:
            self.vol_state["icon"].value = "audio-volume-high-symbolic"
        elif volume > 100:
            self.vol_state["icon"].value = "audio-volume-overamplified-symbolic"
        volume /= 100
        self.vol_state["visible"].value = True
        self.vol_state["value"].value = volume
        self.vol_popup_debounce()

    def brightness_change(self):
        # Close volume OSD if visible
        if self.vol_state["visible"].value:
            self.vol_state["visible"].value = False

        brightness_level = self.backlight.brightness / self.backlight.max_brightness
        if brightness_level <= 0.25:
            self.bl_state["icon"].value = "display-brightness-low-symbolic"
        elif brightness_level <= 0.5:
            self.bl_state["icon"].value = "display-brightness-medium-symbolic"
        elif brightness_level <= 0.75:
            self.bl_state["icon"].value = "display-brightness-high-symbolic"
        else:
            self.bl_state["icon"].value = "display-brightness-symbolic"

        self.bl_state["visible"].value = True
        self.bl_state["value"].value = brightness_level
        self.bl_popup_debounce()

    @utils.debounce(3000)
    def bl_popup_debounce(self):
        self.bl_state["visible"].value = False

    @utils.debounce(3000)
    def vol_popup_debounce(self):
        self.vol_state["visible"].value = False

    def popup(self, state: dict):
        osd_window = OsdWindow(state, self.monitor_id)
        self.osd_windows[state["name"]] = osd_window
