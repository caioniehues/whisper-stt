"""
VU Meter-style progress widget for transcription status.
Inspired by professional audio equipment with LED-style indicators.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal, QTimer, QTime, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

from whisper_stt.gui.theme import COLORS, FONTS, danger_button_style


class VUMeterWidget(QWidget):
    """
    VU Meter-style progress indicator with LED segments.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._value = 0.0
        self._segments = 40
        self._glow_intensity = 0.0

        # Pulsing glow animation
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._update_glow)
        self._glow_direction = 1

    def _get_value(self) -> float:
        return self._value

    def _set_value(self, val: float):
        self._value = max(0.0, min(1.0, val))
        self.update()

    value = Property(float, _get_value, _set_value)

    def start_glow(self):
        self._glow_timer.start(50)

    def stop_glow(self):
        self._glow_timer.stop()
        self._glow_intensity = 0.0

    def _update_glow(self):
        self._glow_intensity += 0.05 * self._glow_direction
        if self._glow_intensity >= 1.0:
            self._glow_direction = -1
        elif self._glow_intensity <= 0.3:
            self._glow_direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        segment_width = (width - (self._segments - 1) * 2) / self._segments
        active_segments = int(self._value * self._segments)

        for i in range(self._segments):
            x = i * (segment_width + 2)
            is_active = i < active_segments

            # Color gradient: green -> yellow -> amber -> red
            if i < self._segments * 0.6:
                # Green zone
                base_color = QColor(COLORS["success"])
            elif i < self._segments * 0.8:
                # Yellow/amber zone
                base_color = QColor(COLORS["accent_primary"])
            else:
                # Red zone (peak)
                base_color = QColor(COLORS["error"])

            if is_active:
                # Active segment with glow
                color = base_color
                if self._glow_intensity > 0:
                    color = color.lighter(100 + int(20 * self._glow_intensity))
            else:
                # Inactive segment - dim version
                color = QColor(COLORS["bg_hover"])

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(int(x), 0, int(segment_width), height, 2, 2)


class StageIndicator(QFrame):
    """Shows the current processing stage with LED-style dots."""

    STAGES = [
        ("LOAD", "Loading models"),
        ("TRANSCRIBE", "Transcribing audio"),
        ("DIARIZE", "Identifying speakers"),
        ("MERGE", "Merging results"),
        ("OUTPUT", "Generating output"),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_stage = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stage_labels = []

        for i, (code, _) in enumerate(self.STAGES):
            stage_widget = QWidget()
            stage_layout = QHBoxLayout(stage_widget)
            stage_layout.setSpacing(8)
            stage_layout.setContentsMargins(0, 0, 0, 0)

            # LED indicator dot
            led = QLabel("●")
            led.setStyleSheet(f"color: {COLORS['bg_hover']}; font-size: 10px;")
            led.setObjectName(f"led_{i}")

            # Stage code
            label = QLabel(code)
            label.setStyleSheet(f"""
                font-family: {FONTS['mono']};
                font-size: 11px;
                font-weight: 600;
                color: {COLORS['text_muted']};
                letter-spacing: 1px;
            """)
            label.setObjectName(f"label_{i}")

            stage_layout.addWidget(led)
            stage_layout.addWidget(label)

            layout.addWidget(stage_widget)
            self._stage_labels.append((led, label))

        layout.addStretch()

    def set_stage(self, progress: float):
        """Set the current stage based on progress (0.0 to 1.0)."""
        if progress < 0.1:
            stage = 0
        elif progress < 0.5:
            stage = 1
        elif progress < 0.8:
            stage = 2
        elif progress < 0.9:
            stage = 3
        else:
            stage = 4

        for i, (led, label) in enumerate(self._stage_labels):
            if i < stage:
                # Completed
                led.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px;")
                label.setStyleSheet(f"""
                    font-family: {FONTS['mono']};
                    font-size: 11px;
                    font-weight: 600;
                    color: {COLORS['text_secondary']};
                    letter-spacing: 1px;
                """)
            elif i == stage:
                # Current - active/glowing
                led.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 10px;")
                label.setStyleSheet(f"""
                    font-family: {FONTS['mono']};
                    font-size: 11px;
                    font-weight: 600;
                    color: {COLORS['accent_primary']};
                    letter-spacing: 1px;
                """)
            else:
                # Pending
                led.setStyleSheet(f"color: {COLORS['bg_hover']}; font-size: 10px;")
                label.setStyleSheet(f"""
                    font-family: {FONTS['mono']};
                    font-size: 11px;
                    font-weight: 600;
                    color: {COLORS['text_muted']};
                    letter-spacing: 1px;
                """)


class ProgressWidget(QWidget):
    """
    VU Meter-style progress widget with stage indicators.
    """

    cancelRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProgressWidget")

        self._start_time = QTime.currentTime()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timer)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(32)
        layout.setContentsMargins(0, 40, 0, 40)

        # File being processed
        self.filename_label = QLabel("audio.mp3")
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 14px;
            color: {COLORS['text_secondary']};
            padding: 12px 24px;
            background-color: {COLORS['bg_secondary']};
            border-radius: 8px;
        """)
        layout.addWidget(self.filename_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Stage indicators
        self.stage_indicator = StageIndicator()
        layout.addWidget(self.stage_indicator, alignment=Qt.AlignmentFlag.AlignCenter)

        # VU Meter progress bar
        meter_container = QWidget()
        meter_layout = QVBoxLayout(meter_container)
        meter_layout.setSpacing(12)
        meter_layout.setContentsMargins(0, 0, 0, 0)

        self.vu_meter = VUMeterWidget()
        meter_layout.addWidget(self.vu_meter)

        # Progress info row
        info_layout = QHBoxLayout()

        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 24px;
            font-weight: 300;
            color: {COLORS['text_primary']};
            letter-spacing: 2px;
        """)

        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 24px;
            font-weight: 700;
            color: {COLORS['accent_primary']};
        """)

        info_layout.addWidget(self.timer_label)
        info_layout.addStretch()
        info_layout.addWidget(self.percent_label)
        meter_layout.addLayout(info_layout)

        layout.addWidget(meter_container)

        # Status message
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            font-size: 15px;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.setStyleSheet(danger_button_style())
        self.cancel_btn.clicked.connect(self.cancelRequested.emit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def start(self):
        """Reset and start the timer."""
        self._start_time = QTime.currentTime()
        self._timer.start(1000)
        self.vu_meter._set_value(0)
        self.vu_meter.start_glow()
        self.status_label.setText("Starting...")
        self.percent_label.setText("0%")
        self.timer_label.setText("00:00")
        self.stage_indicator.set_stage(0)

    def set_filename(self, name: str):
        """Set the filename being processed."""
        self.filename_label.setText(name)

    def stop(self):
        """Stop the timer."""
        self._timer.stop()
        self.vu_meter.stop_glow()

    def update_progress(self, status: str, value: float):
        """Update progress bar and status label."""
        self.status_label.setText(status)
        percent = int(value * 100)
        self.vu_meter._set_value(value)
        self.percent_label.setText(f"{percent}%")
        self.stage_indicator.set_stage(value)

    def _update_timer(self):
        elapsed = self._start_time.secsTo(QTime.currentTime())
        mins = elapsed // 60
        secs = elapsed % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
