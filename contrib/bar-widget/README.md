# Whisper STT Bar Widget

A professional audio hardware-inspired widget for controlling Whisper STT from Hyprland/Wayland bars.

![Sound Studio Theme](https://img.shields.io/badge/theme-Sound%20Studio-f59e0b)
![React](https://img.shields.io/badge/React-18.3-61dafb)
![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-components-000)

## Features

- **LED Segment Display**: Recording duration shown in vintage audio equipment style
- **Status LED Indicators**: Visual feedback for recording/ready/stopped states
- **Hardware Panel Aesthetic**: Professional studio equipment-inspired design
- **Dropdown Menu**: Quick access to service controls and model selection
- **Compact Design**: Optimized for bar integration

## Screenshots

```
┌─────────────────────────────────────┐
│ ● 󰍬 [02:45] STT ▾                   │  <- Recording (red LED, timer active)
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ● 󰍭 [--:--] turbo ▾                 │  <- Ready (green LED)
└─────────────────────────────────────┘
```

## Installation

### Prerequisites

- Node.js 18+
- pnpm (recommended) or npm

### Setup

```bash
cd contrib/bar-widget
pnpm install
```

### Development

```bash
pnpm dev
```

Opens at http://localhost:3847 with a mock API that simulates the STT service.

### Build

```bash
pnpm build
```

Outputs to `dist/` directory.

## Integration

### AGS (Aylur's GTK Shell)

AGS supports embedding web views. Add the widget as a WebView in your AGS config:

```typescript
// ~/.config/ags/config.js
import Widget from 'resource:///com/github/Aylur/ags/widget.js';

const SttWidget = () => Widget.Box({
  className: 'stt-widget',
  child: Widget.WebView({
    url: 'file:///path/to/bar-widget/dist/index.html',
    hexpand: false,
    setup: self => {
      self.set_size_request(180, 40);
    },
  }),
});
```

### Waybar (WebKit module)

Waybar doesn't natively support web views, but you can use the custom module with this widget running as a local server:

```json
{
  "custom/stt": {
    "exec": "curl -s http://localhost:3847/api/status | jq -r '.recording as $r | .model as $m | if $r then \"🔴 REC\" else \"󰍭 \\($m)\" end'",
    "return-type": "json",
    "interval": 1,
    "on-click": "curl -X POST http://localhost:3847/api/command/toggle-recording",
    "on-click-right": "curl -X POST http://localhost:3847/api/command/stop"
  }
}
```

### Tauri (Standalone Widget)

For a native widget, wrap with Tauri:

```bash
pnpm add -D @tauri-apps/cli
pnpm tauri init
pnpm tauri build
```

### EWW (via GTK WebView)

Create a custom EWW widget:

```lisp
(defwidget stt []
  (box :class "stt-container"
    (literal :content '(webkit :url "file:///path/to/dist/index.html")')))
```

## Architecture

```
src/
├── components/
│   ├── BarWidget.tsx      # Main widget component
│   └── ui/                # shadcn components
│       ├── button.tsx
│       └── dropdown-menu.tsx
├── hooks/
│   └── useStatus.ts       # Status polling hook
├── lib/
│   └── utils.ts           # Utilities
├── App.tsx                # Application root
├── main.tsx               # Entry point
└── index.css              # Global styles + theme
```

## Theme Customization

The widget uses the Sound Studio theme from the main application. Colors are defined in `tailwind.config.js`:

```javascript
colors: {
  background: {
    DEFAULT: "#0d0d0f",    // Near black
    secondary: "#151518",  // Dark charcoal
    elevated: "#1c1c21",   // Elevated surfaces
  },
  accent: {
    DEFAULT: "#f59e0b",    // Amber gold (VU meter inspired)
    glow: "#fbbf24",       // Lighter amber
  },
  status: {
    success: "#22c55e",    // Green (ready)
    error: "#ef4444",      // Red (recording)
  },
}
```

## API Reference

### Status Endpoint

```
GET /api/status
```

Returns:
```json
{
  "recording": false,
  "model": "turbo",
  "pid": 12345,
  "recording_start_time": null
}
```

### Command Endpoints

```
POST /api/command/toggle-recording
POST /api/command/start          { "model": "turbo" }
POST /api/command/stop
POST /api/command/change-model   { "model": "medium" }
```

## Development

### Mock API

The development server includes a mock API that simulates the STT service. Actions are logged to the console and state is maintained in memory.

### Adding New Components

```bash
npx shadcn@latest add <component-name>
```

## License

MIT - Same as parent project.
