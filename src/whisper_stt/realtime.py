"""Push-to-talk audio capture and transcription pipeline."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pyaudio

# Use same path as daemon.py for Waybar compatibility
XDG_RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATE_DIR = XDG_RUNTIME_DIR / "whisper-stt"
STATUS_FILE = STATE_DIR / "status.json"

from whisper_stt.transcriber import Transcriber
from whisper_stt.typing import WaylandTyper, get_typer
from whisper_stt.hotkey import HotkeyListener

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
FORMAT = pyaudio.paFloat32


class RealtimeTranscriber:
    """Push-to-talk speech-to-text with F13 toggle and Wayland output.

    Records audio while F13 is active, then transcribes the complete
    recording when F13 is released.
    """

    def __init__(
        self,
        model_name: str = "turbo",
        language: str = "en",
        on_transcription: Optional[Callable[[str], None]] = None,
        on_state_change: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.model_name = model_name
        self.language = language
        self.on_transcription = on_transcription
        self.on_state_change = on_state_change

        self._transcriber: Optional[Transcriber] = None
        self._typer: Optional[WaylandTyper] = None
        self._hotkey: Optional[HotkeyListener] = None

        self._audio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._audio_chunks: list[np.ndarray] = []
        self._chunks_lock = threading.Lock()

        self._running = False
        self._recording = False
        self._recording_start_time: Optional[float] = None

    def _write_status(self) -> None:
        status = {
            "recording": self._recording,
            "running": self._running,
            "model": self.model_name,
            "pid": os.getpid(),
            "recording_start_time": self._recording_start_time,
        }
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            STATUS_FILE.write_text(json.dumps(status))
        except Exception:
            pass

    def _clear_status(self) -> None:
        try:
            STATUS_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    def start(self) -> None:
        if self._running:
            return

        logger.info("Initializing push-to-talk transcriber...")

        self._transcriber = Transcriber(
            model_name=self.model_name,
            language=self.language,
        )
        _ = self._transcriber.model

        self._typer = get_typer()
        self._audio = pyaudio.PyAudio()

        self._running = True

        self._hotkey = HotkeyListener(on_toggle=self._on_toggle)
        self._hotkey.start()

        self._write_status()
        logger.info("Ready. Press F13 to start recording, press again to stop and transcribe.")

    def stop(self) -> None:
        self._running = False

        if self._hotkey:
            self._hotkey.stop()

        if self._recording:
            self._stop_recording(transcribe=False)

        if self._audio:
            self._audio.terminate()
            self._audio = None

        if self._transcriber:
            self._transcriber.unload()

        self._clear_status()
        logger.info("Push-to-talk transcriber stopped.")

    def _on_toggle(self, is_recording: bool) -> None:
        self._recording = is_recording
        self._recording_start_time = time.time() if is_recording else None
        self._write_status()

        if self.on_state_change:
            self.on_state_change(is_recording)

        if is_recording:
            self._start_recording()
        else:
            self._stop_recording(transcribe=True)

    def _start_recording(self) -> None:
        logger.info("Recording started...")

        with self._chunks_lock:
            self._audio_chunks = []

        self._stream = self._audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._audio_callback,
        )
        self._stream.start_stream()

    def _stop_recording(self, transcribe: bool = True) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        with self._chunks_lock:
            chunks = self._audio_chunks
            self._audio_chunks = []

        if not transcribe or not chunks:
            logger.info("Recording stopped (no transcription).")
            return

        audio_buffer = np.concatenate(chunks)
        duration = len(audio_buffer) / SAMPLE_RATE
        logger.info(f"Recording stopped. Transcribing {duration:.1f}s of audio...")

        # Transcribe in a thread to avoid blocking the hotkey listener
        threading.Thread(
            target=self._transcribe_buffer,
            args=(audio_buffer,),
            daemon=True,
        ).start()

    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status: int,
    ) -> tuple[None, int]:
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        with self._chunks_lock:
            self._audio_chunks.append(audio_data)
        return (None, pyaudio.paContinue)

    def _transcribe_buffer(self, audio: np.ndarray) -> None:
        try:
            result = self._transcriber.transcribe(audio)
            text = result["text"].strip()

            if text:
                logger.info(f"Transcribed: {text}")

                if self._typer:
                    self._typer.type_text(text + " ")

                if self.on_transcription:
                    self.on_transcription(text)
            else:
                logger.info("No speech detected.")

        except Exception as e:
            logger.error(f"Transcription error: {e}")

    def __enter__(self) -> "RealtimeTranscriber":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()


def run_realtime(
    model_name: str = "turbo",
    language: str = "en",
) -> None:
    """Run the push-to-talk transcriber as a blocking process."""
    import signal

    def on_state_change(is_recording: bool) -> None:
        if is_recording:
            print("\n[REC] Recording...", end=" ", flush=True)
        else:
            print("[PROCESSING]", end=" ", flush=True)

    transcriber = RealtimeTranscriber(
        model_name=model_name,
        language=language,
        on_state_change=on_state_change,
        on_transcription=lambda text: print(f"\n→ {text}"),
    )

    def signal_handler(sig, frame):
        print("\nShutting down...")
        transcriber.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    transcriber.start()

    try:
        signal.pause()
    except AttributeError:
        import time
        while transcriber._running:
            time.sleep(0.5)
