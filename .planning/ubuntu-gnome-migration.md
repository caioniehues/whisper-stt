# Migration Plan: Arch Linux/Waybar → Ubuntu/GNOME

## Overview

Migrate whisper-stt from Arch Linux with Wayland/Waybar to Ubuntu with GNOME. This is a **complete replacement** - all Arch/Waybar-specific code will be removed.

## User Decisions

| Component | Decision |
|-----------|----------|
| Text Injection | Keep wtype only (build from source on Ubuntu) |
| System Tray | AppIndicator3 (libayatana-appindicator3) |
| Status Widget | GNOME Shell extension (replaces Waybar) |
| Platform Scope | Complete replacement (remove Arch/Waybar code) |

---

## Phase 1: Text Injection Updates

**File:** `src/whisper_stt/typing.py`

Update error messages from Arch to Ubuntu:

- [ ] Line 38-42: Update `_find_wtype()` error message
  ```python
  # From: "Arch Linux: sudo pacman -S wtype"
  # To:   "Ubuntu: sudo apt install wtype"
  ```
- [ ] Line 147: Update `check_environment()` error message
- [ ] Lines 17-20: Update class docstring (remove Hyprland/Sway references)

---

## Phase 2: System Tray Rewrite

**File:** `src/whisper_stt/tray.py` (complete rewrite)

Replace PySide6 QSystemTrayIcon with GTK/AppIndicator3:

- [ ] Remove PySide6 imports, add PyGObject imports
- [ ] Replace `QSystemTrayIcon` with `AyatanaAppIndicator3.Indicator`
- [ ] Replace `QTimer` with `GLib.timeout_add()`
- [ ] Replace `QMenu/QAction` with `Gtk.Menu/Gtk.MenuItem`
- [ ] Add model selection submenu (radio buttons)
- [ ] Add "Open Meeting Mode" menu item
- [ ] Replace `QApplication.exec()` with `Gtk.main()`

**Ubuntu Dependencies:**
```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1 libayatana-appindicator3-1
```

---

## Phase 3: GNOME Shell Extension

**New Directory:** `contrib/gnome-shell-extension/`

Create native GNOME panel indicator:

- [ ] `metadata.json` - Extension metadata (GNOME 45-48 support)
- [ ] `extension.js` - Main extension code:
  - Panel button with microphone icon
  - Status polling from `$XDG_RUNTIME_DIR/whisper-stt/status.json`
  - Recording duration display (MM:SS)
  - Color-coded states (red=recording, green=ready, gray=stopped)
  - Dropdown menu: toggle service, model selection, open GUI
- [ ] `stylesheet.css` - Styling (amber accents, pulse animation)
- [ ] `schemas/org.gnome.shell.extensions.whisper-stt.gschema.xml`
- [ ] `README.md` - Installation instructions

---

## Phase 4: Delete Arch/Waybar Code

Remove obsolete files:

- [ ] Delete `contrib/waybar/` (entire directory)
  - `stt-status.py` (177 lines)
  - `style.css` (92 lines)
- [ ] Delete `contrib/bar-widget/` (entire directory - React widget)
- [ ] Delete `HANDOFF.md` (documents obsolete Waybar implementation)

---

## Phase 5: Documentation Updates

### README.md
- [ ] Update badges: Arch→Ubuntu, Wayland→GNOME
- [ ] Update tagline: "optimized for AMD ROCm on Ubuntu with GNOME"
- [ ] Update requirements: Ubuntu 22.04+, GNOME
- [ ] Update system dependencies: `apt` commands instead of `pacman`
- [ ] Replace Waybar section with GNOME Shell Extension section
- [ ] Update troubleshooting for GNOME

### CLAUDE.md
- [ ] Update target environment (Ubuntu/GNOME)
- [ ] Update project structure (remove waybar/bar-widget, add gnome-shell-extension)
- [ ] Update Wayland integration section
- [ ] Update contrib modules documentation

### SPEC.md
- [ ] Update target environment
- [ ] Update visual feedback section
- [ ] Update installation steps
- [ ] Update constraints (GNOME instead of wlroots)

### CONTRIBUTING.md
- [ ] Update prerequisites (Ubuntu 22.04+)
- [ ] Update installation commands
- [ ] Update project structure

### pyproject.toml
- [ ] Update description
- [ ] Update keywords: remove "wayland", add "gnome", "ubuntu"

---

## Phase 6: CLI Updates (Minor)

**File:** `src/whisper_stt/cli.py`

- [ ] Update description string (~line 159)

---

## Implementation Order

1. **typing.py** - Simple string replacements (5 min)
2. **tray.py** - Complete rewrite to GTK/AppIndicator (30 min)
3. **GNOME Shell Extension** - New code (60 min)
4. **Delete Arch/Waybar code** - File deletions (5 min)
5. **Documentation** - Update all docs (45 min)
6. **CLI** - Minor string updates (5 min)

---

## Critical Files

| File | Action |
|------|--------|
| `src/whisper_stt/tray.py` | Complete rewrite (Qt → GTK) |
| `src/whisper_stt/typing.py` | Update error messages |
| `README.md` | Major documentation update |
| `CLAUDE.md` | Developer docs update |
| `contrib/gnome-shell-extension/extension.js` | New file (core extension) |

---

## Testing Checklist

### Text Injection
- [ ] Verify wtype available on Ubuntu: `apt install wtype`
- [ ] Test wtype works on GNOME Wayland
- [ ] Test error messages display correctly

### System Tray
- [ ] Install AppIndicator dependencies
- [ ] Run `stt tray`, verify icon appears
- [ ] Test menu items and model switching

### GNOME Shell Extension
- [ ] Install to `~/.local/share/gnome-shell/extensions/`
- [ ] Enable and verify panel indicator
- [ ] Test status polling and duration display
- [ ] Test on GNOME 45, 46, 47, 48

### Core Functionality
- [ ] F13 hotkey capture still works
- [ ] Transcription pipeline unchanged
- [ ] Meeting mode GUI works (`stt gui`)
- [ ] All CLI commands functional

---

## Potential Issues

| Issue | Mitigation |
|-------|------------|
| wtype on GNOME Wayland | Test first; may need X11 fallback or ydotool |
| AppIndicator requires extension | Document users need "AppIndicator Support" GNOME extension |
| GNOME Shell API changes | Test on multiple versions, use stable APIs |
| ROCm on Ubuntu | Document Ubuntu-specific installation steps |

---

## Notes

- Core transcription engine (`transcriber.py`, `diarization.py`, `meeting.py`) remains **unchanged**
- Hotkey mechanism (`hotkey.py`) uses evdev - works on any Linux, **no changes needed**
- Daemon architecture (`service/daemon.py`) is platform-agnostic, **no changes needed**
- Meeting Mode GUI (PySide6) works on both platforms, **no changes needed**
