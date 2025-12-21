# Waybar Integration

Status bar module for whisper-stt with recording timer, model switching, and Sound Studio aesthetics.

## Features

- **Recording timer**: Shows elapsed time when recording (󰍬 02:34)
- **Status indicators**: Recording (amber), Ready (green), Stopped (gray)
- **Model cycling**: Scroll up/down to switch models
- **Model menu**: Right-click to open wofi/rofi model selector
- **Sound Studio theme**: Matches the bar-widget aesthetic

## Setup

### 1. Copy the script

```bash
mkdir -p ~/.config/waybar/scripts
cp stt-status.py ~/.config/waybar/scripts/
chmod +x ~/.config/waybar/scripts/stt-status.py
```

### 2. Add to waybar config

Add to `~/.config/waybar/config`:

```json
"custom/stt": {
    "exec": "~/.config/waybar/scripts/stt-status.py",
    "return-type": "json",
    "interval": 1,
    "on-click": "stt toggle",
    "on-click-right": "~/.config/waybar/scripts/stt-status.py --menu",
    "on-scroll-up": "~/.config/waybar/scripts/stt-status.py --next-model",
    "on-scroll-down": "~/.config/waybar/scripts/stt-status.py --prev-model"
}
```

Add to your modules array:

```json
"modules-right": ["custom/stt", ...]
```

### 3. Add styling

Option A: Copy the provided stylesheet:
```bash
cat style.css >> ~/.config/waybar/style.css
```

Option B: Import in your style.css:
```css
@import url("path/to/whisper-stt/contrib/waybar/style.css");
```

## Interactions

| Action | Behavior |
|--------|----------|
| Left-click | Toggle recording on/off |
| Right-click | Open model selector (wofi/rofi) |
| Scroll up | Cycle to next model |
| Scroll down | Cycle to previous model |

## Display States

| State | Display | Color |
|-------|---------|-------|
| Recording | 󰍬 02:34 | Amber (#f59e0b), pulsing |
| Ready | 󰍭 | Green (#22c55e) |
| Stopped | 󰍭 | Gray (#71717a), dimmed |

## Requirements

- **Nerd Font**: For microphone icons (󰍬 󰍭)
- **wofi or rofi**: For model selection menu (optional)
- **whisper-stt**: The `stt` command must be in PATH

## Troubleshooting

### Module shows nothing
- Check that `stt daemon` is running
- Verify status file exists: `cat $XDG_RUNTIME_DIR/whisper-stt/status.json`

### Icons don't render
- Install a Nerd Font (e.g., JetBrainsMono Nerd Font)
- Set the font in your waybar config or style.css

### Model menu doesn't appear
- Install wofi (`pacman -S wofi`) or rofi (`pacman -S rofi`)
