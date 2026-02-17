"""
main.py — Entry point for the Transcriber app.

Wires together: UI, AudioWorker (QThread), Vosk, Autosave, Settings.
"""

import sys
import os
import logging
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt6.QtCore import QThread, QObject, pyqtSignal

from settings import AppSettings
from audio_engine import AudioEngine
from transcription_engine import TranscriptionEngine
from autosave import AutosaveManager
from ui import TranscriberUI, AppState
from tray_icon import TrayIcon
from file_transcriber import FileTranscriptionWorker, FILE_DIALOG_FILTER

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    filename="error.log",
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Audio worker (runs in QThread)
# ---------------------------------------------------------------------------

class AudioWorker(QObject):
    """Captures mic audio and runs Vosk transcription in a background thread."""

    text_ready = pyqtSignal(str)       # finalized text
    partial_ready = pyqtSignal(str)    # in-progress hypothesis
    error_occurred = pyqtSignal(str)   # error message

    def __init__(self):
        super().__init__()
        self._running = False
        self._paused = False
        self._audio_engine: AudioEngine | None = None
        self._transcription_engine: TranscriptionEngine | None = None
        self._sources: list[dict] = []

    def configure(self, audio_engine: AudioEngine, transcription_engine: TranscriptionEngine, sources: list[dict]):
        self._audio_engine = audio_engine
        self._transcription_engine = transcription_engine
        self._sources = sources

    def run(self):
        """Main capture loop — runs until stop() is called."""
        try:
            self._audio_engine.open_streams(self._sources)
        except Exception as e:
            self.error_occurred.emit(f"Failed to open audio sources: {e}")
            return

        self._running = True
        self._paused = False

        while self._running:
            if self._paused:
                QThread.msleep(50)
                continue

            data = self._audio_engine.read_and_mix()
            if not data:
                QThread.msleep(10)
                continue

            final, partial = self._transcription_engine.process_chunk(data)
            if final:
                self.text_ready.emit(final)
            elif partial:
                self.partial_ready.emit(partial)

        # Flush remaining speech
        remaining = self._transcription_engine.final_result()
        if remaining:
            self.text_ready.emit(remaining)

        self._audio_engine.close_streams()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# Application controller
# ---------------------------------------------------------------------------

