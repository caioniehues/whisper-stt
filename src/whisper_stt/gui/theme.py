"""
Sound Studio theme for Whisper STT GUI.

A professional audio production aesthetic with warm amber accents,
deep charcoal backgrounds, and visual elements inspired by studio equipment.
"""

# Color Palette - Sound Studio
COLORS = {
    # Backgrounds
    "bg_primary": "#0d0d0f",       # Near black
    "bg_secondary": "#151518",     # Dark charcoal
    "bg_elevated": "#1c1c21",      # Elevated surfaces
    "bg_hover": "#252529",         # Hover states

    # Accents - Warm amber (VU meter inspired)
    "accent_primary": "#f59e0b",   # Amber gold
    "accent_glow": "#fbbf24",      # Lighter amber for glow
    "accent_dim": "#b45309",       # Dimmed amber

    # Secondary accent - Cyan (LED indicator)
    "accent_secondary": "#06b6d4", # Cyan
    "accent_secondary_dim": "#0891b2",

    # Text
    "text_primary": "#fafafa",     # Pure white
    "text_secondary": "#a1a1aa",   # Zinc gray
    "text_muted": "#71717a",       # Muted

    # Borders & Dividers
    "border": "#27272a",           # Subtle border
    "border_focus": "#f59e0b",     # Focus state

    # Status
    "success": "#22c55e",          # Green
    "error": "#ef4444",            # Red
    "warning": "#f59e0b",          # Amber

    # Waveform colors
    "waveform_bar": "#3f3f46",     # Inactive bars
    "waveform_active": "#f59e0b",  # Active bars
}

# Typography
FONTS = {
    "heading": "'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace",
    "body": "'Inter', 'SF Pro Display', -apple-system, sans-serif",
    "mono": "'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace",
}

# Shared Styles
GLOBAL_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-family: {FONTS['body']};
    }}

    QLabel {{
        color: {COLORS['text_primary']};
    }}

    QPushButton {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 13px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['accent_primary']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['accent_dim']};
    }}

    QScrollBar:vertical {{
        border: none;
        background: {COLORS['bg_secondary']};
        width: 8px;
        margin: 0;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        min-height: 30px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLORS['accent_primary']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QTextEdit {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        color: {COLORS['text_primary']};
        padding: 16px;
        font-family: {FONTS['mono']};
        font-size: 13px;
        line-height: 1.6;
        selection-background-color: {COLORS['accent_primary']};
        selection-color: {COLORS['bg_primary']};
    }}

    QTextEdit:focus {{
        border-color: {COLORS['accent_primary']};
    }}
"""

# Button Variants
def primary_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: {COLORS['accent_primary']};
            color: {COLORS['bg_primary']};
            border: none;
            border-radius: 6px;
            padding: 12px 28px;
            font-weight: 700;
            font-size: 14px;
            font-family: {FONTS['heading']};
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_glow']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['accent_dim']};
        }}
    """

def secondary_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 13px;
        }}
        QPushButton:hover {{
            color: {COLORS['text_primary']};
            border-color: {COLORS['text_secondary']};
        }}
    """

def danger_button_style() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['error']};
            border: 1px solid {COLORS['error']};
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {COLORS['error']};
            color: {COLORS['bg_primary']};
        }}
    """
