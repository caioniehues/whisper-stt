# Contributing to Whisper STT

Thank you for your interest in contributing to Whisper STT! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing. We are committed to providing a welcoming and inclusive environment.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
1. Check existing [GitHub Issues](https://github.com/caioniehues/whisper-stt/issues) to avoid duplicates
2. Collect relevant information (OS, Python version, GPU, error messages)

**Bug reports should include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- System information:
  ```bash
  python --version
  pip show whisper-stt
  rocminfo | head -20  # GPU info
  echo $XDG_SESSION_TYPE  # Wayland check
  ```
- Error messages or logs

### Suggesting Features

Feature requests are welcome! Please:
1. Check if the feature was already requested
2. Describe the use case clearly
3. Explain why existing features don't solve your need

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- AMD GPU with ROCm support (or CPU for testing)
- Arch Linux with Wayland (Hyprland/Sway)
- User in `input` group

### Installation

```bash
# Clone the repository
git clone https://github.com/caioniehues/whisper-stt.git
cd whisper-stt

# Install PyTorch with ROCm
pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm6.3

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=whisper_stt --cov-report=term-missing

# Run specific test file
pytest tests/test_transcriber.py

# Run specific test
pytest tests/test_transcriber.py::test_model_loading -v
```

### Linting and Formatting

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Code Style

- **Line length**: 100 characters
- **Type hints**: Required for all public functions
- **Docstrings**: Google-style for public APIs
- **Imports**: Sorted by ruff (isort compatible)

Example:
```python
from __future__ import annotations

from pathlib import Path
from typing import Optional


def transcribe_audio(
    audio_path: Path,
    model_name: str = "turbo",
    language: Optional[str] = None,
) -> str:
    """Transcribe audio file to text.

    Args:
        audio_path: Path to the audio file.
        model_name: Whisper model to use.
        language: Target language code (auto-detect if None).

    Returns:
        Transcribed text.

    Raises:
        FileNotFoundError: If audio file doesn't exist.
    """
    ...
```

### Commit Messages

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change without feature/fix
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(realtime): add recording duration display
fix(hotkey): handle keyboards without F13
docs(readme): update installation instructions
```

## Project Structure

```
whisper-stt/
├── src/whisper_stt/      # Main package
│   ├── cli.py            # CLI entry point
│   ├── transcriber.py    # Whisper wrapper
│   ├── realtime.py       # Push-to-talk mode
│   ├── meeting.py        # Meeting transcription
│   ├── diarization.py    # Speaker identification
│   ├── hotkey.py         # F13 capture
│   ├── typing.py         # wtype integration
│   ├── service/          # Daemon management
│   └── gui/              # PySide6 GUI
├── contrib/              # External integrations
│   ├── waybar/           # Waybar module
│   └── bar-widget/       # React widget
├── tests/                # Test suite
├── docs/                 # Documentation
└── pyproject.toml        # Project configuration
```

## Testing Guidelines

### Writing Tests

- Use `pytest` fixtures for setup/teardown
- Mock external dependencies (GPU, audio, keyboard)
- Use `model_name="tiny"` for faster tests
- Keep test files under 5 seconds

### Mocking Examples

```python
from unittest.mock import patch

# Mock GPU availability
@patch('torch.cuda.is_available', return_value=False)
def test_cpu_fallback(mock_cuda):
    from whisper_stt.transcriber import Transcriber
    transcriber = Transcriber()
    assert transcriber.device == "cpu"

# Mock keyboard devices
@patch('evdev.list_devices', return_value=[])
def test_no_keyboard(mock_devices):
    from whisper_stt.hotkey import HotkeyListener
    with pytest.raises(RuntimeError):
        HotkeyListener(lambda x: None)._find_keyboard_device()
```

## Questions?

- Open a [GitHub Issue](https://github.com/caioniehues/whisper-stt/issues) for questions
- Check existing issues and discussions first

Thank you for contributing!
