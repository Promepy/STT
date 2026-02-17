"""
autosave.py — QTimer-based autosave manager for transcription files.
"""

import logging

from PyQt6.QtCore import QTimer, QObject

logger = logging.getLogger(__name__)


class AutosaveManager(QObject):
    """Periodically flushes a text buffer to an open file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._file = None
        self._buffer: list[str] = []

    # ---- Control ----

    def start(self, file_handle, interval_ms: int):
        """Begin autosaving to the given file handle every interval_ms."""
        self._file = file_handle
        self._buffer.clear()
        self._timer.start(interval_ms)
        logger.info("Autosave started — interval %d ms", interval_ms)

    def stop(self):
        """Stop the autosave timer (does NOT flush — call flush() first)."""
        self._timer.stop()
        logger.info("Autosave stopped")

    def append(self, text: str):
        """Add text to the autosave buffer."""
        if text:
            self._buffer.append(text)

    def flush(self):
        """Write all buffered text to disk immediately."""
        if not self._file or not self._buffer:
            return
        try:
            self._file.write(" ".join(self._buffer) + "\n")
            self._file.flush()
            self._buffer.clear()
            logger.debug("Autosave flushed to disk")
        except OSError as e:
            logger.error("Autosave flush failed: %s", e)

    # ---- Internal ----

    def _on_tick(self):
        """Timer callback — flush buffer to disk."""
        self.flush()
