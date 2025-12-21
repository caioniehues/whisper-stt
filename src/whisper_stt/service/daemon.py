from __future__ import annotations

import json
import os
import signal
import sys
from pathlib import Path
from typing import Optional

XDG_RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATE_DIR = XDG_RUNTIME_DIR / "whisper-stt"


def get_status_path() -> Path:
    return STATE_DIR / "status.json"


def get_pid_path() -> Path:
    return STATE_DIR / "daemon.pid"


class DaemonManager:
    
    def __init__(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._pid_path = get_pid_path()
        self._status_path = get_status_path()
    
    def is_running(self) -> bool:
        if not self._pid_path.exists():
            return False
        
        try:
            pid = int(self._pid_path.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError, PermissionError):
            self._pid_path.unlink(missing_ok=True)
            return False
    
    def get_pid(self) -> Optional[int]:
        if not self._pid_path.exists():
            return None
        try:
            return int(self._pid_path.read_text().strip())
        except ValueError:
            return None
    
    def write_pid(self) -> None:
        self._pid_path.write_text(str(os.getpid()))
    
    def remove_pid(self) -> None:
        self._pid_path.unlink(missing_ok=True)
    
    def write_status(self, recording: bool, model: str = "turbo") -> None:
        status = {
            "recording": recording,
            "model": model,
            "pid": os.getpid(),
        }
        self._status_path.write_text(json.dumps(status))
    
    def read_status(self) -> dict:
        if not self._status_path.exists():
            return {"recording": False, "model": "unknown", "pid": None}
        try:
            return json.loads(self._status_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {"recording": False, "model": "unknown", "pid": None}
    
    def stop_daemon(self) -> bool:
        pid = self.get_pid()
        if pid is None:
            return False
        
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except ProcessLookupError:
            self.remove_pid()
            return False
    
    def cleanup(self) -> None:
        self.remove_pid()
        self._status_path.unlink(missing_ok=True)


def run_daemon(model_name: str = "turbo", language: str = "en") -> int:
    from whisper_stt.realtime import RealtimeTranscriber
    
    manager = DaemonManager()
    
    if manager.is_running():
        print("Daemon already running.", file=sys.stderr)
        return 1
    
    manager.write_pid()
    manager.write_status(recording=False, model=model_name)
    
    def on_state_change(recording: bool) -> None:
        manager.write_status(recording=recording, model=model_name)
    
    transcriber = RealtimeTranscriber(
        model_name=model_name,
        language=language,
        on_state_change=on_state_change,
    )
    
    def signal_handler(sig, frame):
        transcriber.stop()
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        transcriber.start()
        signal.pause()
    except Exception as e:
        print(f"Daemon error: {e}", file=sys.stderr)
        manager.cleanup()
        return 1
    finally:
        manager.cleanup()
    
    return 0
