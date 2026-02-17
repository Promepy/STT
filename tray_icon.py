"""
tray_icon.py — macOS menu bar (system tray) icon for the Transcriber app.

Provides quick Start/Pause-Resume/Stop access from the menu bar,
with state-aware icon changes (gray=idle, red=recording, yellow=paused).
"""

import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from ui import AppState

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _icon_path(name: str) -> str:
    """Get the path for a tray icon. Prefer 32px for retina clarity."""
    path = os.path.join(ASSETS_DIR, f"{name}_32.png")
    if os.path.exists(path):
        return path
    # Fallback to 16px
    return os.path.join(ASSETS_DIR, f"{name}_16.png")


class TrayIcon(QObject):
    """System tray icon with context menu for controlling transcription."""

    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    show_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = AppState.IDLE

        # Create tray icon
        self._tray = QSystemTrayIcon(parent)
        self._tray.setIcon(QIcon(_icon_path("tray_idle")))
        self._tray.setToolTip("Transcriber — Idle")

        # Build context menu
        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 8px;
            }
        """)

        self._start_action = self._menu.addAction("▶  Start")
        self._pause_action = self._menu.addAction("⏸  Pause")
        self._stop_action = self._menu.addAction("⏹  Stop")
        self._menu.addSeparator()
        self._show_action = self._menu.addAction("🪟  Show Window")
        self._menu.addSeparator()
        self._quit_action = self._menu.addAction("✕  Quit")

        # Connect actions
        self._start_action.triggered.connect(self.start_requested.emit)
        self._pause_action.triggered.connect(self._on_pause_resume)
        self._stop_action.triggered.connect(self.stop_requested.emit)
        self._show_action.triggered.connect(self.show_requested.emit)
        self._quit_action.triggered.connect(self.quit_requested.emit)

        # Double-click tray icon → show window
        try:
            self._tray.activated.connect(self._on_activated)
        except TypeError:
            pass  # Some PyQt6 versions can't convert ActivationReason enum

        self._tray.setContextMenu(self._menu)
        self._update_menu_state()

    def show(self):
        """Show the tray icon."""
        self._tray.show()

    def hide(self):
        """Hide the tray icon."""
        self._tray.hide()

    def set_state(self, state: AppState):
        """Update tray icon and menu to reflect the new state."""
        self._state = state
        self._update_menu_state()

        if state == AppState.RUNNING:
            self._tray.setIcon(QIcon(_icon_path("tray_recording")))
            self._tray.setToolTip("Transcriber — Recording")
        elif state == AppState.PAUSED:
            self._tray.setIcon(QIcon(_icon_path("tray_paused")))
            self._tray.setToolTip("Transcriber — Paused")
        else:
            self._tray.setIcon(QIcon(_icon_path("tray_idle")))
            self._tray.setToolTip("Transcriber — Idle")

    def _update_menu_state(self):
        s = self._state
        self._start_action.setEnabled(s == AppState.IDLE)
        self._pause_action.setEnabled(s in (AppState.RUNNING, AppState.PAUSED))
        self._stop_action.setEnabled(s in (AppState.RUNNING, AppState.PAUSED))

        if s == AppState.PAUSED:
            self._pause_action.setText("▶  Resume")
        else:
            self._pause_action.setText("⏸  Pause")

    def _on_pause_resume(self):
        if self._state == AppState.PAUSED:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()
