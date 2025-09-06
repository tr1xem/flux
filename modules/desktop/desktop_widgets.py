from ignis import widgets, utils
import datetime
from ignis.variable import Variable
from ..shared_widgets.fixed import Fixed, FixedChild
from user_options import user_options
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib


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
            child=[
                FixedChild(
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
            # dynamic_input_region=True,
            # kb_mode="on_demand",
            anchor=["top", "right", "bottom", "left"],
            css_classes=["rec-unset"],
            layer="bottom",
            child=self.fixed_container,
        )

        # Add drag functionality to the time label after window initialization
        self.setup_drag_and_drop()

        # Connect signals for this widget only
        user_options.time.connect("changed", lambda *_: self.update_style())
        user_options.time.connect_option("x_position", lambda: self.move_widget())
        user_options.time.connect_option("y_position", lambda: self.move_widget())
        user_options.desktop_widgets.connect_option(
            "time_enabled", lambda: self.update_visibility()
        )
        user_options.desktop_widgets.connect_option(
            "time_positioning_mode", lambda: self.update_layer()
        )

        # Set initial state
        self.update_style()
        self.update_visibility()
        self.update_layer()  # Set initial layer based on positioning mode

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

    def update_layer(self):
        positioning_mode = user_options.desktop_widgets.time_positioning_mode
        target_layer = "top" if positioning_mode else "bottom"
        print(
            f"[DEBUG] TimeWidget updating layer - time_positioning_mode: {positioning_mode}, target_layer: {target_layer}"
        )

        try:
            self.set_layer(target_layer)
            print(f"[DEBUG] TimeWidget successfully changed layer to: {target_layer}")
        except Exception as e:
            print(f"[DEBUG] TimeWidget failed to change layer to {target_layer}: {e}")

    def setup_drag_and_drop(self):
        print("[DEBUG] Setting up drag and drop for time label")

        # Method 1: Try standard drag source first
        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare)
        drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-end", self.on_drag_end)
        self.time_label.add_controller(drag_source)
        print("[DEBUG] Drag source added to time label")

        drop_target = Gtk.DropTarget.new(type=str, actions=Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        drop_target.connect("enter", self.on_drag_enter)
        drop_target.connect("leave", self.on_drag_leave)

        # Add the drop target to the window itself
        self.add_controller(drop_target)
        print("[DEBUG] Drop target added to time widget window")

    def on_drag_prepare(self, drag_source, x, y):
        print(f"[DEBUG] Time drag prepare called at position: x={x}, y={y}")

        # Store the relative position where drag started
        self.drag_start_x = x
        self.drag_start_y = y
        print(
            f"[DEBUG] Stored time drag start position: {self.drag_start_x}, {self.drag_start_y}"
        )

        # Return content provider for the drag
        try:
            data = "time_label".encode("utf-8")
            bytes_data = GLib.Bytes(data)
            content = Gdk.ContentProvider.new_for_bytes("text/plain", bytes_data)
            print("[DEBUG] Time content provider created successfully")
            return content
        except Exception as e:
            print(f"[DEBUG] Error creating time content provider: {e}")
            return None

    def on_drag_begin(self, drag_source, drag):
        print("[DEBUG] Time drag begin - drag operation started")
        # No layer switching needed - top layer already handles input events

    def on_drag_end(self, drag_source, drag, delete_data):
        print(
            f"[DEBUG] Time drag end - operation completed, delete_data: {delete_data}"
        )
        # Move back to appropriate layer based on positioning mode after drag is complete
        positioning_mode = user_options.desktop_widgets.time_positioning_mode
        target_layer = "top" if positioning_mode else "bottom"
        try:
            self.set_layer(target_layer)
            print(
                f"[DEBUG] Moved time widget to {target_layer} layer after dragging (time_positioning_mode: {positioning_mode})"
            )
        except Exception as e:
            print(f"[DEBUG] Failed to change time widget layer back: {e}")

    def on_drag_enter(self, drop_target, x, y):
        print(f"[DEBUG] Time drag enter at position: x={x}, y={y}")
        return Gdk.DragAction.MOVE

    def on_drag_leave(self, drop_target):
        self.set_layer("bottom")
        print("[DEBUG] Time drag leave - left drop zone")

    def on_drop(self, drop_target, value, x, y):
        self.set_layer("bottom")
        print(f"[DEBUG] Time drop event at position: x={x}, y={y}, value={value}")

        if value and "time_label" in str(value):
            print("[DEBUG] Valid drop detected for time_label")

            # Get current widget position
            current_x = user_options.time.x_position
            current_y = user_options.time.y_position
            print(f"[DEBUG] Current time widget position: {current_x}, {current_y}")

            # Calculate new position relative to the drag start
            new_x = int(x - self.drag_start_x)
            new_y = int(y - self.drag_start_y)
            print(
                f"[DEBUG] Calculated time new position (before bounds): {new_x}, {new_y}"
            )

            # Ensure position is within reasonable bounds
            new_x = max(0, min(new_x, 1820))
            new_y = max(0, min(new_y, 980))
            print(f"[DEBUG] Final time position (after bounds): {new_x}, {new_y}")

            # Update the position in user options
            try:
                user_options.time.set_x_position(new_x)
                user_options.time.set_y_position(new_y)
                print(
                    f"[DEBUG] Successfully updated time position to: {new_x}, {new_y}"
                )
                return True
            except Exception as e:
                print(f"[DEBUG] Error updating time position: {e}")
                return False
        else:
            print(
                f"[DEBUG] Invalid time drop - value doesn't contain 'time_label': {value}"
            )
            return False

    def on_gesture_drag_begin(self, gesture, start_x, start_y):
        print(f"[DEBUG] Time gesture drag begin at: {start_x}, {start_y}")
        # Store the starting position
        self.gesture_start_x = start_x
        self.gesture_start_y = start_y
        # No layer switching needed - top layer already handles gesture events

    def on_gesture_drag_update(self, gesture, offset_x, offset_y):
        # This is called during the drag to show visual feedback
        print(
            f"[DEBUG] Time gesture drag update: offset_x={offset_x}, offset_y={offset_y}"
        )

    def on_gesture_drag_end(self, gesture, offset_x, offset_y):
        print(
            f"[DEBUG] Time gesture drag end: offset_x={offset_x}, offset_y={offset_y}"
        )

        # Calculate new position
        current_x = user_options.time.x_position
        current_y = user_options.time.y_position
        new_x = int(current_x + offset_x)
        new_y = int(current_y + offset_y)

        # Apply bounds
        new_x = max(0, min(new_x, 1820))
        new_y = max(0, min(new_y, 980))

        print(f"[DEBUG] Time gesture calculated position: {new_x}, {new_y}")

        # Update position
        try:
            user_options.time.set_x_position(new_x)
            user_options.time.set_y_position(new_y)
            print("[DEBUG] Time gesture successfully updated position")
        except Exception as e:
            print(f"[DEBUG] Time gesture position update failed: {e}")

        # Move back to appropriate layer based on positioning mode
        positioning_mode = user_options.desktop_widgets.time_positioning_mode
        target_layer = "top" if positioning_mode else "bottom"
        try:
            self.set_layer(target_layer)
            print(
                f"[DEBUG] Moved time widget to {target_layer} layer after gesture (time_positioning_mode: {positioning_mode})"
            )
        except Exception as e:
            print(f"[DEBUG] Failed to change time widget layer back after gesture: {e}")


class DateWidget(widgets.Window):
    def __init__(self, monitor_id: int = 0):
        print(f"[DEBUG] DateWidget initializing for monitor {monitor_id}")

        self.date_label = widgets.Label(css_classes=["movable-date"], use_markup=True)

        date_variable = Variable(
            value=utils.Poll(
                1000,
                lambda x: datetime.datetime.now().strftime("%A %-d, %b"),
            ).bind("output")
        )

        self.date_label.label = date_variable.bind("value")
        print("[DEBUG] Date label created and bound to variable")

        self.fixed_container = Fixed(
            child=[
                FixedChild(
                    self.date_label,
                    user_options.date.x_position,
                    user_options.date.y_position,
                ),
            ],
            css_classes=["fixed-label"],
        )
        print("[DEBUG] Fixed container created")

        super().__init__(
            namespace=f"ignis_DATE_{monitor_id}",
            monitor=monitor_id,
            exclusivity="ignore",
            # dynamic_input_region=True,
            anchor=["top", "right", "bottom", "left"],
            css_classes=["rec-unset"],
            layer="bottom",  # Start on bottom layer
            child=self.fixed_container,
        )
        print("[DEBUG] DateWidget window initialized")

        # Add drag functionality to the date label after window initialization
        self.setup_drag_and_drop()

        # Connect signals for this widget only
        user_options.date.connect("changed", lambda *_: self.update_style())
        user_options.date.connect_option("x_position", lambda: self.move_widget())
        user_options.date.connect_option("y_position", lambda: self.move_widget())
        user_options.desktop_widgets.connect_option(
            "date_enabled", lambda: self.update_visibility()
        )
        user_options.desktop_widgets.connect_option(
            "date_positioning_mode", lambda: self.update_layer()
        )
        print("[DEBUG] Event handlers connected")

        # Set initial state
        self.update_style()
        self.update_visibility()
        self.update_layer()  # Set initial layer based on positioning mode
        print("[DEBUG] DateWidget initialization complete")

    def setup_drag_and_drop(self):
        print("[DEBUG] Setting up drag and drop for date label")

        # Method 1: Try standard drag source first
        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare)
        drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-end", self.on_drag_end)
        self.date_label.add_controller(drag_source)
        print("[DEBUG] Drag source added to date label")

        # Method 2: Fallback gesture drag for bottom layer
        gesture_drag = Gtk.GestureDrag()
        gesture_drag.connect("drag-begin", self.on_gesture_drag_begin)
        gesture_drag.connect("drag-update", self.on_gesture_drag_update)
        gesture_drag.connect("drag-end", self.on_gesture_drag_end)
        self.date_label.add_controller(gesture_drag)
        print("[DEBUG] Gesture drag controller added as fallback")

        # Set up drop target on the fixed container
        drop_target = Gtk.DropTarget.new(type=str, actions=Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        drop_target.connect("enter", self.on_drag_enter)
        drop_target.connect("leave", self.on_drag_leave)

        # Add the drop target to the window itself so it can receive drops anywhere
        self.add_controller(drop_target)
        print("[DEBUG] Drop target added to window")

    def on_drag_prepare(self, drag_source, x, y):
        print(f"[DEBUG] Drag prepare called at position: x={x}, y={y}")

        # Store the relative position where drag started
        self.drag_start_x = x
        self.drag_start_y = y
        print(
            f"[DEBUG] Stored drag start position: {self.drag_start_x}, {self.drag_start_y}"
        )

        # Return content provider for the drag - simplified approach
        try:
            data = "date_label".encode("utf-8")
            bytes_data = GLib.Bytes(data)
            content = Gdk.ContentProvider.new_for_bytes("text/plain", bytes_data)
            print("[DEBUG] Content provider created successfully")
            return content
        except Exception as e:
            print(f"[DEBUG] Error creating content provider: {e}")
            return None

    def on_drag_begin(self, drag_source, drag):
        print("[DEBUG] Drag begin - drag operation started")
        # No layer switching needed - top layer already handles input events
        # Optionally set a drag icon
        pass

    def on_drag_end(self, drag_source, drag, delete_data):
        print(
            f"[DEBUG] Date drag end - operation completed, delete_data: {delete_data}"
        )
        # Move back to appropriate layer based on positioning mode after drag is complete
        positioning_mode = user_options.desktop_widgets.date_positioning_mode
        target_layer = "top" if positioning_mode else "bottom"
        try:
            self.set_layer(target_layer)
            print(
                f"[DEBUG] Moved date widget to {target_layer} layer after dragging (date_positioning_mode: {positioning_mode})"
            )
        except Exception as e:
            print(f"[DEBUG] Failed to change date widget layer back: {e}")

    def on_drag_enter(self, drop_target, x, y):
        print(f"[DEBUG] Drag enter at position: x={x}, y={y}")
        return Gdk.DragAction.MOVE

    def on_drag_leave(self, drop_target):
        print("[DEBUG] Drag leave - left drop zone")

    def on_drop(self, drop_target, value, x, y):
        print(f"[DEBUG] Drop event at position: x={x}, y={y}, value={value}")

        if value and "date_label" in str(value):
            print("[DEBUG] Valid drop detected for date_label")

            # Get current widget position
            current_x = user_options.date.x_position
            current_y = user_options.date.y_position
            print(f"[DEBUG] Current widget position: {current_x}, {current_y}")

            # Calculate new position relative to the drag start
            new_x = int(x - self.drag_start_x)
            new_y = int(y - self.drag_start_y)
            print(f"[DEBUG] Calculated new position (before bounds): {new_x}, {new_y}")

            # Ensure position is within reasonable bounds
            new_x = max(0, min(new_x, 1820))
            new_y = max(0, min(new_y, 980))
            print(f"[DEBUG] Final position (after bounds): {new_x}, {new_y}")

            # Update the position in user options
            try:
                user_options.date.set_x_position(new_x)
                user_options.date.set_y_position(new_y)
                print(f"[DEBUG] Successfully updated position to: {new_x}, {new_y}")
                return True
            except Exception as e:
                print(f"[DEBUG] Error updating position: {e}")
                return False
        else:
            print(f"[DEBUG] Invalid drop - value doesn't contain 'date_label': {value}")
            return False

    def on_gesture_drag_begin(self, gesture, start_x, start_y):
        print(f"[DEBUG] Gesture drag begin at: {start_x}, {start_y}")
        # Store the starting position
        self.gesture_start_x = start_x
        self.gesture_start_y = start_y
        # No layer switching needed - top layer already handles gesture events

    def on_gesture_drag_update(self, gesture, offset_x, offset_y):
        # This is called during the drag to show visual feedback
        # We could add visual feedback here if needed
        print(f"[DEBUG] Gesture drag update: offset_x={offset_x}, offset_y={offset_y}")

    def on_gesture_drag_end(self, gesture, offset_x, offset_y):
        print(f"[DEBUG] Gesture drag end: offset_x={offset_x}, offset_y={offset_y}")

        # Calculate new position
        current_x = user_options.date.x_position
        current_y = user_options.date.y_position
        new_x = int(current_x + offset_x)
        new_y = int(current_y + offset_y)

        # Apply bounds
        new_x = max(0, min(new_x, 1820))
        new_y = max(0, min(new_y, 980))

        print(f"[DEBUG] Gesture calculated position: {new_x}, {new_y}")

        # Update position
        try:
            user_options.date.set_x_position(new_x)
            user_options.date.set_y_position(new_y)
            print("[DEBUG] Gesture successfully updated position")
        except Exception as e:
            print(f"[DEBUG] Gesture position update failed: {e}")

        # Move back to appropriate layer based on positioning mode after drag is complete
        positioning_mode = user_options.desktop_widgets.date_positioning_mode
        target_layer = "top" if positioning_mode else "bottom"
        try:
            self.set_layer(target_layer)
            print(
                f"[DEBUG] Moved date widget to {target_layer} layer after gesture (date_positioning_mode: {positioning_mode})"
            )
        except Exception as e:
            print(f"[DEBUG] Failed to change date widget layer back after gesture: {e}")

    def move_widget(self):
        x_pos = user_options.date.x_position
        y_pos = user_options.date.y_position
        print(f"[DEBUG] Moving widget to position: x={x_pos}, y={y_pos}")

        self.fixed_container.move(
            self.date_label,
            x_pos,
            y_pos,
        )
        print("[DEBUG] Widget moved successfully")

    def update_visibility(self):
        enabled = user_options.desktop_widgets.date_enabled
        print(f"[DEBUG] Updating visibility - enabled: {enabled}")
        self.set_visible(enabled)

    def update_layer(self):
        positioning_mode = user_options.desktop_widgets.date_positioning_mode
        target_layer = "top" if positioning_mode else "bottom"
        print(
            f"[DEBUG] DateWidget updating layer - date_positioning_mode: {positioning_mode}, target_layer: {target_layer}"
        )

        try:
            self.set_layer(target_layer)
            print(f"[DEBUG] DateWidget successfully changed layer to: {target_layer}")
        except Exception as e:
            print(f"[DEBUG] DateWidget failed to change layer to {target_layer}: {e}")

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
