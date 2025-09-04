import os
import sys

# Add the project root to Python path to import from services
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from services.idle_inhibitor import IdleInhibitorService

from ...qs_button import QSButton

idle_inhibitor = IdleInhibitorService.get_default()


class IdleInhibitorButton(QSButton):
    __gtype_name__ = "IdleInhibitorButton"

    def __init__(self):
        def get_label(is_inhibiting: bool) -> str:
            return "Keep Awake" if is_inhibiting else "Sleep Mode"

        def get_icon(is_inhibiting: bool) -> str:
            return (
                "preferences-system-privacy-symbolic"
                if is_inhibiting
                else "night-light-symbolic"
            )

        def toggle_inhibitor(x) -> None:
            idle_inhibitor.toggle()

        super().__init__(
            label=idle_inhibitor.bind("is_inhibiting", get_label),
            icon_name="system-suspend-uninhibited",
            on_activate=toggle_inhibitor,
            on_deactivate=toggle_inhibitor,
            active=idle_inhibitor.bind("is_inhibiting"),
            visible=idle_inhibitor.bind("available"),
        )