class TranscriberApp:
    """Top-level controller — owns all components and manages session lifecycle."""

    def __init__(self):
        self.settings = AppSettings()
        self.audio_engine = AudioEngine()
        self.audio_engine.init()

        self.ui = TranscriberUI(self.settings, self.audio_engine)

        # Tray icon
        self.tray = TrayIcon()
        self.tray.show()

        self.autosave = AutosaveManager()
        self._file = None
        self._worker: AudioWorker | None = None
        self._thread: QThread | None = None
        self._transcription_engine: TranscriptionEngine | None = None

        # File transcription state
        self._file_worker: FileTranscriptionWorker | None = None
        self._file_output = None  # output file handle for file transcription

        # Wire UI signals
        self.ui.start_requested.connect(self.start_session)
        self.ui.pause_requested.connect(self.pause_session)
        self.ui.resume_requested.connect(self.resume_session)
        self.ui.stop_requested.connect(self.stop_session)
        self.ui.file_transcribe_requested.connect(self.start_file_transcription)
        self.ui.file_cancel_requested.connect(self.cancel_file_transcription)

        # Wire tray signals
        self.tray.start_requested.connect(self.start_session)
        self.tray.pause_requested.connect(self.pause_session)
        self.tray.resume_requested.connect(self.resume_session)
        self.tray.stop_requested.connect(self.stop_session)
        self.tray.show_requested.connect(self._show_window)
        self.tray.quit_requested.connect(self._quit)

    # ---- Session lifecycle ----

    def start_session(self):
        """Start a new transcription session."""
        # Lazy-load Vosk model
        if self._transcription_engine is None:
            try:
                self._transcription_engine = TranscriptionEngine()
            except FileNotFoundError as e:
                QMessageBox.critical(self.ui, "Model Error", str(e))
                return
        else:
            self._transcription_engine.reset()

        # Create output file
        save_dir = self.settings.save_path
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(save_dir, f"transcription_{ts}.txt")
        try:
            self._file = open(filepath, "a", encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self.ui, "File Error", f"Cannot create file:\n{e}")
            return

        logger.info("Session started → %s", filepath)

        # Clear UI
        self.ui.clear_text()

        # Start autosave
        interval_ms = self.settings.autosave_minutes * 60 * 1000
        self.autosave.start(self._file, interval_ms)

        # Determine audio sources
        sources = self.settings.get_enabled_sources()
        if not sources:
            # Default: use first available input device at gain 1.0
            devices = self.audio_engine.list_input_devices()
            if devices:
                sources = [{"device_index": devices[0]["index"], "gain": 1.0, "enabled": True}]
            else:
                QMessageBox.critical(self.ui, "Audio Error", "No audio input devices found.")
                return

        # Start audio worker thread
        self._thread = QThread()
        self._worker = AudioWorker()
        self._worker.configure(self.audio_engine, self._transcription_engine, sources)
        self._worker.moveToThread(self._thread)

        self._worker.text_ready.connect(self._on_final_text)
        self._worker.partial_ready.connect(self._on_partial_text)
        self._worker.error_occurred.connect(self._on_error)
        self._thread.started.connect(self._worker.run)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()
        self.ui.set_state(AppState.RUNNING)
        self.tray.set_state(AppState.RUNNING)

    def pause_session(self):
        """Pause the current session."""
        if self._worker:
            self._worker.pause()
        self.ui.set_state(AppState.PAUSED)
        self.tray.set_state(AppState.PAUSED)
        logger.info("Session paused")

    def resume_session(self):
        """Resume a paused session."""
        if self._worker:
            self._worker.resume()
        self.ui.set_state(AppState.RUNNING)
        self.tray.set_state(AppState.RUNNING)
        logger.info("Session resumed")

    def stop_session(self):
        """Stop and finalize the current session."""
        if self._worker:
            self._worker.stop()

        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)

        # Flush autosave
        self.autosave.flush()
        self.autosave.stop()

        # Close file
        if self._file:
            try:
                self._file.close()
            except OSError:
                pass
            self._file = None

        self._worker = None
        self._thread = None

        self.ui.set_state(AppState.IDLE)
        self.tray.set_state(AppState.IDLE)
        logger.info("Session stopped")

    # ---- Slots ----

    def _on_final_text(self, text: str):
        self.ui.clear_partial()
        self.ui.append_text(text)
        self.autosave.append(text)

    def _on_partial_text(self, text: str):
        self.ui.show_partial(text)

    def _on_error(self, msg: str):
        logger.error("Worker error: %s", msg)
        QMessageBox.warning(self.ui, "Error", msg)
        self.stop_session()

    # ---- File transcription ----

    def start_file_transcription(self):
        """Open file dialog, then start background file transcription."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select Media File", "", FILE_DIALOG_FILTER,
        )
        if not file_path:
            return  # user cancelled the dialog

        # Create output file
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        save_dir = self.settings.save_path
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(save_dir, f"{base_name}_transcript_{ts}.txt")
        try:
            self._file_output = open(output_path, "a", encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self.ui, "File Error", f"Cannot create output file:\n{e}")
            return

        logger.info("File transcription started: %s → %s", file_path, output_path)

        # Prepare UI
        self.ui.clear_text()
        self.ui.set_file_transcribing(True)

        # Start worker
        self._file_worker = FileTranscriptionWorker(file_path)
        self._file_worker.progress_updated.connect(self._on_file_progress)
        self._file_worker.text_updated.connect(self._on_file_text)
        self._file_worker.finished_signal.connect(self._on_file_finished)
        self._file_worker.error_occurred.connect(self._on_file_error)
        self._file_worker.start()

    def cancel_file_transcription(self):
        """Cancel ongoing file transcription."""
        if self._file_worker:
            self._file_worker.cancel()
            self._file_worker.wait(5000)
            self._cleanup_file_transcription()
            self.ui.append_text("\n— File transcription cancelled —")
            logger.info("File transcription cancelled")

    def _on_file_progress(self, pct: int):
        self.ui.update_file_progress(pct)

    def _on_file_text(self, text: str):
        self.ui.append_text(text)
        if self._file_output:
            try:
                self._file_output.write(text + "\n")
                self._file_output.flush()
            except OSError as e:
                logger.error("File write error: %s", e)

    def _on_file_finished(self):
        self._cleanup_file_transcription()
        self.ui.append_text("\n— File transcription complete —")
        logger.info("File transcription finished")

    def _on_file_error(self, msg: str):
        self._cleanup_file_transcription()
        logger.error("File transcription error: %s", msg)
        QMessageBox.warning(self.ui, "File Transcription Error", msg)

    def _cleanup_file_transcription(self):
        """Reset file transcription state and close output file."""
        self.ui.set_file_transcribing(False)
        if self._file_output:
            try:
                self._file_output.close()
            except OSError:
                pass
            self._file_output = None
        self._file_worker = None

    # ---- Window management ----

    def _show_window(self):
        """Bring the main window to front."""
        self.ui.show()
        self.ui.raise_()
        self.ui.activateWindow()

    def _quit(self):
        """Quit the entire application."""
        self.shutdown()
        QApplication.instance().quit()

    # ---- Cleanup ----

    def shutdown(self):
        """Clean up all resources."""
        if self._thread and self._thread.isRunning():
            self.stop_session()
        if self._file_worker:
            self.cancel_file_transcription()
        self.tray.hide()
        self.audio_engine.terminate()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Transcriber")
    app.setOrganizationName("Transcriber")

    # Keep app alive when main window is closed (tray stays active)
    app.setQuitOnLastWindowClosed(False)

    controller = TranscriberApp()
    controller.ui.show()

    exit_code = app.exec()
    controller.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
