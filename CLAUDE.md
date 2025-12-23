# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**whisper-stt** is a real-time speech-to-text tool optimized for AMD ROCm on Arch Linux with Wayland. It provides two distinct modes: push-to-talk dictation and meeting transcription with speaker diarization.

### Key Technologies
- **Backend**: Python 3.10+, OpenAI Whisper, pyannote.audio
- **GPU**: AMD ROCm (PyTorch CUDA compatibility layer)
- **Desktop**: PySide6 (Qt), Wayland (wtype, evdev)
- **Frontend Widget**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui

## Development Commands

### Installation
```bash
# Install PyTorch with ROCm support first (required for AMD GPUs)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm6.3

# Install in editable mode for development
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=whisper_stt --cov-report=term-missing

# Run specific test file
pytest tests/test_transcriber.py

# Run specific test
pytest tests/test_transcriber.py::test_model_loading
```

### Linting
```bash
# Run ruff linter
ruff check .

# Run ruff with auto-fix
ruff check --fix .

# Format code
ruff format .
```

### Running the Application
```bash
# Real-time mode (foreground) - default command
stt

# Real-time mode (background daemon)
stt daemon

# Real-time mode (with system tray icon)
stt tray

# Meeting mode GUI
stt gui

# Transcribe a file directly (with speaker diarization)
stt transcribe meeting.mp3

# Check daemon status
stt status

# Stop daemon
stt stop

# Toggle daemon on/off
stt toggle

# Use a different model or language
stt -m medium -l pt
stt transcribe -m turbo recording.mp3
```

## Architecture Overview

### Project Structure

```
whisper-stt/
├── src/whisper_stt/
│   ├── cli.py              # Argparse CLI entry point
│   ├── transcriber.py      # Core Whisper wrapper (shared by all modes)
│   ├── realtime.py         # Push-to-talk pipeline
│   ├── hotkey.py           # F13 capture via evdev
│   ├── typing.py           # Wayland text injection via wtype
│   ├── meeting.py          # Meeting transcription orchestrator
│   ├── diarization.py      # Speaker diarization (pyannote)
│   ├── markdown.py         # Transcript formatting
│   ├── title_generator.py  # Content-based title generation
│   ├── tray.py             # System tray icon (PySide6)
│   ├── service/
│   │   └── daemon.py       # Background daemon management
│   └── gui/
│       ├── main_window.py  # Meeting Mode GUI
│       ├── file_picker.py  # Drag-and-drop file picker
│       ├── progress.py     # VU meter-style progress widget
│       └── theme.py        # Sound Studio theme (colors, fonts)
├── contrib/
│   ├── waybar/
│   │   ├── stt-status.py   # Waybar custom module script
│   │   └── style.css       # Waybar styling
│   └── bar-widget/         # React-based status widget
│       ├── src/
│       │   ├── components/BarWidget.tsx
│       │   └── hooks/useStatus.ts
│       └── package.json
└── pyproject.toml
```

### Two-Mode System

This application operates in two distinct modes with different data flows:

#### 1. Real-time Push-to-Talk Mode (`realtime.py`)
- **Trigger**: F13 key toggle via evdev (kernel-level input capture)
- **Flow**: Audio Input → PyAudio Stream → Chunk Buffer → Whisper Transcription → wtype Text Injection
- **Components**:
  - `hotkey.py`: F13 capture using evdev (requires `input` group membership)
  - `realtime.py`: Audio streaming with PyAudio, buffering, and transcription coordination
  - `typing.py`: Wayland text injection via `wtype` subprocess
  - `transcriber.py`: Whisper inference wrapper
- **Threading**: Audio callback thread + transcription worker thread
- **State**: Status written to `$XDG_RUNTIME_DIR/whisper-stt/status.json`

#### 2. Meeting Mode (`meeting.py`)
- **Trigger**: File selection via GUI or CLI
- **Flow**: Audio File → Whisper Transcription + Diarization → Merged Segments → Markdown Output
- **Components**:
  - `meeting.py`: Orchestrates transcription + diarization
  - `diarization.py`: pyannote.audio for speaker segmentation
  - `markdown.py`: Structured transcript formatting
  - `title_generator.py`: Content-based filename generation
  - `gui/`: PySide6 interface with drag-and-drop
- **Output**: Auto-named markdown file with timestamps and speaker labels

### Core Data Flow Diagrams

