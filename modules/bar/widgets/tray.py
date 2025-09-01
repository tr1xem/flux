from ignis import widgets
from ignis.services.system_tray import SystemTrayItem, SystemTrayService

system_tray = SystemTrayService.get_default()


def tray_item(item: SystemTrayItem) -> widgets.Button:
    if item.menu:
        menu = item.menu.copy()
    else:
        menu = None

    return widgets.Button(
        child=widgets.Box(
            child=[
                widgets.Icon(image=item.bind("icon"), pixel_size=22),
                menu,
            ]
        ),
        setup=lambda self: item.connect("removed", lambda x: self.unparent()),
        tooltip_text=item.bind("tooltip"),
        on_click=lambda x: menu.popup() if menu else None,
        on_right_click=lambda x: menu.popup() if menu else None,
        css_classes=["tray-item"],
    )


class Tray(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["containers"],
            spacing=5,
            setup=lambda self: system_tray.connect(
                "added", lambda x, item: self.append(tray_item(item))
            ),
        )
