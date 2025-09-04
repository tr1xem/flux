from ignis import widgets
from ignis.services.applications import ApplicationsService
from ignis.services.hyprland import HyprlandService

hyprland = HyprlandService.get_default()
applications = ApplicationsService.get_default()


def _truncate(text: str, size: int) -> str:
    return text if len(text) <= size else text[:size] + "…"


def find_app_by_class(win_class: str):
    """
    Find application by window class using various search strategies
    """
    if not win_class:
        return None

    search_terms = [
        win_class,
        win_class.lower(),
        win_class.replace("-", " "),
        win_class.replace("_", " "),
        win_class.split(".")[-1] if "." in win_class else win_class,
    ]

    for search_term in search_terms:
        results = ApplicationsService.search(applications.apps, search_term)
        if results:
            return results[0]

    return None


def get_app_info(win_title: str, win_class: str):
    """
    Get window app info using Applications service for dynamic app detection
    Returns tuple of (icon_name, display_text)
    """

    trunc = True
    trunc_size = 32

    if not win_class or win_class == "":
        return ("desktop", "Desktop")

    app = find_app_by_class(win_class)

    if app and app.icon and app.name:
        return (app.icon, app.name)
    elif app and app.name:
        return ("application-x-executable", app.name)

    display_text = win_title if win_title else win_class
    display_text = _truncate(display_text, trunc_size) if trunc else display_text

    return ("application-x-executable", display_text)


class WindowTitle(widgets.Box):
    def __init__(self):
        super().__init__(
            vexpand=True,
            hexpand=True,
            spacing=8,
            valign="center",
            css_classes=["container"],
            child=[
                widgets.Icon(
                    image=hyprland.bind(
                        "active_window",
                        transform=lambda window: get_app_info(
                            window.initial_title, window.initial_class
                        )[0],
                    ),
                    pixel_size=20,
                ),
                widgets.Label(
                    label=hyprland.bind(
                        "active_window",
                        transform=lambda window: get_app_info(
                            window.initial_title, window.initial_class
                        )[1],
                    ),
                    css_classes=["title-text"],
                ),
            ],
        )