#### Real-time Mode Flow
```
[F13 Key Press]
       ↓
[evdev HotkeyListener] ─→ on_toggle(is_recording)
       ↓
[RealtimeTranscriber._on_toggle()]
       ↓
   ┌───┴───┐
   │       │
[Start]  [Stop]
   ↓       ↓
[PyAudio] [Transcribe Buffer]
   ↓       ↓
[Chunks] [Whisper Model]
   ↓       ↓
[Buffer] [WaylandTyper.type_text()]
```

#### Meeting Mode Flow
```
[Audio File Path]
       ↓
[MeetingTranscriber.transcribe()]
       ↓
   ┌───┴───────────────┐
   ↓                   ↓
[Transcriber]      [Diarizer]
   ↓                   ↓
[Word Timestamps]  [Speaker Segments]
   └───────┬───────────┘
           ↓
[merge_with_transcription()]
           ↓
[generate_title_from_segments()]
           ↓
[format_meeting_transcript()]
           ↓
[Markdown File Output]
```

### Core Transcription Engine

The `Transcriber` class (`transcriber.py`) is shared between both modes:
- **Lazy loading**: Model loads on first access via `@property`
- **VRAM fallback**: Catches `torch.cuda.OutOfMemoryError` and falls back to medium model
- **Device detection**: Auto-detects CUDA/ROCm vs CPU
- **Streaming support**: `transcribe_stream()` for real-time chunks with overlap

### Service Architecture

Three execution modes:
1. **Foreground** (`stt`): Direct execution, Ctrl+C to exit
2. **Daemon** (`stt daemon`): Background process, status via JSON file
3. **Tray** (`stt tray`): Same as daemon but with Qt system tray icon

All modes use `RealtimeTranscriber` internally. The daemon is managed via `service/daemon.py` with PID tracking.

### IPC: Status File Communication

The daemon writes JSON status to allow external tools to monitor state:
```json
{
  "recording": false,
  "running": true,
  "model": "turbo",
  "pid": 12345,
  "recording_start_time": null
}
```
- **Location**: `$XDG_RUNTIME_DIR/whisper-stt/status.json` (typically `/run/user/1000/whisper-stt/status.json`)
- **Consumers**: Waybar module (`contrib/waybar/stt-status.py`), React widget, system tray

## Key Implementation Patterns

### 1. Lazy Model Loading Pattern
All heavy models (Whisper, pyannote) use lazy initialization to avoid loading during import:
```python
@property
def model(self) -> whisper.Whisper:
    if self._model is None:
        self._model = self._load_model()
    return self._model
```
**Files using this pattern**: `transcriber.py:57-62`, `diarization.py:52-56`, `meeting.py:44-57`

### 2. Progress Callback Pattern
Meeting mode uses callback pattern for progress updates:
```python
def on_progress(msg: str, progress: float) -> None:
    # Called during transcription with status and 0.0-1.0 progress
```
**Files using this pattern**: `meeting.py:64`, `cli.py:59-65`, `gui/main_window.py:45-48`

### 3. State Management via JSON Files
Daemon writes state to JSON for IPC with external tools:
```python
def _write_status(self) -> None:
    status = {
        "recording": self._recording,
        "running": self._running,
        "model": self.model_name,
        "pid": os.getpid(),
        "recording_start_time": self._recording_start_time,
    }
    STATUS_FILE.write_text(json.dumps(status))
```
**Files using this pattern**: `realtime.py:65-77`, `service/daemon.py:56-68`

### 4. Context Manager Protocol
Main classes support `with` statement for proper cleanup:
```python
def __enter__(self) -> "RealtimeTranscriber":
    self.start()
    return self

def __exit__(self, *args) -> None:
    self.stop()
```
**Files using this pattern**: `realtime.py:212-217`, `hotkey.py:169-173`

### 5. Graceful Signal Handling
All daemon modes handle SIGINT/SIGTERM for clean shutdown:
```python
def signal_handler(sig, frame):
    transcriber.stop()
    manager.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```
**Files using this pattern**: `realtime.py:240-245`, `service/daemon.py:128-134`

### 6. Speaker Diarization Merge Algorithm
Aligns word-level timestamps from Whisper with speaker segments from pyannote:
- Whisper provides words with timestamps
- pyannote provides speaker segments with time ranges
- `merge_with_transcription()` assigns speakers to words based on maximum temporal overlap

**Implementation**: `diarization.py:114-146`

### 7. GUI Threading Pattern
Heavy operations run in QThread to avoid blocking UI:
```python
class TranscriptionWorker(QThread):
    progress = Signal(str, float)
    finished = Signal(object)
    error = Signal(str)
```
**Files using this pattern**: `gui/main_window.py:24-64`

