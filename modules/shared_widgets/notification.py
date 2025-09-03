from ignis import widgets
from ignis.services.notifications import Notification

from user_options import user_options


class ScreenshotLayout(widgets.Box):
    def __init__(self, notification: Notification) -> None:
        super().__init__(
            vertical=True,
            hexpand=True,
            css_classes=["unset"],
            child=[
                widgets.Box(
                    css_classes=["unset"],
                    vertical=True,
                    child=[
                        widgets.Overlay(
                            child=widgets.Picture(
                                image=notification.icon,
                                css_classes=["notification-icon"],
                                # content_fit="contain",
                                width=1920 // 7,
                                height=1080 // 7,
                            ),
                            overlays=[
                                widgets.Button(
                                    child=widgets.Icon(
                                        image="window-close-symbolic",
                                        pixel_size=20,
                                    ),
                                    halign="end",
                                    valign="start",
                                    hexpand=True,
                                    css_classes=["notification-close"],
                                    on_click=lambda x: notification.close(),
                                ),
                            ],
                        ),
                        widgets.Box(
                            vertical=True,
                            hexpand=True,
                            halign="center",
                            style="margin-left: 0.75rem;",
                            child=[
                                widgets.Label(
                                    ellipsize="end",
                                    label=notification.summary,
                                    halign="center",
                                    visible=notification.summary != "",
                                    css_classes=["notification-summary"],
                                ),
                                widgets.Label(
                                    label=notification.body,
                                    ellipsize="end",
                                    halign="center",
                                    css_classes=["notification-body"],
                                    visible=notification.body != "",
                                ),
                            ],
                        ),
                        widgets.Box(
                            child=[
                                widgets.Button(
                                    child=widgets.Label(label=action.label),
                                    on_click=lambda x, action=action: action.invoke(),
                                    css_classes=["notification-action"],
                                )
                                for action in notification.actions
                            ],
                            homogeneous=True,
                            style="margin-top: 0.75rem;"
                            if notification.actions
                            else "",
                            spacing=10,
                        ),
                    ],
                ),
            ],
        )


# class ScreenshotLayout(widgets.Box):
#     def __init__(self, notification: Notification) -> None:
#         super().__init__(
#             vertical=True,
#             css_classes=["unset"],
#             hexpand=True,
#             child=[
#                 widgets.Box(
#                     child=[
#                         widgets.Picture(
#                             image=notification.icon,
#                             content_fit="cover",
#                             width=1920 // 7,
#                             height=1080 // 7,
#                             style="border-radius: 1rem; ",
#                         ),
#                         widgets.Button(
#                             child=widgets.Icon(
#                                 image="window-close-symbolic", pixel_size=20
#                             ),
#                             halign="end",
#                             valign="start",
#                             hexpand=True,
#                             css_classes=["notification-close"],
#                             on_click=lambda x: notification.close(),
#                         ),
#                     ],
#                 ),
#                 widgets.Label(
#                     label="Screenshot saved",
#                     css_classes=["notification-screenshot-label"],
#                 ),
#                 widgets.Box(
#                     homogeneous=True,
#                     style="margin-top: 0.75rem;",
#                     spacing=10,
#                     child=[
#                         widgets.Button(
#                             child=widgets.Label(label="Open"),
#                             css_classes=["notification-action"],
#                             on_click=lambda x: asyncio.create_task(
#                                 utils.exec_sh_async(f"xdg-open {notification.icon}")
#                             ),
#                         ),
#                         widgets.Button(
#                             child=widgets.Label(label="Close"),
#                             css_classes=["notification-action"],
#                             on_click=lambda x: notification.close(),
#                         ),
#                     ],
#                 ),
#             ],
#         )
#


class NormalLayout(widgets.Box):
    def __init__(self, notification: Notification) -> None:
        super().__init__(
            vertical=True,
            hexpand=True,
            css_classes=["unset"],
            child=[
                widgets.Box(
                    child=[
                        widgets.Picture(
                            css_classes=["notification-icon"],
                            image=notification.icon
                            if notification.icon
                            else "dialog-information-symbolic",
                            height=42,
                            width=42,
                            halign="start",
                            valign="start",
                        ),
                        widgets.Box(
                            vertical=True,
                            style="margin-left: 0.75rem;",
                            child=[
                                widgets.Label(
                                    ellipsize="end",
                                    label=notification.summary,
                                    halign="start",
                                    visible=notification.summary != "",
                                    css_classes=["notification-summary"],
                                ),
                                widgets.Label(
                                    label=notification.body,
                                    ellipsize="end",
                                    halign="start",
                                    css_classes=["notification-body"],
                                    visible=notification.body != "",
                                ),
                            ],
                        ),
                        widgets.Button(
                            child=widgets.Icon(
                                image="window-close-symbolic", pixel_size=20
                            ),
                            halign="end",
                            valign="start",
                            hexpand=True,
                            css_classes=["notification-close"],
                            on_click=lambda x: notification.close(),
                        ),
                    ],
                ),
                widgets.Box(
                    child=[
                        widgets.Button(
                            child=widgets.Label(label=action.label),
                            on_click=lambda x, action=action: action.invoke(),
                            css_classes=["notification-action"],
                        )
                        for action in notification.actions
                    ],
                    homogeneous=True,
                    style="margin-top: 0.75rem;" if notification.actions else "",
                    spacing=10,
                ),
            ],
        )


class NotificationWidget(widgets.Box):
    def __init__(self, notification: Notification) -> None:
        layout: NormalLayout | ScreenshotLayout

        if notification.app_name in user_options.default.screenshot_app:
            layout = ScreenshotLayout(notification)
        else:
            layout = NormalLayout(notification)

        super().__init__(
            css_classes=["notification"],
            child=[layout],
        )
