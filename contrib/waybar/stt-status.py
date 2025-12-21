#!/usr/bin/env python3
import json
import os
from pathlib import Path

XDG_RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATUS_FILE = XDG_RUNTIME_DIR / "whisper-stt" / "status.json"

def main():
    if not STATUS_FILE.exists():
        output = {"text": "", "tooltip": "STT: Not running", "class": "stopped"}
    else:
        try:
            status = json.loads(STATUS_FILE.read_text())
            recording = status.get("recording", False)
            model = status.get("model", "unknown")
            
            if recording:
                output = {
                    "text": "󰍬",
                    "tooltip": f"STT: Recording ({model})",
                    "class": "recording"
                }
            else:
                output = {
                    "text": "󰍭",
                    "tooltip": f"STT: Ready ({model})",
                    "class": "ready"
                }
        except (json.JSONDecodeError, IOError):
            output = {"text": "", "tooltip": "STT: Error", "class": "error"}
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
