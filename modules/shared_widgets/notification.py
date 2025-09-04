import os
import tempfile
from ignis import widgets
from ignis.services.notifications import Notification
from PIL import Image

from user_options import user_options


def crop_to_square(image_path: str) -> str:
    """
    Crop an image to square aspect ratio and return the path to the cropped image.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # If already square, return original
            if width == height:
                return image_path
            
            # Calculate crop box for center square
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size
            
            # Crop to square
            cropped = img.crop((left, top, right, bottom))
            
            # Save to temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
            os.close(temp_fd)
            cropped.save(temp_path, 'PNG')
            
            return temp_path
    except Exception:
        # If cropping fails, return original path
        return image_path


class CroppedPicture(widgets.Picture):
    """Picture widget that automatically crops images to square aspect ratio."""
    
    def __init__(self, image=None, **kwargs):
        if image and isinstance(image, str):
            image = crop_to_square(image)
        super().__init__(image=image, **kwargs)


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
                            child=CroppedPicture(
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
                        CroppedPicture(
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
