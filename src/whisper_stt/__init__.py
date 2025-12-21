"""Whisper STT - Real-time speech-to-text for AMD ROCm on Wayland."""

__version__ = "0.1.0"
__all__ = [
    "Transcriber",
    "HotkeyListener", 
    "WaylandTyper",
    "RealtimeTranscriber",
    "MeetingTranscriber",
    "Diarizer",
]

from whisper_stt.transcriber import Transcriber
from whisper_stt.hotkey import HotkeyListener
from whisper_stt.typing import WaylandTyper
from whisper_stt.realtime import RealtimeTranscriber
from whisper_stt.meeting import MeetingTranscriber
from whisper_stt.diarization import Diarizer