## Platform-Specific Requirements

### ROCm/GPU Considerations
- **Target hardware**: AMD RDNA3 (gfx1101), specifically RX 7800XT
- **PyTorch backend**: Uses `torch.cuda` API (ROCm's CUDA compatibility layer)
- **VRAM management**: large-v3 requires ~6GB, automatic fallback to medium if OOM
- **Model naming**: "turbo" maps to large-v3-turbo in Whisper

### Wayland Integration
- **Input capture**: Uses evdev directly (bypasses Wayland input isolation)
  - Requires user in `input` group: `sudo usermod -aG input $USER`
  - Captures at kernel level via `/dev/input/eventX`
- **Text injection**: Uses `wtype` command (Wayland alternative to `xdotool`)
  - Must be installed: `pacman -S wtype`
  - Works with wlroots-based compositors (Hyprland, Sway)

### Audio Configuration
- **Sample rate**: 16kHz (Whisper's expected input)
- **Format**: Float32
- **Channels**: Mono
- **Buffering**: 2-second minimum chunks for transcription, 0.5s overlap for context

## Contrib Modules

### Waybar Integration (`contrib/waybar/`)
Python script that outputs JSON for Waybar's custom module:
```json
{
  "custom/stt": {
    "exec": "~/.config/waybar/scripts/stt-status.py",
    "return-type": "json",
    "interval": 1,
    "on-click": "stt toggle",
    "on-click-right": "~/.config/waybar/scripts/stt-status.py --menu",
    "on-scroll-up": "~/.config/waybar/scripts/stt-status.py --next-model",
    "on-scroll-down": "~/.config/waybar/scripts/stt-status.py --prev-model"
  }
}
```

### React Bar Widget (`contrib/bar-widget/`)
Standalone React widget with audio hardware aesthetic:
- **Stack**: Vite, React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Features**: LED segment display, status indicators, model selector dropdown
- **Hook**: `useStatus()` polls status file and calculates recording duration
- **Development**: `cd contrib/bar-widget && pnpm dev`

## Testing Considerations

When writing tests:
- Mock `torch.cuda.is_available()` to simulate GPU presence/absence
- Mock `evdev.list_devices()` for hotkey tests (requires root otherwise)
- Use small test audio files (<5 seconds) to avoid slow tests
- Consider using `model_name="tiny"` for faster test execution
- Test VRAM fallback by mocking `torch.cuda.OutOfMemoryError`

### Mocking Examples
```python
# Mock GPU availability
@patch('torch.cuda.is_available', return_value=False)
def test_cpu_fallback(mock_cuda):
    transcriber = Transcriber()
    assert transcriber.device == "cpu"

# Mock keyboard devices
@patch('evdev.list_devices', return_value=[])
def test_no_keyboard_found(mock_devices):
    with pytest.raises(RuntimeError, match="No keyboard device found"):
        HotkeyListener(lambda x: None)._find_keyboard_device()
```

## Common Gotchas

1. **F13 not detected**: User must be in `input` group AND log out/in for changes to take effect
2. **wtype permission denied**: Wayland compositor must support virtual keyboard protocol
3. **Model download on first run**: First execution downloads ~3GB model, may appear hung
4. **Speaker diarization requires HuggingFace login**: `huggingface-cli login` for pyannote models
5. **ROCm installation**: System PyTorch won't work, must install from ROCm-specific index
6. **Status file permissions**: `$XDG_RUNTIME_DIR` must be accessible for IPC

## Code Style & Conventions

### Python
- **Formatter**: ruff format (line length 100)
- **Linting**: ruff check with rules E, F, W, I, UP, B, C4
- **Type hints**: Full type annotations with `from __future__ import annotations`
- **Imports**: Lazy imports for heavy dependencies (torch, whisper, pyannote)
- **Docstrings**: Google-style with Args, Returns, Example sections

### TypeScript/React (bar-widget)
- **Framework**: React 18 with hooks
- **Styling**: Tailwind CSS with custom theme
- **Components**: shadcn/ui components
- **State**: React hooks (useState, useEffect, useCallback, useRef)

### GUI Theme
The PySide6 GUI uses a "Sound Studio" aesthetic:
- **Colors**: Near-black background (#0d0d0f), amber accents (#f59e0b)
- **Fonts**: JetBrains Mono for headings, Inter for body
- **Inspiration**: Professional audio equipment (VU meters, LED indicators)
