"""
transcription_engine.py — Vosk model loading and speech recognition.
"""

import json
import os

from vosk import Model, KaldiRecognizer

from audio_engine import SAMPLE_RATE


# Default model path (relative to this file's directory)
_DEFAULT_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models",
    "vosk-model-small-en-us-0.15",
)


class TranscriptionEngine:
    """Wraps Vosk for streaming speech-to-text."""

    def __init__(self, model_path: str | None = None):
        path = model_path or _DEFAULT_MODEL_DIR
        if not os.path.isdir(path):
            raise FileNotFoundError(
                f"Vosk model not found at: {path}\n"
                "Download from https://alphacephei.com/vosk/models"
            )
        self._model = Model(path)
        self._recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)

    # ---- Processing ----

    def process_chunk(self, data: bytes) -> tuple[str | None, str | None]:
        """Feed an audio chunk to the recognizer.

        Returns:
            (final_text, partial_text)
            - final_text is set when the recognizer has a complete phrase.
            - partial_text is set with the current partial hypothesis.
            - One or both may be None.
        """
        if self._recognizer.AcceptWaveform(data):
            result = json.loads(self._recognizer.Result())
            text = result.get("text", "").strip()
            return (text if text else None, None)
        else:
            partial = json.loads(self._recognizer.PartialResult())
            text = partial.get("partial", "").strip()
            return (None, text if text else None)

    def final_result(self) -> str | None:
        """Get the final remaining text from the recognizer buffer.

        Call this when stopping a session to flush any buffered speech.
        """
        result = json.loads(self._recognizer.FinalResult())
        text = result.get("text", "").strip()
        return text if text else None

    def reset(self):
        """Reset the recognizer for a new session."""
        self._recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)
