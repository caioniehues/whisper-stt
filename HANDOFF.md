# Handoff Document: Bar Module UI Implementation

> **Created:** 2025-12-21
> **Branch:** `feature/bar-module-ui`
> **Status:** Core implementation complete, ready for testing and integration

---

## Project Context

**whisper-stt** is a dual-mode speech-to-text application for AMD ROCm on Arch Linux/Wayland:
1. **Real-time Mode**: Push-to-talk (F13 key) with live transcription via wtype
2. **Meeting Mode**: File-based transcription with speaker diarization

The user requested a rich bar module UI for integration with Hyprland/Wayland bars, specifically wanting:
- Recording duration timer display
- Visual status indicators
- Click-to-toggle recording
- Dropdown menu for service control
- shadcn components with their existing "Sound Studio" theme

---

## What Was Built

### React Widget (`contrib/bar-widget/`)

A professional **audio hardware-inspired** React widget featuring:

| Feature | Implementation |
|---------|---------------|
| Duration Timer | LED segment display showing `MM:SS` when recording |
| Status LED | Colored indicator: red (recording), green (ready), gray (stopped) |
| Toggle Recording | Click main area to start/stop recording |
| Dropdown Menu | Service control (start/stop), model selection (tiny→turbo) |
| Theme | Sound Studio: dark charcoal (#0d0d0f) + amber accent (#f59e0b) |
| Accessibility | ARIA labels, screen reader text, keyboard navigation |

**Tech Stack:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- shadcn/ui (Button, DropdownMenu)
- Radix UI primitives

### Backend Enhancement

Modified `src/whisper_stt/service/daemon.py` to include `recording_start_time` in the status JSON, enabling accurate duration display:

```python
# Status JSON now includes:
{
    "recording": bool,
    "model": str,
    "pid": int,
    "recording_start_time": float | None  # NEW: Unix timestamp when recording started
}
```

---

## File Structure

```
contrib/bar-widget/
├── package.json              # Dependencies (React, Radix, Tailwind)
├── vite.config.ts            # Build config + mock API plugin
├── tailwind.config.js        # Sound Studio theme colors
├── components.json           # shadcn configuration
├── index.html                # Entry HTML (transparent bg for embedding)
├── README.md                 # Integration documentation
├── tsconfig.json
├── tsconfig.node.json
├── postcss.config.js
└── src/
    ├── main.tsx              # React entry point
    ├── App.tsx               # Main app with action handlers
    ├── index.css             # Global styles + CSS animations
    ├── lib/utils.ts          # cn() helper, duration formatting
    ├── hooks/useStatus.ts    # Status polling + duration calculation
    ├── vite-plugin-mock-api.ts  # Dev server mock endpoints
    └── components/
        ├── BarWidget.tsx     # Main widget (StatusLED, SegmentDisplay)
        └── ui/
            ├── button.tsx    # shadcn Button
            └── dropdown-menu.tsx  # shadcn DropdownMenu
```

---

## Key Design Decisions

### 1. Client-Side Duration Fallback
The widget tracks recording duration client-side as a fallback when the backend doesn't provide `recording_start_time`. This ensures the timer works during development and handles edge cases.

```typescript
// hooks/useStatus.ts
const clientStartTimeRef = useRef<number | null>(null)
// Detects recording state transitions and captures start time
```

### 2. Architecture Choice: Clean Over Minimal
User chose the **extensible architecture** approach over minimal changes, anticipating future bar integrations (EWW, AGS). The widget is self-contained in `contrib/bar-widget/` with clear abstractions.

### 3. Mock API for Development
A Vite plugin provides mock endpoints during development:
- `GET /api/status` - Returns mock status JSON
- `POST /api/command/{action}` - Handles toggle-recording, start, stop, change-model

---

## Issues Found & Fixed

During code review, these issues were identified and resolved:

| Issue | Fix |
|-------|-----|
| Missing `recording_start_time` in backend | Added to `daemon.py` with timestamp tracking |
| CSS screw positioning (absolute without relative parent) | Added `relative` class to parent div |
| Model selection state not syncing | Added `useEffect` to sync when status updates |
| Missing ARIA labels on buttons | Added `aria-label` attributes |
| StatusLED not accessible | Added `role="status"` and `sr-only` text |
| Type mismatch in Tauri interface | Changed to `Record<string, unknown>` |

---

## Current State

### What Works
- ✅ Widget renders with full styling
- ✅ Mock API responds to all actions
- ✅ Duration timer counts up when recording
- ✅ Status LED changes color based on state
- ✅ Dropdown menu shows all options
- ✅ Python backend writes `recording_start_time`

### What Needs Testing
- ⏳ Integration with actual STT daemon
- ⏳ Build output (`pnpm build`) verification
- ⏳ Embedding in AGS/Tauri/WebView
- ⏳ Production file:// protocol status reading

### Known Limitations
- Widget currently runs as standalone web app (needs wrapper for bar embedding)
- No actual IPC with Python backend yet (uses mock in dev, placeholder in prod)
- Model changes in menu don't restart daemon (just updates state)

---

## Next Steps

### Immediate (To Complete Feature)

1. **Test with real daemon:**
   ```bash
   stt daemon -m turbo  # Start daemon
   cd contrib/bar-widget && pnpm dev  # Start widget
   # Verify status updates propagate
   ```

2. **Implement production IPC:**
   - Option A: Tauri wrapper (recommended for standalone widget)
   - Option B: Local Python server that proxies to `stt` CLI
   - Option C: AGS integration with `Utils.exec()` calls

3. **Add toggle-recording CLI command:**
   The original architecture planned a `stt toggle-recording` command using SIGUSR1. This was designed but not implemented in `cli.py`.

### Future Enhancements

- EWW integration (Lisp formatter)
- AGS native integration (TypeScript module)
- System tray fallback when bar unavailable
- Keyboard shortcut support in widget
- VU meter animation when recording (stretch goal)

---

## How to Continue

### Setup
```bash
cd /home/caio/Developer/whisper-stt
git checkout feature/bar-module-ui

# Install widget dependencies
cd contrib/bar-widget
pnpm install

# Run development server
pnpm dev  # Opens http://localhost:3847
```

### Key Files to Understand
1. `contrib/bar-widget/src/components/BarWidget.tsx` - Main UI component
2. `contrib/bar-widget/src/hooks/useStatus.ts` - Status polling logic
3. `src/whisper_stt/service/daemon.py` - Backend status writing
4. `contrib/bar-widget/README.md` - Integration options

### Testing Commands
```bash
# Check Python backend
stt daemon -m turbo &
cat $XDG_RUNTIME_DIR/whisper-stt/status.json

# Build widget
cd contrib/bar-widget
pnpm build
ls dist/
```

---

## Reference: Status JSON Schema

```typescript
interface STTStatus {
  recording: boolean           // Is currently recording
  model: string               // "tiny" | "base" | "small" | "medium" | "large" | "large-v3" | "turbo"
  pid: number | null          // Daemon process ID (null if not running)
  running?: boolean           // Optional: explicit running state
  recording_start_time?: number | null  // Unix timestamp when recording started
}
```

**Location:** `$XDG_RUNTIME_DIR/whisper-stt/status.json`

---

## Git History

```
08faebd feat: add rich bar widget UI with shadcn components  <- Current HEAD
c6f3a12 Initial commit: whisper-stt project
```

To merge into master when ready:
```bash
git checkout master
git merge feature/bar-module-ui
```
