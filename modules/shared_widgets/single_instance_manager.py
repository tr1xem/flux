from typing import Dict
from ignis.window_manager import WindowManager

window_manager = WindowManager.get_default()


class SingleInstanceManager:
    """Manages single instances of widgets that can switch between monitors"""
    _instances: Dict[str, 'SingleInstanceManager'] = {}
    
    def __init__(self, window_prefix: str):
        self.window_prefix = window_prefix
        self.current_monitor = 0  # Always use monitor 0 for single instance
    
    @classmethod
    def get_instance(cls, window_prefix: str) -> 'SingleInstanceManager':
        """Get or create a singleton instance for the given window prefix"""
        if window_prefix not in cls._instances:
            cls._instances[window_prefix] = cls(window_prefix)
        return cls._instances[window_prefix]
    
    def toggle_or_switch(self, requested_monitor: int) -> None:
        """Toggle visibility or switch to the specified monitor"""
        window_name = f"ignis_{self.window_prefix}_0"
        window = window_manager.get_window(window_name)
        
        if window and hasattr(window, 'visible') and hasattr(window, 'monitor'):
            if window.visible and window.monitor == requested_monitor:
                # Same monitor and visible - toggle off
                window.visible = False
            else:
                # Different monitor or not visible - switch and show
                if window.monitor != requested_monitor:
                    window.set_monitor(requested_monitor)
                window.visible = True
    
    def is_visible_on_monitor(self, monitor: int) -> bool:
        """Check if the widget is visible on the specified monitor"""
        window_name = f"ignis_{self.window_prefix}_0"
        window = window_manager.get_window(window_name)
        
        if window and hasattr(window, 'visible') and hasattr(window, 'monitor'):
            return window.visible and window.monitor == monitor
        return False