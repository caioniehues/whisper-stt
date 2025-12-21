"""
Main window for the Whisper STT GUI.
Sound Studio aesthetic with professional audio production vibes.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QTextEdit, QPushButton, QHBoxLayout, QLabel, QFileDialog, QMessageBox,
    QFrame
)
from PySide6.QtGui import QFont

from whisper_stt.gui.file_picker import FilePickerWidget
from whisper_stt.gui.progress import ProgressWidget
from whisper_stt.gui.theme import COLORS, FONTS, GLOBAL_STYLE, primary_button_style, secondary_button_style
from whisper_stt.meeting import MeetingTranscriber, TranscriptionResult


class TranscriptionWorker(QThread):
    """Worker thread for running transcription in the background."""

    progress = Signal(str, float)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, model_name: str, language: str, audio_path: Path):
        super().__init__()
        self.model_name = model_name
        self.language = language
        self.audio_path = audio_path
        self._is_cancelled = False

    def run(self):
        try:
            transcriber = MeetingTranscriber(
                model_name=self.model_name,
                language=self.language
            )

            def on_progress(step: str, val: float):
                if self._is_cancelled:
                    raise InterruptedError("Cancelled by user")
                self.progress.emit(step, val)

            result = transcriber.transcribe(
                self.audio_path,
                on_progress=on_progress
            )

            if not self._is_cancelled:
                self.finished.emit(result)

        except InterruptedError:
            pass
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True


class ResultWidget(QWidget):
    """Widget to display transcription results with refined typography."""

    startOverRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._current_markdown = ""

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header section
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Success indicator
        success_badge = QLabel("✓ TRANSCRIPTION COMPLETE")
        success_badge.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 11px;
            font-weight: 600;
            color: {COLORS['success']};
            letter-spacing: 2px;
        """)
        header_layout.addWidget(success_badge)

        # Title
        self.title_label = QLabel("Meeting Title")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(f"""
            font-family: {FONTS['heading']};
            font-size: 28px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            line-height: 1.2;
        """)
        header_layout.addWidget(self.title_label)

        # Metadata row
        meta_widget = QFrame()
        meta_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        meta_layout = QHBoxLayout(meta_widget)
        meta_layout.setSpacing(32)
        meta_layout.setContentsMargins(16, 12, 16, 12)

        # Duration
        duration_container = QWidget()
        duration_layout = QVBoxLayout(duration_container)
        duration_layout.setSpacing(2)
        duration_layout.setContentsMargins(0, 0, 0, 0)

        duration_label = QLabel("DURATION")
        duration_label.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 10px;
            color: {COLORS['text_muted']};
            letter-spacing: 1px;
        """)
        self.duration_value = QLabel("0:00")
        self.duration_value.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['accent_primary']};
        """)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_value)
        meta_layout.addWidget(duration_container)

        # Speakers
        speakers_container = QWidget()
        speakers_layout = QVBoxLayout(speakers_container)
        speakers_layout.setSpacing(2)
        speakers_layout.setContentsMargins(0, 0, 0, 0)

        speakers_label = QLabel("SPEAKERS")
        speakers_label.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 10px;
            color: {COLORS['text_muted']};
            letter-spacing: 1px;
        """)
        self.speakers_value = QLabel("0")
        self.speakers_value.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['accent_secondary']};
        """)
        speakers_layout.addWidget(speakers_label)
        speakers_layout.addWidget(self.speakers_value)
        meta_layout.addWidget(speakers_container)

        meta_layout.addStretch()
        header_layout.addWidget(meta_widget)
        layout.addWidget(header)

        # Transcript content
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                color: {COLORS['text_primary']};
                padding: 20px;
                font-family: {FONTS['body']};
                font-size: 14px;
                line-height: 1.7;
                selection-background-color: {COLORS['accent_primary']};
                selection-color: {COLORS['bg_primary']};
            }}
            QTextEdit:focus {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        layout.addWidget(self.text_area)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.new_btn = QPushButton("← New Transcription")
        self.new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_btn.setStyleSheet(secondary_button_style())
        self.new_btn.clicked.connect(self.startOverRequested.emit)

        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet(secondary_button_style())
        self.copy_btn.clicked.connect(self._copy_to_clipboard)

        self.save_btn = QPushButton("Save Transcript")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(primary_button_style())
        self.save_btn.clicked.connect(self._save_file)

        btn_layout.addWidget(self.new_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def set_result(self, result: TranscriptionResult):
        self.title_label.setText(result.title)

        # Format duration
        mins = int(result.duration) // 60
        secs = int(result.duration) % 60
        self.duration_value.setText(f"{mins}:{secs:02d}")

        self.speakers_value.setText(str(result.num_speakers))
        self.text_area.setMarkdown(result.markdown)
        self._current_markdown = result.markdown

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._current_markdown)

        # Visual feedback
        original_text = self.copy_btn.text()
        self.copy_btn.setText("✓ Copied!")
        self.copy_btn.setEnabled(False)

        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: (
            self.copy_btn.setText(original_text),
            self.copy_btn.setEnabled(True)
        ))

    def _save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Transcript", "transcript.md", "Markdown Files (*.md)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self._current_markdown)
                QMessageBox.information(self, "Saved", f"Transcript saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")


