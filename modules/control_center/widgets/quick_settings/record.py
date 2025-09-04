import asyncio

from ignis import widgets
from ignis.exceptions import RecorderPortalCaptureCanceled
from ignis.services.recorder import RecorderConfig, RecorderService

from ...menu import Menu
from ...qs_button import QSButton

AUDIO_DEVICES = {
    "Internal audio": "default_output",
    "Microphone": "default_input",
    "Both sources": "default_output|default_input",
}

SOURCE_OPTIONS = {
    "Screen": "screen",
    "Portal": "portal",
    "Focused window": "focused",
    "Region": "region",
}

QUALITY_OPTIONS = ["medium", "high", "very_high", "ultra"]
VIDEO_CODECS = ["auto", "h264", "hevc", "av1"]

recorder = RecorderService.get_default()


class RecordMenu(Menu):
    def __init__(self):
        self._audio_switch = widgets.Switch(halign="end", hexpand=True, valign="center")
        self._audio_dropdown = widgets.DropDown(
            items=["Internal audio", "Microphone", "Both sources"],
            css_classes=["record-dropdown"],
        )

        # Audio source box (conditionally visible)
        self._audio_source_box = widgets.Box(
            style="margin-bottom: 0.75rem;",
            visible=False,  # Initially hidden
            child=[
                widgets.Icon(
                    image="microphone-sensitivity-medium-symbolic",
                    pixel_size=20,
                    style="margin-right: 0.75rem;",
                ),
                widgets.Label(
                    label="Audio source",
                    style="font-size: 1.1rem;",
                    halign="start",
                    hexpand=True,
                ),
                self._audio_dropdown,
            ],
        )

        # Bind audio switch to control visibility of audio source
        self._audio_switch.bind("active", self._on_audio_toggle)

        # New controls
        self._source_dropdown = widgets.DropDown(
            items=list(SOURCE_OPTIONS.keys()),
            selected="Portal",
            css_classes=["record-dropdown"],
        )

        self._quality_dropdown = widgets.DropDown(
            items=QUALITY_OPTIONS,
            selected="high",
            css_classes=["record-dropdown"],
        )

        self._codec_dropdown = widgets.DropDown(
            items=VIDEO_CODECS,
            selected="auto",
            css_classes=["record-dropdown"],
        )

        self._cursor_switch = widgets.Switch(
            halign="end", hexpand=True, valign="center", active=True
        )

        super().__init__(
            name="recording",
            child=[
                widgets.Icon(
                    image="media-record-symbolic",
                    pixel_size=36,
                    halign="center",
                    css_classes=["record-icon"],
                ),
                widgets.Label(
                    label="Recording Settings",
                    halign="center",
                    style="font-size: 1.2rem; margin-bottom: 1rem;",
                ),
                # Source selection
                widgets.Box(
                    style="margin-bottom: 0.75rem;",
                    child=[
                        widgets.Icon(
                            image="video-display-symbolic",
                            pixel_size=20,
                            style="margin-right: 0.75rem;",
                        ),
                        widgets.Label(
                            label="Source",
                            style="font-size: 1.1rem;",
                            halign="start",
                            hexpand=True,
                        ),
                        self._source_dropdown,
                    ],
                ),
                # Quality selection
                widgets.Box(
                    style="margin-bottom: 0.75rem;",
                    child=[
                        widgets.Icon(
                            image="preferences-system-symbolic",
                            pixel_size=20,
                            style="margin-right: 0.75rem;",
                        ),
                        widgets.Label(
                            label="Quality",
                            style="font-size: 1.1rem;",
                            halign="start",
                            hexpand=True,
                        ),
                        self._quality_dropdown,
                    ],
                ),
                # Video codec selection
                widgets.Box(
                    style="margin-bottom: 0.75rem;",
                    child=[
                        widgets.Icon(
                            image="video-x-generic-symbolic",
                            pixel_size=20,
                            style="margin-right: 0.75rem;",
                        ),
                        widgets.Label(
                            label="Codec",
                            style="font-size: 1.1rem;",
                            halign="start",
                            hexpand=True,
                        ),
                        self._codec_dropdown,
                    ],
                ),
                # Cursor recording
                widgets.Box(
                    style="margin-bottom: 0.75rem;",
                    child=[
                        widgets.Icon(
                            image="input-mouse-symbolic",
                            pixel_size=20,
                            style="margin-right: 0.75rem;",
                        ),
                        widgets.Label(
                            label="Record cursor",
                            style="font-size: 1.1rem;",
                            halign="start",
                            hexpand=True,
                        ),
                        self._cursor_switch,
                    ],
                ),
                # Record audio toggle
                widgets.Box(
                    style="margin-bottom: 0.75rem;",
                    child=[
                        widgets.Icon(
                            image="audio-volume-high-symbolic",
                            pixel_size=20,
                            style="margin-right: 0.75rem;",
                        ),
                        widgets.Label(
                            label="Record audio",
                            style="font-size: 1.1rem;",
                            halign="start",
                            hexpand=True,
                        ),
                        self._audio_switch,
                    ],
                ),
                # Audio source selection (only when audio recording is enabled)
                self._audio_source_box,
                # Control buttons
                widgets.Box(
                    style="margin-top: 1rem;",
                    child=[
                        widgets.Button(
                            child=widgets.Label(label="Cancel"),
                            css_classes=["record-cancel-button", "unset"],
                            hexpand=True,
                            on_click=lambda x: self.set_reveal_child(False),  # type: ignore
                        ),
                        widgets.Button(
                            child=widgets.Label(label="Start recording"),
                            css_classes=["record-start-button", "unset"],
                            hexpand=True,
                            style="margin-left: 0.5rem;",
                            on_click=lambda x: asyncio.create_task(
                                self.__start_recording()
                            ),
                        ),
                    ],
                ),
            ],
        )

    def _on_audio_toggle(self, switch, *args):
        """Toggle visibility of audio source dropdown based on audio switch"""
        self._audio_source_box.visible = switch.active

    async def __start_recording(self) -> None:
        self.set_reveal_child(False)

        config = RecorderConfig.new_from_options()

        # Apply source selection
        source_name = self._source_dropdown.selected
        config.source = SOURCE_OPTIONS.get(source_name, "portal")

        # Apply quality selection
        config.quality = self._quality_dropdown.selected

        # Apply codec selection
        config.video_codec = self._codec_dropdown.selected

        # Apply cursor setting
        config.cursor = "yes" if self._cursor_switch.active else "no"

        # Apply audio settings
        if self._audio_switch.active:
            config.audio_devices = [
                AUDIO_DEVICES.get(self._audio_dropdown.selected, "")
            ]

        try:
            await recorder.start_recording(config=config)
        except RecorderPortalCaptureCanceled:
            pass


