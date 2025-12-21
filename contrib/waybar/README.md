# Waybar Integration

## Setup

1. Copy `stt-status.py` to your scripts directory:
```bash
cp stt-status.py ~/.config/waybar/scripts/
chmod +x ~/.config/waybar/scripts/stt-status.py
```

2. Add to your waybar config (`~/.config/waybar/config`):
```json
"custom/stt": {
    "exec": "~/.config/waybar/scripts/stt-status.py",
    "return-type": "json",
    "interval": 1,
    "on-click": "stt toggle"
}
```

3. Add to your modules:
```json
"modules-right": ["custom/stt", ...]
```

4. Add styling (`~/.config/waybar/style.css`):
```css
#custom-stt {
    padding: 0 10px;
    color: #6c7086;
}

#custom-stt.recording {
    color: #f38ba8;
    animation: pulse 1s ease-in-out infinite;
}

#custom-stt.ready {
    color: #a6e3a1;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

## Icons

- 󰍬 = microphone (recording)
- 󰍭 = microphone-off (ready/idle)

Requires a Nerd Font for icons.