class HeaderWidget(QFrame):
    """Application header with branding."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)

        # Logo/Title
        title = QLabel("WHISPER STT")
        title.setStyleSheet(f"""
            font-family: {FONTS['heading']};
            font-size: 14px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            letter-spacing: 3px;
        """)

        # Accent dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 8px;")

        # Subtitle
        subtitle = QLabel("MEETING TRANSCRIPTION")
        subtitle.setStyleSheet(f"""
            font-family: {FONTS['mono']};
            font-size: 10px;
            color: {COLORS['text_muted']};
            letter-spacing: 2px;
        """)

        layout.addWidget(title)
        layout.addWidget(dot)
        layout.addWidget(subtitle)
        layout.addStretch()


class MainWindow(QMainWindow):
    """Main application window with Sound Studio aesthetic."""

    def __init__(self, model_name: str = "large-v3", language: str = "en"):
        super().__init__()
        self.model_name = model_name
        self.language = language
        self.setWindowTitle("Whisper STT")
        self.resize(900, 700)
        self.setMinimumSize(700, 500)

        # Apply global theme
        self.setStyleSheet(GLOBAL_STYLE)

        # Central widget
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(48, 32, 48, 48)
        main_layout.setSpacing(32)

        # Header
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)

        # Stacked content area
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # File picker view
        self.picker = FilePickerWidget()
        self.picker.fileSelected.connect(self._start_transcription)
        self.stack.addWidget(self.picker)

        # Progress view
        self.progress = ProgressWidget()
        self.progress.cancelRequested.connect(self._cancel_transcription)
        self.stack.addWidget(self.progress)

        # Result view
        self.result_view = ResultWidget()
        self.result_view.startOverRequested.connect(self._reset_ui)
        self.stack.addWidget(self.result_view)

        self.worker: Optional[TranscriptionWorker] = None

    def _start_transcription(self, file_path: Path):
        self.stack.setCurrentWidget(self.progress)
        self.progress.start()
        self.progress.set_filename(file_path.name)

        self.worker = TranscriptionWorker(self.model_name, self.language, file_path)
        self.worker.progress.connect(self.progress.update_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.start()

    def _cancel_transcription(self):
        if self.worker:
            self.worker.cancel()
            self.worker.wait()
            self.worker = None
        self.progress.stop()
        self._reset_ui()

    def _on_finished(self, result: TranscriptionResult):
        self.progress.stop()
        self.result_view.set_result(result)
        self.stack.setCurrentWidget(self.result_view)
        self.worker = None

    def _on_error(self, message: str):
        self.progress.stop()
        QMessageBox.critical(self, "Error", f"Transcription failed:\n{message}")
        self._reset_ui()
        self.worker = None

    def _reset_ui(self):
        self.stack.setCurrentWidget(self.picker)


def run_gui(model_name: str = "large-v3", language: str = "en") -> int:
    """Entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow(model_name, language)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(run_gui())
