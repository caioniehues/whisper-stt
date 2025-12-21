"""
File picker widget with animated waveform visualization.
Sound Studio aesthetic with drag-and-drop support.
"""

import random
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QPen, QLinearGradient
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QFileDialog, QWidget

from whisper_stt.gui.theme import COLORS, FONTS


class WaveformWidget(QWidget):
    """Animated waveform visualization widget."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self._bars = 48
        self._bar_values = [random.uniform(0.2, 0.8) for _ in range(self._bars)]
        self._target_values = self._bar_values.copy()
        self._is_active = False
        self._hover_intensity = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def _get_hover_intensity(self) -> float:
        return self._hover_intensity

    def _set_hover_intensity(self, value: float):
        self._hover_intensity = value
        self.update()

    hover_intensity = Property(float, _get_hover_intensity, _set_hover_intensity)

    def set_active(self, active: bool):
        self._is_active = active

    def _animate(self):
        # Generate new targets occasionally
        for i in range(self._bars):
            if random.random() < 0.15:
                if self._is_active:
                    self._target_values[i] = random.uniform(0.4, 1.0)
                else:
                    self._target_values[i] = random.uniform(0.15, 0.5)

            # Smooth interpolation
            self._bar_values[i] += (self._target_values[i] - self._bar_values[i]) * 0.2

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        bar_width = max(2, (width / self._bars) * 0.6)
        spacing = width / self._bars

        # Colors based on state
        if self._is_active or self._hover_intensity > 0:
            base_color = QColor(COLORS["accent_primary"])
            base_color.setAlphaF(0.3 + 0.7 * max(self._hover_intensity, 1.0 if self._is_active else 0))
        else:
            base_color = QColor(COLORS["waveform_bar"])

        for i, value in enumerate(self._bar_values):
            x = i * spacing + (spacing - bar_width) / 2
            bar_height = value * height * 0.8

            # Create gradient for each bar
            gradient = QLinearGradient(0, height / 2 - bar_height / 2, 0, height / 2 + bar_height / 2)

            if self._is_active:
                gradient.setColorAt(0, QColor(COLORS["accent_glow"]))
                gradient.setColorAt(0.5, QColor(COLORS["accent_primary"]))
                gradient.setColorAt(1, QColor(COLORS["accent_dim"]))
            elif self._hover_intensity > 0:
                color = QColor(COLORS["accent_primary"])
                color.setAlphaF(self._hover_intensity * 0.8)
                gradient.setColorAt(0, color.lighter(120))
                gradient.setColorAt(1, color)
            else:
                gradient.setColorAt(0, base_color.lighter(110))
                gradient.setColorAt(1, base_color)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)

            # Draw bar centered vertically with rounded caps
            y = (height - bar_height) / 2
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), bar_width / 2, bar_width / 2)


class FilePickerWidget(QFrame):
    """
    Modern file picker with animated waveform visualization.

    Features:
    - Animated waveform background
    - Drag and drop support
    - Click to browse
    - Smooth hover transitions
    """

    fileSelected = Signal(Path)

    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mp4'}

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("FilePicker")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(280)

        self._setup_ui()
        self._setup_animations()
        self._apply_style(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 40, 40, 40)

        # Waveform visualization
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)

        # Icon
        self.icon_label = QLabel("⎙")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(f"""
            font-size: 36px;
            color: {COLORS['accent_primary']};
        """)
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel("Drop Audio File")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            font-family: {FONTS['heading']};
            color: {COLORS['text_primary']};
            letter-spacing: -0.5px;
        """)
        layout.addWidget(self.title_label)

        # Subtitle
        self.subtitle_label = QLabel("or click to browse")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_muted']};
        """)
        layout.addWidget(self.subtitle_label)

        # Supported formats
        self.formats_label = QLabel("MP3 · WAV · M4A · FLAC · OGG · MP4")
        self.formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formats_label.setStyleSheet(f"""
            font-size: 11px;
            font-family: {FONTS['mono']};
            color: {COLORS['text_muted']};
            letter-spacing: 1px;
            margin-top: 8px;
        """)
        layout.addWidget(self.formats_label)

    def _setup_animations(self):
        self._hover_anim = QPropertyAnimation(self.waveform, b"hover_intensity")
        self._hover_anim.setDuration(300)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _apply_style(self, is_active: bool):
        if is_active:
            border_color = COLORS['accent_primary']
            bg_color = COLORS['bg_elevated']
            glow = f"0 0 30px {COLORS['accent_primary']}40"
        else:
            border_color = COLORS['border']
            bg_color = COLORS['bg_secondary']
            glow = "none"

        self.setStyleSheet(f"""
            #FilePicker {{
                background-color: {bg_color};
                border: 2px dashed {border_color};
                border-radius: 16px;
            }}
        """)

    def enterEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self.waveform.hover_intensity)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self.waveform.hover_intensity)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        self._apply_style(False)
        super().leaveEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = Path(urls[0].toLocalFile())
                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self.waveform.set_active(True)
                    self._apply_style(True)
                    self.icon_label.setText("↓")
                    self.title_label.setText("Release to Transcribe")
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.waveform.set_active(False)
        self._apply_style(False)
        self.icon_label.setText("⎙")
        self.title_label.setText("Drop Audio File")
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.waveform.set_active(False)
        self._apply_style(False)
        self.icon_label.setText("⎙")
        self.title_label.setText("Drop Audio File")

        urls = event.mimeData().urls()
        if urls:
            file_path = Path(urls[0].toLocalFile())
            self.fileSelected.emit(file_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()

    def _open_file_dialog(self):
        file_filter = "Audio/Video Files (*.mp3 *.wav *.m4a *.flac *.ogg *.webm *.mp4)"
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            str(Path.home()),
            file_filter
        )
        if path:
            self.fileSelected.emit(Path(path))
