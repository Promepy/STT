"""
ui.py — PyQt6 UI for the Transcriber app.

Provides:
  - TranscriberUI (QMainWindow): top bar + transcription area
  - SettingsDialog (QDialog): audio sources with gain sliders, save path, autosave
"""

import sys
from enum import Enum, auto

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QTextEdit, QToolButton, QLabel,
    QDialog, QFormLayout, QComboBox,
    QSpinBox, QPushButton, QFileDialog,
    QCheckBox, QSlider, QGroupBox, QScrollArea,
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from settings import AppSettings
from audio_engine import AudioEngine


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class AppState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()


# ---------------------------------------------------------------------------
# Animated recording dot
# ---------------------------------------------------------------------------

class RecordingDot(QLabel):
    """A small blinking red/yellow dot indicating recording state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._visible = True
        self._color = "#e74c3c"  # red

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle)
        self._update_style()
        self.hide()

    def start(self, color: str = "#e74c3c"):
        """Start blinking with the given color."""
        self._color = color
        self._visible = True
        self._update_style()
        self.show()
        self._blink_timer.start(600)

    def stop(self):
        """Stop blinking and hide."""
        self._blink_timer.stop()
        self.hide()

    def set_color(self, color: str):
        """Change the dot color without restarting."""
        self._color = color
        self._update_style()

    def _toggle(self):
        self._visible = not self._visible
        self._update_style()

    def _update_style(self):
        bg = self._color if self._visible else "transparent"
        self.setStyleSheet(
            f"background-color: {bg};"
            f"border-radius: 6px;"
            f"border: none;"
        )


# ---------------------------------------------------------------------------
# Source row widget (checkbox + name + slider + percentage)
# ---------------------------------------------------------------------------

class AudioSourceRow(QWidget):
    """One row in the audio sources list: ☑ Device Name  ━━━●━━  80%"""

    def __init__(self, device_index: int, device_name: str,
                 gain: float = 1.0, enabled: bool = True, parent=None):
        super().__init__(parent)
        self.device_index = device_index

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(enabled)
        layout.addWidget(self.checkbox)

        # Device name
        name_label = QLabel(device_name)
        name_label.setMinimumWidth(180)
        name_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        layout.addWidget(name_label, stretch=1)

        # Gain slider (0–200 %, stored as 0.0–2.0)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 200)
        self.slider.setValue(int(gain * 100))
        self.slider.setMinimumWidth(120)
        self.slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self.slider, stretch=1)

        # Percentage label
        self.pct_label = QLabel(f"{int(gain * 100)}%")
        self.pct_label.setFixedWidth(42)
        self.pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.pct_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        layout.addWidget(self.pct_label)

    def _on_slider_change(self, value: int):
        self.pct_label.setText(f"{value}%")

    def to_dict(self) -> dict:
        return {
            "device_index": self.device_index,
            "gain": self.slider.value() / 100.0,
            "enabled": self.checkbox.isChecked(),
        }


# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------

class SettingsDialog(QDialog):
    """Modal dialog for app settings — audio sources, save path, autosave."""

    def __init__(self, settings: AppSettings, audio_engine: AudioEngine, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self._settings = settings
        self._audio_engine = audio_engine
        self._source_rows: list[AudioSourceRow] = []
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setLayout(layout)

        # ---- Audio Sources section ----
        sources_group = QGroupBox("Audio Sources")
        sources_group.setStyleSheet("""
            QGroupBox {
                color: #e0e0e0;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
        """)
        sources_layout = QVBoxLayout()
        sources_layout.setSpacing(4)
        sources_group.setLayout(sources_layout)

        # Build source rows from available devices + saved settings
        devices = self._audio_engine.list_input_devices()
        saved = {s["device_index"]: s for s in self._settings.audio_sources}

        for dev in devices:
            idx = dev["index"]
            if idx in saved:
                gain = saved[idx].get("gain", 1.0)
                enabled = saved[idx].get("enabled", False)
            else:
                gain = 1.0
                enabled = False  # new devices default to disabled

            row = AudioSourceRow(idx, dev["name"], gain, enabled)
            self._source_rows.append(row)
            sources_layout.addWidget(row)

        if not devices:
            no_dev = QLabel("No audio input devices found")
            no_dev.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
            sources_layout.addWidget(no_dev)

        layout.addWidget(sources_group)

        # ---- Other settings (form) ----
        form = QFormLayout()
        form.setSpacing(14)

        # Save path
        path_row = QHBoxLayout()
        self.path_label = QLabel(self._settings.save_path)
        self.path_label.setWordWrap(True)
        browse_btn = QPushButton("Browse…")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_folder)
        path_row.addWidget(self.path_label, stretch=1)
        path_row.addWidget(browse_btn)
        form.addRow("Save Location:", path_row)

        # Autosave interval
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" min")
        self.interval_spin.setValue(self._settings.autosave_minutes)
        form.addRow("Autosave Interval:", self.interval_spin)

        layout.addLayout(form)

        # ---- Save button ----
        save_btn = QPushButton("Save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        save_btn.setFixedHeight(36)
        layout.addWidget(save_btn)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.path_label.text())
        if folder:
            self.path_label.setText(folder)

    def _save(self):
        # Collect source settings
        sources = [row.to_dict() for row in self._source_rows]
        self._settings.audio_sources = sources

        self._settings.save_path = self.path_label.text()
        self._settings.autosave_minutes = self.interval_spin.value()
        self._settings.sync()
        self.accept()

    def _apply_styles(self):
        self.setStyleSheet(self.styleSheet() + """
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #b0b0b0;
                font-size: 13px;
            }
            QSpinBox {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #555;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #2ecc71;
                border-color: #2ecc71;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #333;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #e0e0e0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #3a6ea5;
                border-radius: 2px;
            }
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class TranscriberUI(QMainWindow):
    """The main transcriber window."""

    # Signals for external wiring (main.py connects these)
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, settings: AppSettings, audio_engine: AudioEngine):
        super().__init__()
        self._settings = settings
        self._audio_engine = audio_engine
        self._state = AppState.IDLE
        self.setWindowTitle("Transcriber")
        self.setMinimumSize(900, 600)
        self._init_ui()
        self._apply_styles()
        self._update_button_states()

    # ---- UI construction ----

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        # ---- Top bar ----
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(55)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(15, 10, 15, 10)
        top_layout.setSpacing(10)
        top_bar.setLayout(top_layout)

        # Recording dot
        self.rec_dot = RecordingDot()

        # Buttons
        self.start_btn = self._make_button("Start")
        self.pause_btn = self._make_button("Pause")
        self.stop_btn = self._make_button("Stop")
        self.settings_btn = self._make_button("⚙")

        self.start_btn.clicked.connect(self._on_start)
        self.pause_btn.clicked.connect(self._on_pause)
        self.stop_btn.clicked.connect(self._on_stop)
        self.settings_btn.clicked.connect(self._on_settings)

        top_layout.addWidget(self.rec_dot)
        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.pause_btn)
        top_layout.addWidget(self.stop_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.settings_btn)

        # ---- Transcription area ----
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("SF Pro Text", 13))
        self.text_area.setPlaceholderText("Live transcription will appear here…")

        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.text_area)

    # ---- Helpers ----

    @staticmethod
    def _make_button(text: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(32)
        return btn

    # ---- State management ----

    def set_state(self, state: AppState):
        """Update internal state and refresh button states + indicators."""
        self._state = state
        self._update_button_states()

    def _update_button_states(self):
        s = self._state

        self.start_btn.setEnabled(s == AppState.IDLE)
        self.pause_btn.setEnabled(s in (AppState.RUNNING, AppState.PAUSED))
        self.stop_btn.setEnabled(s in (AppState.RUNNING, AppState.PAUSED))

        # Reset button styles
        self.start_btn.setStyleSheet("")
        self.pause_btn.setStyleSheet("")

        if s == AppState.RUNNING:
            self.pause_btn.setText("Pause")
            self.start_btn.setStyleSheet(
                "QToolButton { background-color: #2ecc71; color: #1a1a1a; }"
            )
            self.rec_dot.start("#e74c3c")
        elif s == AppState.PAUSED:
            self.pause_btn.setText("Resume")
            self.pause_btn.setStyleSheet(
                "QToolButton { background-color: #f1c40f; color: #1a1a1a; }"
            )
            self.rec_dot.start("#f1c40f")
        else:
            self.pause_btn.setText("Pause")
            self.rec_dot.stop()

    # ---- Slots triggered by UI buttons ----

    def _on_start(self):
        self.start_requested.emit()

    def _on_pause(self):
        if self._state == AppState.PAUSED:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()

    def _on_stop(self):
        self.stop_requested.emit()

    def _on_settings(self):
        dlg = SettingsDialog(self._settings, self._audio_engine, self)
        dlg.exec()

    # ---- Public API for updating text ----

    def append_text(self, text: str):
        """Append finalized transcription text."""
        self.text_area.append(text)

    def show_partial(self, text: str):
        """Show partial (in-progress) transcription.

        Replaces the last line if it was a partial, appends otherwise.
        """
        cursor = self.text_area.textCursor()
        # Move to end
        cursor.movePosition(cursor.MoveOperation.End)
        self.text_area.setTextCursor(cursor)

        # Get current block text to check if it's a partial
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        current_block = cursor.selectedText()

        if current_block.startswith("…"):
            # Replace existing partial
            cursor.removeSelectedText()
            cursor.insertText(f"…{text}")
        else:
            self.text_area.append(f"…{text}")

    def clear_partial(self):
        """Remove the current partial line (called when final text arrives)."""
        cursor = self.text_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        if cursor.selectedText().startswith("…"):
            cursor.removeSelectedText()
            # Remove the trailing newline left behind
            cursor.deletePreviousChar()
        self.text_area.setTextCursor(cursor)

    def clear_text(self):
        """Clear the transcription area."""
        self.text_area.clear()

    # ---- Stylesheet ----

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }

            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }

            #topBar {
                background-color: #252525;
                border-bottom: 1px solid #333333;
            }

            QToolButton {
                background-color: #2a2a2a;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
                color: #e0e0e0;
            }

            QToolButton:hover {
                background-color: #3a3a3a;
            }

            QToolButton:disabled {
                background-color: #222222;
                color: #555555;
            }

            QTextEdit {
                background-color: #202020;
                border: none;
                padding: 20px;
                font-size: 13px;
                color: #e0e0e0;
                selection-background-color: #3a6ea5;
            }
        """)
