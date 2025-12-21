"""F13 hotkey capture using evdev for Wayland compatibility."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
except ImportError:
    raise ImportError("evdev is required. Install with: pip install evdev")

logger = logging.getLogger(__name__)

# F13 key code
KEY_F13 = 183


class HotkeyListener:
    """Listen for F13 key press to toggle recording.
    
    Uses evdev to capture keyboard events at the kernel level,
    bypassing Wayland's input restrictions.
    
    Requires user to be in the 'input' group:
        sudo usermod -aG input $USER
        
    Args:
        on_toggle: Callback function invoked when F13 is pressed.
        device_path: Path to keyboard device. Auto-detected if None.
        
    Example:
        >>> def on_toggle(is_recording: bool):
        ...     print(f"Recording: {is_recording}")
        >>> listener = HotkeyListener(on_toggle)
        >>> listener.start()
    """
    
    def __init__(
        self,
        on_toggle: Callable[[bool], None],
        device_path: Optional[str] = None,
    ) -> None:
        self.on_toggle = on_toggle
        self.device_path = device_path
        self._device: Optional[InputDevice] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._is_recording = False
        
    def _find_keyboard_device(self) -> str:
        """Auto-detect the keyboard device with F13 support."""
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        
        for device in devices:
            capabilities = device.capabilities()
            # Check if device has key events
            if ecodes.EV_KEY in capabilities:
                keys = capabilities[ecodes.EV_KEY]
                # Check for F13 capability or standard keyboard keys
                if KEY_F13 in keys or ecodes.KEY_A in keys:
                    logger.info(f"Found keyboard device: {device.name} at {device.path}")
                    return device.path
                    
        # Fallback: try common keyboard device paths
        common_paths = [
            "/dev/input/event0",
            "/dev/input/event1",
            "/dev/input/event2",
        ]
        for path in common_paths:
            if Path(path).exists():
                logger.warning(f"Using fallback keyboard device: {path}")
                return path
                
        raise RuntimeError(
            "No keyboard device found. Ensure you're in the 'input' group: "
            "sudo usermod -aG input $USER"
        )
    
    def start(self) -> None:
        """Start listening for F13 key presses in a background thread."""
        if self._running:
            logger.warning("Listener already running")
            return
            
        device_path = self.device_path or self._find_keyboard_device()
        
        try:
            self._device = InputDevice(device_path)
            logger.info(f"Opened device: {self._device.name}")
        except PermissionError:
            raise PermissionError(
                f"Cannot access {device_path}. Add user to input group:\n"
                "  sudo usermod -aG input $USER\n"
                "Then log out and back in."
            )
        
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Hotkey listener started (press F13 to toggle)")
        
    def stop(self) -> None:
        """Stop the listener."""
        self._running = False
        if self._device:
            self._device.close()
            self._device = None
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("Hotkey listener stopped")
        
    def _listen_loop(self) -> None:
        """Main event loop for keyboard events."""
        try:
            for event in self._device.read_loop():
                if not self._running:
                    break
                    
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    
                    # Only respond to key down events
                    if key_event.keycode == "KEY_F13" or key_event.scancode == KEY_F13:
                        if key_event.keystate == key_event.key_down:
                            self._is_recording = not self._is_recording
                            logger.debug(f"F13 pressed, recording: {self._is_recording}")
                            self.on_toggle(self._is_recording)
                            
        except OSError as e:
            if self._running:
                logger.error(f"Device read error: {e}")
                
    @property
    def is_recording(self) -> bool:
        """Current recording state."""
        return self._is_recording
    
    def __enter__(self) -> "HotkeyListener":
        self.start()
        return self
        
    def __exit__(self, *args) -> None:
        self.stop()


def find_f13_device() -> Optional[str]:
    """Find a keyboard device that supports F13.
    
    Returns:
        Device path if found, None otherwise.
    """
    try:
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            caps = device.capabilities()
            if ecodes.EV_KEY in caps and KEY_F13 in caps[ecodes.EV_KEY]:
                return device.path
    except Exception as e:
        logger.debug(f"Error scanning devices: {e}")
    return None
