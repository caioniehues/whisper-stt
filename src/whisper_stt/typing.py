"""Wayland text injection using wtype."""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class WaylandTyper:
    """Type text into the focused window on Wayland using wtype.
    
    wtype is a Wayland-native tool that simulates keyboard input.
    Works with wlroots-based compositors like Hyprland and Sway.
    
    Install wtype on Arch Linux:
        sudo pacman -S wtype
        
    Args:
        delay_ms: Delay between keystrokes in milliseconds.
        
    Example:
        >>> typer = WaylandTyper()
        >>> typer.type_text("Hello, world!")
    """
    
    def __init__(self, delay_ms: int = 0) -> None:
        self.delay_ms = delay_ms
        self._wtype_path = self._find_wtype()
        
    def _find_wtype(self) -> str:
        """Find the wtype executable."""
        wtype_path = shutil.which("wtype")
        if wtype_path is None:
            raise RuntimeError(
                "wtype not found. Install it:\n"
                "  Arch Linux: sudo pacman -S wtype\n"
                "  Or from AUR: yay -S wtype"
            )
        logger.debug(f"Found wtype at: {wtype_path}")
        return wtype_path
    
    def type_text(self, text: str) -> bool:
        """Type text into the focused window.
        
        Args:
            text: Text to type.
            
        Returns:
            True if successful, False otherwise.
        """
        if not text:
            return True
            
        try:
            cmd = [self._wtype_path]
            
            if self.delay_ms > 0:
                cmd.extend(["-d", str(self.delay_ms)])
            
            # Use -- to prevent text starting with - being interpreted as flags
            cmd.extend(["--", text])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                logger.error(f"wtype failed: {result.stderr}")
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("wtype timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False
    
    def type_key(self, key: str) -> bool:
        """Press a special key.
        
        Args:
            key: Key name (e.g., "Return", "Tab", "BackSpace").
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            result = subprocess.run(
                [self._wtype_path, "-k", key],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to press key {key}: {e}")
            return False
    
    def type_with_newline(self, text: str) -> bool:
        """Type text followed by Enter key.
        
        Args:
            text: Text to type.
            
        Returns:
            True if successful, False otherwise.
        """
        success = self.type_text(text)
        if success:
            success = self.type_key("Return")
        return success
    
    @staticmethod
    def is_wayland() -> bool:
        """Check if running on Wayland.
        
        Returns:
            True if Wayland session detected.
        """
        import os
        return bool(os.environ.get("WAYLAND_DISPLAY"))
    
    @staticmethod
    def check_environment() -> tuple[bool, Optional[str]]:
        """Check if the environment is properly configured.
        
        Returns:
            Tuple of (is_ready, error_message).
        """
        import os
        
        # Check Wayland
        if not os.environ.get("WAYLAND_DISPLAY"):
            return False, "Not running on Wayland (WAYLAND_DISPLAY not set)"
        
        # Check wtype
        if not shutil.which("wtype"):
            return False, "wtype not installed (sudo pacman -S wtype)"
        
        return True, None


class DummyTyper:
    """Fallback typer that just prints to stdout.
    
    Used when wtype is not available or for testing.
    """
    
    def type_text(self, text: str) -> bool:
        """Print text to stdout."""
        print(text, end="", flush=True)
        return True
    
    def type_key(self, key: str) -> bool:
        """Print key name."""
        if key == "Return":
            print()
        return True
    
    def type_with_newline(self, text: str) -> bool:
        """Print text with newline."""
        print(text)
        return True


def get_typer(force_dummy: bool = False) -> WaylandTyper | DummyTyper:
    """Get the appropriate typer for the current environment.
    
    Args:
        force_dummy: Force use of DummyTyper for testing.
        
    Returns:
        WaylandTyper if available, DummyTyper otherwise.
    """
    if force_dummy:
        return DummyTyper()
    
    try:
        return WaylandTyper()
    except RuntimeError as e:
        logger.warning(f"Falling back to DummyTyper: {e}")
        return DummyTyper()