class RecordControlMenu(Menu):
    """Menu shown when recording is active"""

    def __init__(self):
        super().__init__(
            name="recording-controls",
            child=[
                widgets.Icon(
                    image="media-playback-pause-symbolic",
                    pixel_size=36,
                    halign="center",
                    css_classes=["record-icon"],
                ),
                widgets.Label(
                    label="Recording in progress...",
                    halign="center",
                    style="font-size: 1.2rem; margin-bottom: 1rem;",
                ),
                # Control buttons
                widgets.Box(
                    child=[
                        widgets.Button(
                            child=widgets.Box(
                                child=[
                                    widgets.Icon(
                                        image="media-playback-pause-symbolic",
                                        pixel_size=16,
                                        style="margin-right: 0.5rem;",
                                    ),
                                    widgets.Label(label="Pause"),
                                ]
                            ),
                            css_classes=["record-pause-button", "unset"],
                            hexpand=True,
                            on_click=self._toggle_pause,
                        ),
                        widgets.Button(
                            child=widgets.Box(
                                child=[
                                    widgets.Icon(
                                        image="media-playback-stop-symbolic",
                                        pixel_size=16,
                                        style="margin-right: 0.5rem;",
                                    ),
                                    widgets.Label(label="Stop"),
                                ]
                            ),
                            css_classes=["record-stop-button", "unset"],
                            hexpand=True,
                            style="margin-left: 0.5rem;",
                            on_click=lambda x: recorder.stop_recording(),
                        ),
                    ],
                ),
            ],
        )

    def _toggle_pause(self, *args):
        """Toggle pause/resume recording"""
        if recorder.is_paused:
            recorder.continue_recording()
        else:
            recorder.pause_recording()


class RecordButton(QSButton):
    def __init__(self):
        self.record_menu = RecordMenu()
        self.control_menu = RecordControlMenu()
        self._current_menu = self.record_menu

        super().__init__(
            label="Record",
            icon_name="media-record-symbolic",
            on_activate=self._on_activate,
            on_deactivate=lambda x: recorder.stop_recording(),
            active=recorder.bind("active"),
            menu=self.record_menu,
        )

        # Bind to recorder state to update menu and label
        recorder.bind("active", self._update_state)

    def _update_state(self, *args):
        """Update button state based on recorder status"""
        if recorder.active:
            self.label = "Recording..."
            self._current_menu = self.control_menu
        else:
            self.label = "Record"
            self._current_menu = self.record_menu

    def _on_activate(self, *args):
        """Handle button activation"""
        if recorder.active:
            # If recording is active, show control menu
            self.control_menu.toggle()
        else:
            # If not recording, show settings menu
            self.record_menu.toggle()
