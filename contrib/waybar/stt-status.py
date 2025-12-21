#!/usr/bin/env python3
"""Waybar custom module for whisper-stt.

Usage in waybar config:
    "custom/stt": {
        "exec": "~/.config/waybar/scripts/stt-status.py",
        "return-type": "json",
        "interval": 1,
        "on-click": "stt toggle",
        "on-click-right": "~/.config/waybar/scripts/stt-status.py --menu",
        "on-scroll-up": "~/.config/waybar/scripts/stt-status.py --next-model",
        "on-scroll-down": "~/.config/waybar/scripts/stt-status.py --prev-model"
    }
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

XDG_RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATUS_FILE = XDG_RUNTIME_DIR / "whisper-stt" / "status.json"

# Available models in order (for cycling)
MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]

# Icons (Nerd Fonts)
ICON_RECORDING = "󰍬"  # microphone
ICON_READY = "󰍭"      # microphone-off (but we use it as ready)


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS or HH:MM:SS if over an hour."""
    seconds = int(seconds)
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"


def read_status() -> dict | None:
    """Read current status from status file."""
    if not STATUS_FILE.exists():
        return None
    try:
        return json.loads(STATUS_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def get_waybar_output() -> dict:
    """Generate Waybar JSON output."""
    status = read_status()

    if status is None:
        return {
            "text": ICON_READY,
            "tooltip": "whisper-stt: Not running",
            "class": "stopped",
        }

    recording = status.get("recording", False)
    model = status.get("model", "unknown")
    pid = status.get("pid", "?")
    recording_start = status.get("recording_start_time")

    if recording and recording_start:
        duration = time.time() - recording_start
        duration_str = format_duration(duration)
        return {
            "text": f"{ICON_RECORDING} {duration_str}",
            "tooltip": f"Recording | Model: {model} | PID: {pid}",
            "class": "recording",
        }
    elif status.get("running", True):
        return {
            "text": ICON_READY,
            "tooltip": f"Ready | Model: {model} | PID: {pid}",
            "class": "ready",
        }
    else:
        return {
            "text": ICON_READY,
            "tooltip": f"Stopped | Model: {model}",
            "class": "stopped",
        }


def cycle_model(direction: int) -> None:
    """Cycle to next (+1) or previous (-1) model."""
    status = read_status()
    if status is None:
        return

    current = status.get("model", "turbo")
    try:
        idx = MODELS.index(current)
    except ValueError:
        idx = MODELS.index("turbo")

    new_idx = (idx + direction) % len(MODELS)
    new_model = MODELS[new_idx]

    if new_model != current:
        # Restart daemon with new model
        subprocess.run(["stt", "stop"], capture_output=True)
        subprocess.run(["stt", "-m", new_model, "daemon"], capture_output=True)


def show_menu() -> None:
    """Show model selection menu via wofi or rofi."""
    status = read_status()
    current = status.get("model", "turbo") if status else "turbo"

    # Build menu with current model marked
    menu_items = []
    for model in MODELS:
        if model == current:
            menu_items.append(f"● {model}")
        else:
            menu_items.append(f"  {model}")

    menu_input = "\n".join(menu_items)

    # Try wofi first, fall back to rofi
    for launcher in ["wofi", "rofi"]:
        try:
            result = subprocess.run(
                [launcher, "--dmenu", "--prompt", "Model"],
                input=menu_input,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                selected = result.stdout.strip()
                # Extract model name (remove the bullet/space prefix)
                selected_model = selected.lstrip("● ").strip()
                if selected_model in MODELS and selected_model != current:
                    subprocess.run(["stt", "stop"], capture_output=True)
                    subprocess.run(["stt", "-m", selected_model, "daemon"], capture_output=True)
                return
        except FileNotFoundError:
            continue

    # No launcher found - silently fail
    pass


def main():
    parser = argparse.ArgumentParser(description="Waybar module for whisper-stt")
    parser.add_argument("--next-model", action="store_true", help="Cycle to next model")
    parser.add_argument("--prev-model", action="store_true", help="Cycle to previous model")
    parser.add_argument("--menu", action="store_true", help="Show model selection menu")
    args = parser.parse_args()

    if args.next_model:
        cycle_model(1)
    elif args.prev_model:
        cycle_model(-1)
    elif args.menu:
        show_menu()
    else:
        # Default: output status JSON for Waybar
        output = get_waybar_output()
        print(json.dumps(output))


if __name__ == "__main__":
    main()
