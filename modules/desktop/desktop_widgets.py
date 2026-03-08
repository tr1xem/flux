from ignis import widgets, utils
import os
import datetime
from ignis.variable import Variable
from ignis.widgets import Fixed
from user_options import user_options


class TimeWidget(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        self.time_label = widgets.Label(css_classes=["movable-time"], use_markup=True)

        time_variable = Variable(
            value=utils.Poll(
                1000,
                lambda x: datetime.datetime.now().strftime("%I:%M"),
            ).bind("output")
        )

        self.time_label.label = time_variable.bind("value")

        self.fixed_container = Fixed(
            hexpand=True,
            vexpand=True,
            child=[
                widgets.FixedChild(
                    self.time_label,
                    user_options.time.x_position,
                    user_options.time.y_position,
                ),
            ],
            css_classes=["fixed-label"],
        )

        super().__init__(
            namespace=f"ignis_TIME_{monitor_id}",
            monitor=monitor_id,
            exclusivity="ignore",
            anchor=["top", "right", "bottom", "left"],
            css_classes=["rec-unset"],
            layer="bottom",
            child=self.fixed_container,
        )

        # Connect signals for this widget only
        user_options.time.connect("changed", lambda *_: self.update_style())
        user_options.time.connect_option("x_position", lambda: self.move_widget())
        user_options.time.connect_option("y_position", lambda: self.move_widget())
        user_options.desktop_widgets.connect_option(
            "time_enabled", lambda: self.update_visibility()
        )

        # Set initial state
        self.update_style()
        self.update_visibility()

    def move_widget(self):
        self.fixed_container.move(
            self.time_label,
            user_options.time.x_position,
            user_options.time.y_position,
        )

    def update_visibility(self):
        enabled = user_options.desktop_widgets.time_enabled
        self.set_visible(enabled)

    def update_style(self):
        if user_options.time.use_custom_color:
            color = user_options.time.color
            font_size = user_options.time.font_size
            self.time_label.set_style(f"color: {color}; font-size: {font_size}px;")
        else:
            font_size = user_options.time.font_size
            self.time_label.set_style(f"font-size: {font_size}px;")


class DateWidget(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        self.date_label = widgets.Label(css_classes=["movable-date"], use_markup=True)

        date_variable = Variable(
            value=utils.Poll(
                1000,
                lambda x: datetime.datetime.now().strftime("%A %-d, %b"),
            ).bind("output")
        )

        self.date_label.label = date_variable.bind("value")

        self.fixed_container = Fixed(
            hexpand=True,
            vexpand=True,
            child=[
                widgets.FixedChild(
                    self.date_label,
                    user_options.date.x_position,
                    user_options.date.y_position,
                ),
            ],
            css_classes=["fixed-label"],
        )

        super().__init__(
            namespace=f"ignis_DATE_{monitor_id}",
            monitor=monitor_id,
            exclusivity="ignore",
            anchor=["top", "right", "bottom", "left"],
            css_classes=["rec-unset"],
            layer="bottom",
            child=self.fixed_container,
        )

        # Connect signals for this widget only
        user_options.date.connect("changed", lambda *_: self.update_style())
        user_options.date.connect_option("x_position", lambda: self.move_widget())
        user_options.date.connect_option("y_position", lambda: self.move_widget())
        user_options.desktop_widgets.connect_option(
            "date_enabled", lambda: self.update_visibility()
        )

        # Set initial state
        self.update_style()
        self.update_visibility()

    def move_widget(self):
        self.fixed_container.move(
            self.date_label,
            user_options.date.x_position,
            user_options.date.y_position,
        )

    def update_visibility(self):
        enabled = user_options.desktop_widgets.date_enabled
        self.set_visible(enabled)

    def update_style(self):
        if user_options.date.use_custom_color:
            color = user_options.date.color
            font_size = user_options.date.font_size
            self.date_label.set_style(f"color: {color}; font-size: {font_size}px;")
        else:
            font_size = user_options.date.font_size
            self.date_label.set_style(f"font-size: {font_size}px;")


class Depth(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        self.depth_picture = widgets.Picture(
            image=user_options.wallpaper.bind("depth_wall"),
            hexpand=True,
            vexpand=True,
            visible=user_options.wallpaper.bind(
                "depth_wall",
                lambda x: (
                    True
                    if user_options.rembg.enabled
                    and os.path.exists(x)
                    and user_options.wallpaper.depth_processing
                    else False
                ),
            ),
            content_fit="cover",
            css_classes=["depth-wallpaper"],
        )

        super().__init__(
            namespace=f"ignis_DESKTOP_{monitor_id}",
            monitor=monitor_id,
            css_classes=["desktop"],
            anchor=["top", "right", "bottom", "left"],
            layer="bottom",
            exclusivity="ignore",
            child=self.depth_picture,
        )

        def update_visibility():
            enabled = getattr(user_options.rembg, "enabled", True)
            self.set_visible(enabled)

        # Connect to rembg options
        if hasattr(user_options, "rembg"):
            user_options.rembg.connect_option("enabled", lambda: update_visibility())
        update_visibility()


class CountdownBox(widgets.Box):
    def __init__(
        self,
        eventName,
        eventTime: datetime.datetime,
        logoPath: str = "~/.config/ignis/assets/logo.png",
        monitor_id: int = 0,
    ):
        self.logo = widgets.Picture(
            image=os.path.abspath(os.path.expanduser(logoPath)),
            css_classes=["countdown-box-logo"],
            height=35,
            width=35,
        )

        self.topBox = widgets.Box(
            name="topBox",
            css_classes=["topBox"],
            hexpand=True,
            child=[
                widgets.Label(label="Days Left", css_classes=["countdown-box-title"]),
                widgets.Box(
                    hexpand=True,
                    halign="end",
                    child=[
                        self.logo,
                    ],
                ),
            ],
        )
        self.currentDate = Variable(
            value=utils.Poll(
                1000,
                lambda x: datetime.datetime.now(),
            ).bind("output")
        )

        self.daysLeft = Variable(
            value=utils.Poll(
                1000, lambda x: str((eventTime - datetime.datetime.now()).days)
            ).bind("output")
        )

        self.mainBox = widgets.Box(
            name="mainBox",
            css_classes=["mainBox"],
            vertical=True,
            halign="start",
            hexpand=True,
            vexpand=True,
            child=[
                widgets.Label(
                    label=self.daysLeft.bind("value"),
                    css_classes=["countdown-box-daysleft"],
                    halign="start",
                ),
                widgets.Label(
                    label=f"{eventName}",
                    css_classes=["countdown-box-eventname"],
                    wrap=True,
                    halign="start",
                ),
                widgets.Label(
                    label=f"{eventTime.strftime('%-d %b %Y')}",
                    css_classes=["countdown-box-eventtime"],
                    halign="start",
                ),
            ],
        )
        super().__init__(
            name=eventName,
            css_classes=["countdown-box"],
            vertical=True,
            hexpand=True,
            child=[
                self.topBox,
                self.mainBox,
            ],
        )


class CountdownWidget(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        self.countdown_box = CountdownBox(
            eventName="Jee Mains 2026",
            eventTime=datetime.datetime(2026, 4, 2),
            logoPath="~/exams/mains.png",
            monitor_id=monitor_id,
        )
        self.countdown_box_adv = CountdownBox(
            eventName="Jee Adv 2026",
            eventTime=datetime.datetime(2026, 5, 17),
            logoPath="~/exams/adv.png",
            monitor_id=monitor_id,
        )

        super().__init__(
            namespace=f"ignis_COUNTDOWN_{monitor_id}",
            monitor=monitor_id,
            anchor=["top", "left"],
            css_classes=["rec-unset", "countdown-window"],
            layer="bottom",
            child=widgets.Box(
                spacing=10, child=[self.countdown_box, self.countdown_box_adv]
            ),
            # child=self.countdown_box,
        )
