from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import QTimer, Qt

from whisper_stt.service.daemon import DaemonManager, run_daemon


class TrayIcon(QSystemTrayIcon):
    
    def __init__(self, model_name: str = "turbo", language: str = "en") -> None:
        super().__init__()
        self.model_name = model_name
        self.language = language
        self._manager = DaemonManager()
        self._recording = False
        
        self._icon_idle = self._create_icon("#6c7086")
        self._icon_recording = self._create_icon("#f38ba8")
        self._icon_ready = self._create_icon("#a6e3a1")
        
        self.setIcon(self._icon_idle)
        self.setToolTip("Whisper STT - Idle")
        
        self._menu = QMenu()
        
        self._status_action = QAction("Status: Idle")
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)
        
        self._menu.addSeparator()
        
        self._toggle_action = QAction("Start Service")
        self._toggle_action.triggered.connect(self._toggle_service)
        self._menu.addAction(self._toggle_action)
        
        self._menu.addSeparator()
        
        quit_action = QAction("Quit")
        quit_action.triggered.connect(self._quit)
        self._menu.addAction(quit_action)
        
        self.setContextMenu(self._menu)
        self.activated.connect(self._on_activated)
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_status)
        self._timer.start(500)
        
        self._transcriber = None
        self._update_status()
    
    def _create_icon(self, color: str) -> QIcon:
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, size - 8, size - 8)
        
        painter.setBrush(QColor("#1e1e2e"))
        mic_rect = (size // 4, size // 4, size // 2, size // 2)
        painter.drawRoundedRect(*mic_rect, 8, 8)
        
        painter.end()
        return QIcon(pixmap)
    
    def _update_status(self) -> None:
        status = self._manager.read_status()
        recording = status.get("recording", False)
        is_running = self._manager.is_running()
        
        if not is_running:
            self.setIcon(self._icon_idle)
            self.setToolTip("Whisper STT - Service Stopped")
            self._status_action.setText("Status: Service Stopped")
            self._toggle_action.setText("Start Service")
        elif recording:
            self.setIcon(self._icon_recording)
            self.setToolTip("Whisper STT - Recording")
            self._status_action.setText("Status: Recording...")
            self._toggle_action.setText("Stop Service")
        else:
            self.setIcon(self._icon_ready)
            self.setToolTip("Whisper STT - Ready (F13 to record)")
            self._status_action.setText("Status: Ready")
            self._toggle_action.setText("Stop Service")
        
        self._recording = recording
    
    def _toggle_service(self) -> None:
        if self._manager.is_running():
            self._manager.stop_daemon()
        else:
            self._start_daemon()
    
    def _start_daemon(self) -> None:
        import subprocess
        subprocess.Popen(
            [sys.executable, "-m", "whisper_stt.cli", "daemon", 
             "-m", self.model_name, "-l", self.language],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_service()
    
    def _quit(self) -> None:
        if self._manager.is_running():
            self._manager.stop_daemon()
        QApplication.quit()


def run_tray(model_name: str = "turbo", language: str = "en") -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray not available", file=sys.stderr)
        return 1
    
    tray = TrayIcon(model_name=model_name, language=language)
    tray.show()
    
    return app.exec()
