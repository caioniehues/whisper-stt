# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation
```bash
# Install PyTorch with ROCm support first (required)
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
# Real-time mode (foreground)
stt

# Real-time mode (background daemon)
stt daemon

# Real-time mode (with system tray)
stt tray

# Meeting mode GUI
stt gui

# Transcribe a file directly
stt transcribe meeting.mp3

# Check daemon status
stt status

# Stop daemon
stt stop

# Toggle recording on/off
stt toggle

# Use a different model or language
stt -m medium -l pt
stt transcribe -m turbo recording.mp3
```

## Architecture Overview

### Two-Mode System

This application operates in two distinct modes with different data flows:

**1. Real-time Push-to-Talk Mode** (`realtime.py`)
- **Trigger**: F13 key toggle via evdev (kernel-level input capture)
- **Flow**: Audio Input → PyAudio Stream → Chunk Buffer → Whisper Transcription → wtype Text Injection
- **Components**:
  - `hotkey.py`: F13 capture using evdev (requires `input` group membership)
  - `realtime.py`: Audio streaming with PyAudio, buffering, and transcription coordination
  - `typing.py`: Wayland text injection via `wtype` subprocess
  - `transcriber.py`: Whisper inference wrapper
- **Threading**: Audio callback thread + transcription worker thread
- **State**: Status written to `$XDG_RUNTIME_DIR/whisper-stt/status.json`

**2. Meeting Mode** (`meeting.py`)
- **Trigger**: File selection via GUI or CLI
- **Flow**: Audio File → Whisper Transcription + Diarization → Merged Segments → Markdown Output
- **Components**:
  - `meeting.py`: Orchestrates transcription + diarization
  - `diarization.py`: pyannote.audio for speaker segmentation
  - `markdown.py`: Structured transcript formatting
  - `title_generator.py`: Content-based filename generation
  - `gui/`: PySide6 interface with drag-and-drop
- **Output**: Auto-named markdown file with timestamps and speaker labels

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

## Key Implementation Patterns

### Lazy Model Loading
All models (Whisper, pyannote) use lazy initialization to avoid loading during import:
```python
@property
def model(self) -> whisper.Whisper:
    if self._model is None:
        self._model = self._load_model()
    return self._model
```

### Progress Callbacks
Meeting mode uses callback pattern for progress updates:
```python
def on_progress(msg: str, progress: float) -> None:
    # Called during transcription with status and 0.0-1.0 progress
```

### Speaker Diarization Merge
`diarization.py` aligns word-level timestamps from Whisper with speaker segments from pyannote:
- Whisper provides words with timestamps
- pyannote provides speaker segments with time ranges
- `merge_with_transcription()` assigns speakers to words based on temporal overlap

### Status File Communication
Daemon mode writes JSON status to allow external tools (Waybar) to monitor state:
- Location: `$XDG_RUNTIME_DIR/whisper-stt/status.json`
- Fields: `recording` (bool), `running` (bool), `model` (str), `pid` (int)
- Waybar integration via `contrib/waybar/stt-status.py`

## Testing Considerations

When writing tests:
- Mock `torch.cuda.is_available()` to simulate GPU presence/absence
- Mock `evdev.list_devices()` for hotkey tests (requires root otherwise)
- Use small test audio files (<5 seconds) to avoid slow tests
- Consider using `model_name="tiny"` for faster test execution
- Test VRAM fallback by mocking `torch.cuda.OutOfMemoryError`

## Common Gotchas

1. **F13 not detected**: User must be in `input` group AND log out/in for changes to take effect
2. **wtype permission denied**: Wayland compositor must support virtual keyboard protocol
3. **Model download on first run**: First execution downloads ~3GB model, may appear hung
4. **Speaker diarization requires HuggingFace login**: `huggingface-cli login` for pyannote models
5. **ROCm installation**: System PyTorch won't work, must install from ROCm-specific index
