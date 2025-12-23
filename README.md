# Whisper STT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)
[![Wayland](https://img.shields.io/badge/display-Wayland-blueviolet.svg)](https://wayland.freedesktop.org/)
[![AMD ROCm](https://img.shields.io/badge/GPU-AMD%20ROCm-red.svg)](https://rocm.docs.amd.com/)

> Real-time speech-to-text tool optimized for AMD ROCm on Arch Linux with Wayland

Push-to-talk dictation and meeting transcription with speaker diarization, powered by OpenAI Whisper. Designed specifically for AMD GPU users on Wayland desktops.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Real-time Dictation](#real-time-dictation)
  - [Meeting Transcription](#meeting-transcription)
  - [Service Management](#service-management)
- [Desktop Integration](#desktop-integration)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Push-to-Talk Dictation** — Press F13 to record, release to transcribe and type directly into any application
- **Meeting Transcription** — Transcribe audio files with automatic speaker diarization (who said what)
- **AMD ROCm Support** — Optimized for AMD GPUs (RX 7800XT tested) with automatic VRAM fallback
- **Wayland Native** — Works with Hyprland, Sway, and other wlroots-based compositors
- **Background Daemon** — Run as a service with system tray icon
- **Waybar Integration** — Custom module with recording status, duration timer, and model selection
- **React Bar Widget** — Modern UI widget for desktop bars (see [contrib/bar-widget](contrib/bar-widget/))
- **Multiple Models** — Choose from tiny, base, small, medium, large, large-v3, or turbo

## Requirements

### Hardware
- **GPU**: AMD GPU with ROCm support (RDNA2/RDNA3 recommended)
  - Tested on: RX 7800XT (16GB VRAM)
  - Minimum ~6GB VRAM for large-v3, ~2GB for medium
- **Audio**: Working microphone

### Software
- **OS**: Arch Linux (or derivatives)
- **Display**: Wayland compositor (Hyprland, Sway, etc.)
- **Python**: 3.10 or higher

### System Dependencies

```bash
# Install required system packages
sudo pacman -S python python-pip portaudio wtype

# Add yourself to the input group (for F13 hotkey capture)
sudo usermod -aG input $USER

# Log out and back in for group changes to take effect
```

> [!IMPORTANT]
> You **must** log out and back in after adding yourself to the `input` group.

## Installation

### Step 1: Install PyTorch with ROCm

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm6.3
```

> [!NOTE]
> Do not use system PyTorch. You must install from the ROCm-specific index.

### Step 2: Install whisper-stt

```bash
pip install git+https://github.com/caioniehues/whisper-stt.git
```

Or for development:

```bash
git clone https://github.com/caioniehues/whisper-stt.git
cd whisper-stt
pip install -e .
```

### Step 3: (Optional) HuggingFace Login for Speaker Diarization

Meeting transcription requires pyannote.audio models:

```bash
# Create account at https://huggingface.co
# Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
huggingface-cli login
```

## Quick Start

### Real-time Dictation

```bash
# Start the transcriber (foreground)
stt

# Press F13 to start recording
# Press F13 again to stop and transcribe
# Text is automatically typed into the focused window
```

### Transcribe a Meeting

```bash
# Transcribe with speaker identification
stt transcribe meeting.mp3

# Output: Meeting_Transcript_2024-01-15.md
```

## Usage

### Real-time Dictation

The default mode captures audio when F13 is pressed and types the transcription into your active window.

```bash
# Foreground mode (Ctrl+C to exit)
stt

# Background daemon
stt daemon

# With system tray icon
stt tray

# Use a different model
stt -m medium

# Use a different language
stt -l pt
```

**Available models** (speed vs accuracy trade-off):
| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1GB | Fastest | Low |
| base | ~1GB | Fast | Basic |
| small | ~2GB | Moderate | Good |
| medium | ~5GB | Slow | Better |
| large-v3 | ~6GB | Slower | Best |
| turbo | ~6GB | Fast | Best |

### Meeting Transcription

Transcribe audio files with automatic speaker identification:

```bash
# Single file
stt transcribe recording.mp3

# Multiple files
stt transcribe *.mp3

# Specify output directory
stt transcribe -o ./transcripts meeting.mp3

# Specify number of speakers (auto-detect if omitted)
stt transcribe -s 3 meeting.mp3

# Use GUI (drag-and-drop)
stt gui
```

**Output format** (Markdown):
```markdown
# Meeting Title

**Date:** 2024-01-15
**Duration:** 00:45:30
**Speakers:** 3 detected

---

[00:00:15] **Speaker 1:**
Welcome everyone to today's meeting...

[00:00:45] **Speaker 2:**
Thanks for having me...
```

### Service Management

```bash
# Check if daemon is running
stt status

# Stop running daemon
stt stop

# Toggle daemon on/off
stt toggle
```

## Desktop Integration

### Waybar Module

Add to your Waybar config (`~/.config/waybar/config`):

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

Copy the script:
```bash
mkdir -p ~/.config/waybar/scripts
cp contrib/waybar/stt-status.py ~/.config/waybar/scripts/
chmod +x ~/.config/waybar/scripts/stt-status.py
```

See [contrib/waybar/README.md](contrib/waybar/README.md) for styling options.

### React Bar Widget

A modern React-based widget with LED segment display and hardware-inspired aesthetics:

```bash
cd contrib/bar-widget
pnpm install
pnpm dev
```

See [contrib/bar-widget/README.md](contrib/bar-widget/README.md) for integration details.

## Configuration

### Model Selection

Set your preferred model at startup:

```bash
# Use turbo (large-v3 optimized) - recommended
stt -m turbo

# Use medium for lower VRAM usage
stt -m medium
```

### Language

```bash
# English (default)
stt -l en

# Portuguese
stt -l pt

# Spanish
stt -l es
```

### Status File Location

The daemon writes status to:
```
$XDG_RUNTIME_DIR/whisper-stt/status.json
```

Typically: `/run/user/1000/whisper-stt/status.json`

## Troubleshooting

<details>
<summary><strong>F13 key not detected</strong></summary>

1. Ensure you're in the `input` group:
   ```bash
   groups | grep input
   ```

2. If not, add yourself and **log out/in**:
   ```bash
   sudo usermod -aG input $USER
   ```

3. Check if your keyboard has F13 (some require Fn key or custom firmware)

</details>

<details>
<summary><strong>wtype: permission denied</strong></summary>

Your Wayland compositor must support the virtual keyboard protocol. This works on:
- Hyprland
- Sway
- Other wlroots-based compositors

It does **not** work on GNOME or KDE Wayland.

</details>

<details>
<summary><strong>Model download appears stuck</strong></summary>

First run downloads the Whisper model (~3GB for large-v3). This is normal and may take several minutes depending on your connection.

</details>

<details>
<summary><strong>Out of VRAM error</strong></summary>

The application automatically falls back to the `medium` model if VRAM is insufficient. You can also explicitly use a smaller model:

```bash
stt -m small
```

</details>

<details>
<summary><strong>Speaker diarization not working</strong></summary>

1. Log in to HuggingFace:
   ```bash
   huggingface-cli login
   ```

2. Accept model terms at:
   https://huggingface.co/pyannote/speaker-diarization-3.1

</details>

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with Whisper, pyannote.audio, and AMD ROCm
</p>
