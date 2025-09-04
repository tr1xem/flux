import calendar
import datetime
from gi.repository import GLib

from ignis import utils, widgets
from ignis.variable import Variable

from user_options import user_options


class CalendarWidget(widgets.Box):
    def __init__(self):
        super().__init__(
            css_classes=["calendar-widget"],
            vertical=True,
            spacing=4,
        )
        
        self._current_date = datetime.datetime.now()
        self._setup_calendar()

    def _setup_calendar(self):
        # Remove all children
        child = self.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.remove(child)
            child = next_child
        
        # Month and year header
        month_year = widgets.Box(
            css_classes=["calendar-header"],
            halign="center",
            child=[
                widgets.Button(
                    css_classes=["calendar-nav"],
                    child=widgets.Icon(image="go-previous-symbolic"),
                    on_click=lambda x: self._change_month(-1),
                ),
                widgets.Label(
                    label=self._current_date.strftime("%b %Y"),
                    css_classes=["calendar-month-year"],
                    hexpand=True,
                    halign="center",
                ),
                widgets.Button(
                    css_classes=["calendar-nav"],
                    child=widgets.Icon(image="go-next-symbolic"),
                    on_click=lambda x: self._change_month(1),
                ),
            ],
        )
        self.append(month_year)

        # Days of week header (single letters)
        days_header = widgets.Box(
            css_classes=["calendar-days-header"],
            spacing=2,
        )
        
        # Single letter day names
        day_names = ["S", "M", "T", "W", "T", "F", "S"]
        for i, day in enumerate(day_names):
            css_classes = ["calendar-day-header"]
            # Add Sunday styling (first column only)
            if i == 0:
                css_classes.append("calendar-sunday")
            
            day_label = widgets.Label(
                label=day,
                css_classes=css_classes,
                halign="center",
                hexpand=True,
            )
            days_header.append(day_label)
        
        self.append(days_header)

        # Calendar grid
        calendar.setfirstweekday(calendar.SUNDAY)  # Set Sunday as first day of week
        cal = calendar.monthcalendar(self._current_date.year, self._current_date.month)
        today = datetime.datetime.now()
        
        for week in cal:
            week_box = widgets.Box(spacing=2)
            for day_index, day in enumerate(week):
                if day == 0:
                    # Empty cell for days from other months
                    day_button = widgets.Label(
                        label="",
                        css_classes=["calendar-day", "calendar-day-empty"],
                        hexpand=True,
                        halign="center",
                    )
                else:
                    # Check if this is today
                    is_today = (
                        day == today.day
                        and self._current_date.month == today.month
                        and self._current_date.year == today.year
                    )
                    
                    css_classes = ["calendar-day"]
                    if is_today:
                        css_classes.append("calendar-today")
                    
                    # Add Sunday styling (first column only, since we start with Sunday)
                    if day_index == 0:
                        css_classes.append("calendar-sunday")
                    
                    day_button = widgets.Label(
                        label=str(day),
                        css_classes=css_classes,
                        hexpand=True,
                        halign="center",
                    )
                
                week_box.append(day_button)
            self.append(week_box)

    def _change_month(self, delta):
        if delta > 0:
            # Next month
            if self._current_date.month == 12:
                self._current_date = self._current_date.replace(year=self._current_date.year + 1, month=1)
            else:
                self._current_date = self._current_date.replace(month=self._current_date.month + 1)
        else:
            # Previous month
            if self._current_date.month == 1:
                self._current_date = self._current_date.replace(year=self._current_date.year - 1, month=12)
            else:
                self._current_date = self._current_date.replace(month=self._current_date.month - 1)
        
        self._setup_calendar()


class CalendarPopup(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        self.monitor_id = monitor_id
        self.revealer = widgets.Revealer(
            css_classes=["calendar-revealer"],
            transition_type="slide_down",
            transition_duration=300,
            reveal_child=False,
            child=CalendarWidget(),
        )
        
        super().__init__(
            namespace=f"ignis_CALENDAR_{monitor_id}",
            monitor=monitor_id,
            css_classes=["calendar-popup"],
            anchor=["top", "left", "bottom", "right"],
            exclusivity="normal",
            visible=False,
            child=widgets.Box(
                vertical=True,
                hexpand=True,
                vexpand=True,
                child=[
                    widgets.CenterBox(
                        hexpand=True,
                        start_widget=widgets.Button(
                            hexpand=True,
                            css_classes=["unset"],
                            on_click=lambda x: self.close(),
                        ),
                        center_widget=widgets.Box(
                            halign="end",
                            child=[self.revealer]
                        ),
                        end_widget=widgets.Button(
                            hexpand=True,
                            css_classes=["unset"],
                            on_click=lambda x: self.close(),
                        ),
                    ),
                    widgets.Button(
                        vexpand=True,
                        hexpand=True,
                        css_classes=["unset"],
                        on_click=lambda x: self.close(),
                    ),
                ],
            ),
        )

    def toggle(self):
        if not self.visible:
            self.visible = True
            self.revealer.reveal_child = True
        else:
            self.close()
    
    def close(self):
        self.revealer.reveal_child = False
        # Hide window after animation completes
        GLib.timeout_add(350, lambda: setattr(self, 'visible', False) or False)


class Datetime(widgets.Box):
    def __init__(self, monitor_id: int = 0):
        super().__init__(
            css_classes=["datetime"],
        )
        
        self.calendar_popup = CalendarPopup(monitor_id)
        
        self.current_time = Variable(
            value=utils.Poll(
                1000,
                lambda x: datetime.datetime.now().strftime("<b>%I:%M</b> • %A, %-d %b"),
            ).bind("output")
        )
        
        self.time_button = widgets.Button(
            css_classes=["datetime-button"],
            on_click=lambda x: self.calendar_popup.toggle(),
            child=widgets.Label(
                label=self.current_time.bind("value"),
                use_markup=True,
            ),
        )
        
        self.append(self.time_button)