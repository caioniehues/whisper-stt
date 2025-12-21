"""Real-time audio capture and transcription pipeline."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pyaudio

STATUS_FILE = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "whisper-stt-status.json"

from whisper_stt.transcriber import Transcriber
from whisper_stt.typing import WaylandTyper, get_typer
from whisper_stt.hotkey import HotkeyListener

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
FORMAT = pyaudio.paFloat32


class RealtimeTranscriber:
    """Real-time speech-to-text with F13 toggle and Wayland output."""

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
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._transcription_thread: Optional[threading.Thread] = None

        self._running = False
        self._recording = False

    def _write_status(self) -> None:
        status = {
            "recording": self._recording,
            "running": self._running,
            "model": self.model_name,
            "pid": os.getpid(),
        }
        try:
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

        logger.info("Initializing real-time transcriber...")

        self._transcriber = Transcriber(
            model_name=self.model_name,
            language=self.language,
        )
        _ = self._transcriber.model

        self._typer = get_typer()
        self._audio = pyaudio.PyAudio()

        self._running = True
        self._transcription_thread = threading.Thread(
            target=self._transcription_loop,
            daemon=True,
        )
        self._transcription_thread.start()

        self._hotkey = HotkeyListener(on_toggle=self._on_toggle)
        self._hotkey.start()

        self._write_status()
        logger.info("Ready. Press F13 to toggle recording.")

    def stop(self) -> None:
        self._running = False

        if self._hotkey:
            self._hotkey.stop()

        if self._recording:
            self._stop_recording()

        if self._transcription_thread:
            self._audio_queue.put(None)
            self._transcription_thread.join(timeout=2.0)

        if self._audio:
            self._audio.terminate()
            self._audio = None

        if self._transcriber:
            self._transcriber.unload()

        self._clear_status()
        logger.info("Real-time transcriber stopped.")

    def _on_toggle(self, is_recording: bool) -> None:
        self._recording = is_recording
        self._write_status()

        if self.on_state_change:
            self.on_state_change(is_recording)

        if is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self) -> None:
        logger.info("Recording started...")

        self._stream = self._audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self._audio_callback,
        )
        self._stream.start_stream()

    def _stop_recording(self) -> None:
        logger.info("Recording stopped.")

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        self._audio_queue.put(None)

    def _audio_callback(
        self,
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status: int,
    ) -> tuple[None, int]:
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        self._audio_queue.put(audio_data)
        return (None, pyaudio.paContinue)

    def _transcription_loop(self) -> None:
        audio_buffer = np.array([], dtype=np.float32)
        min_chunk_samples = int(2.0 * SAMPLE_RATE)

        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if chunk is None:
                if len(audio_buffer) > SAMPLE_RATE:
                    self._process_audio(audio_buffer)
                audio_buffer = np.array([], dtype=np.float32)
                continue

            audio_buffer = np.concatenate([audio_buffer, chunk])

            if len(audio_buffer) >= min_chunk_samples:
                self._process_audio(audio_buffer)
                overlap = int(0.5 * SAMPLE_RATE)
                audio_buffer = audio_buffer[-overlap:]

    def _process_audio(self, audio: np.ndarray) -> None:
        try:
            result = self._transcriber.transcribe(audio)
            text = result["text"].strip()

            if text:
                logger.debug(f"Transcribed: {text}")

                if self._typer:
                    self._typer.type_text(text + " ")

                if self.on_transcription:
                    self.on_transcription(text)

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
    """Run the real-time transcriber as a blocking process."""
    import signal

    transcriber = RealtimeTranscriber(
        model_name=model_name,
        language=language,
        on_state_change=lambda r: print(f"\n{'[REC]' if r else '[STOP]'}", end=" ", flush=True),
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
