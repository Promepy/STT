"""
settings.py — Persistent app settings using QSettings.
"""

import json
import os
from PyQt6.QtCore import QSettings


class AppSettings:
    """Manages persistent application settings via QSettings."""

    DEFAULTS = {
        "save_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
        "autosave_minutes": 5,
        # audio_sources is a JSON-encoded list of dicts:
        #   [{"device_index": 0, "gain": 1.0, "enabled": True}, ...]
        "audio_sources": "[]",
    }

    def __init__(self):
        self._settings = QSettings("Transcriber", "TranscriberApp")

    # ---- Getters ----

    @property
    def save_path(self) -> str:
        return str(self._settings.value("save_path", self.DEFAULTS["save_path"]))

    @property
    def autosave_minutes(self) -> int:
        return int(self._settings.value("autosave_minutes", self.DEFAULTS["autosave_minutes"]))

    @property
    def audio_sources(self) -> list[dict]:
        """Return the list of configured audio sources.

        Each entry: {"device_index": int, "gain": float, "enabled": bool}
        Returns empty list if nothing has been configured yet.
        """
        raw = self._settings.value("audio_sources", self.DEFAULTS["audio_sources"])
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    # ---- Setters ----

    @save_path.setter
    def save_path(self, value: str):
        self._settings.setValue("save_path", value)

    @autosave_minutes.setter
    def autosave_minutes(self, value: int):
        self._settings.setValue("autosave_minutes", value)

    @audio_sources.setter
    def audio_sources(self, sources: list[dict]):
        self._settings.setValue("audio_sources", json.dumps(sources))

    # ---- Convenience ----

    def get_enabled_sources(self) -> list[dict]:
        """Return only the sources that are enabled."""
        return [s for s in self.audio_sources if s.get("enabled", False)]

    # ---- Utility ----

    def sync(self):
        """Force write settings to disk."""
        self._settings.sync()
