import subprocess
import sys
from signal import SIGINT, SIGTERM, signal

from gi.repository import GObject
from ignis.base_service import BaseService


class IdleInhibitorService(BaseService):
    """
    Service for managing idle inhibition using wlinhibit or systemd-inhibit.
    
    Prevents the system from going idle/sleeping when activated.
    """
    
    def __init__(self):
        super().__init__()
        self._is_inhibiting = False
        self._inhibit_process = None
        self._inhibit_method = self._detect_inhibit_method()
        self._available = self._inhibit_method is not None

        signal(SIGINT, self._on_signal)
        signal(SIGTERM, self._on_signal)

    def _on_signal(self, *args):
        self.cleanup()
        sys.exit(0)

    def _detect_inhibit_method(self) -> str | None:
        """Detect which idle inhibition method is available"""
        # Try wlinhibit first (best for Wayland)
        try:
            subprocess.run(['wlinhibit', '--help'], capture_output=True, check=True)
            return 'wlinhibit'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # Try systemd-inhibit as fallback
        try:
            subprocess.run(['systemd-inhibit', '--help'], capture_output=True, check=True)
            return 'systemd-inhibit'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        return None

    @GObject.Property(type=bool, default=False)
    def is_inhibiting(self) -> bool:
        """Whether idle inhibition is currently active"""
        return self._is_inhibiting

    @GObject.Property(type=bool, default=False)
    def available(self) -> bool:
        """Whether idle inhibition is available on this system"""
        return self._available

    def start_inhibiting(self) -> bool:
        """
        Start inhibiting idle/sleep
        
        Returns:
            bool: True if inhibition started successfully
        """
        if not self._available or self._is_inhibiting:
            return False
            
        try:
            if self._inhibit_method == 'wlinhibit':
                # Start wlinhibit as a background process
                self._inhibit_process = subprocess.Popen(
                    ['wlinhibit'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif self._inhibit_method == 'systemd-inhibit':
                # Use systemd-inhibit to prevent idle and sleep
                self._inhibit_process = subprocess.Popen(
                    ['systemd-inhibit', '--what=idle:sleep', '--who=ignis', 
                     '--why=User requested idle inhibition', 'sleep', 'infinity'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                return False
                
            self._is_inhibiting = True
            self.notify("is_inhibiting")
            return True
        except Exception:
            return False

    def stop_inhibiting(self) -> bool:
        """
        Stop inhibiting idle/sleep
        
        Returns:
            bool: True if inhibition stopped successfully
        """
        if not self._is_inhibiting or self._inhibit_process is None:
            return False
            
        try:
            self._inhibit_process.terminate()
            self._inhibit_process.wait(timeout=2)
            self._inhibit_process = None
            self._is_inhibiting = False
            self.notify("is_inhibiting")
            return True
        except Exception:
            # Force kill if terminate doesn't work
            try:
                if self._inhibit_process:
                    self._inhibit_process.kill()
                    self._inhibit_process = None
                self._is_inhibiting = False
                self.notify("is_inhibiting")
                return True
            except Exception:
                return False

    def toggle(self) -> bool:
        """
        Toggle idle inhibition state
        
        Returns:
            bool: New inhibition state
        """
        if self._is_inhibiting:
            self.stop_inhibiting()
        else:
            self.start_inhibiting()
        return self._is_inhibiting

    def cleanup(self):
        """Clean up resources"""
        if self._is_inhibiting and self._inhibit_process:
            try:
                self._inhibit_process.terminate()
                self._inhibit_process.wait(timeout=2)
            except Exception:
                try:
                    self._inhibit_process.kill()
                except Exception:
                    pass
            finally:
                self._inhibit_process = None
                self._is_inhibiting = False

    @property
    def inhibit_method(self) -> str | None:
        """Get the current inhibition method being used"""
        return self._inhibit_method
