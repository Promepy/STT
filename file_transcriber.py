"""
file_transcriber.py — Worker thread for transcribing audio/video files.

Handles:
  - FFmpeg conversion (any media → 16 kHz mono WAV)
  - Chunked Vosk transcription with progress signals
  - Cancellation and temp-file cleanup
"""

import json
import os
import subprocess
import tempfile
import wave
import logging

from PyQt6.QtCore import QThread, pyqtSignal
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)

# Audio constants matching the rest of the app
_SAMPLE_RATE = 16000
_CHUNK_FRAMES = 4000

# Supported file extensions
SUPPORTED_VIDEO = (".mp4", ".mov", ".mkv", ".avi")
SUPPORTED_AUDIO = (".mp3", ".wav", ".m4a", ".aac", ".flac")
SUPPORTED_EXTENSIONS = SUPPORTED_VIDEO + SUPPORTED_AUDIO

FILE_DIALOG_FILTER = (
    "Media Files (*.mp4 *.mov *.mkv *.avi *.mp3 *.wav *.m4a *.aac *.flac);;"
    "Video Files (*.mp4 *.mov *.mkv *.avi);;"
    "Audio Files (*.mp3 *.wav *.m4a *.aac *.flac);;"
    "All Files (*)"
)


def _find_ffmpeg() -> str | None:
    """Return the ffmpeg binary path, or None if not installed."""
    import shutil
    return shutil.which("ffmpeg")


class FileTranscriptionWorker(QThread):
    """Transcribes a media file in a background thread.

    Signals:
        progress_updated(int): percentage 0–100
        text_updated(str): recognized text chunks
        finished_signal(): emitted when transcription completes normally
        error_occurred(str): emitted on any error
    """

    progress_updated = pyqtSignal(int)
    text_updated = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path: str, model_path: str | None = None):
        super().__init__()
        self._file_path = file_path
        self._model_path = model_path
        self._is_cancelled = False
        self._temp_wav: str | None = None

    # ---- Public API ----

    def cancel(self):
        """Request cancellation — worker will stop at next chunk boundary."""
        self._is_cancelled = True

    # ---- Thread entry point ----

    def run(self):
        try:
            self._do_transcription()
        except Exception as e:
            logger.exception("File transcription error")
            self.error_occurred.emit(str(e))
        finally:
            self._cleanup()

    # ---- Internal pipeline ----

    def _do_transcription(self):
        # Step 1 — Convert to WAV if needed
        wav_path = self._ensure_wav()
        if self._is_cancelled:
            return

        # Step 2 — Load Vosk model
        model_dir = self._model_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "models",
            "vosk-model-small-en-us-0.15",
        )
        if not os.path.isdir(model_dir):
            self.error_occurred.emit(
                f"Vosk model not found at: {model_dir}\n"
                "Download from https://alphacephei.com/vosk/models"
            )
            return

        model = Model(model_dir)
        recognizer = KaldiRecognizer(model, _SAMPLE_RATE)

        # Step 3 — Stream audio and transcribe
        with wave.open(wav_path, "rb") as wf:
            total_frames = wf.getnframes()
            if total_frames == 0:
                self.error_occurred.emit("Audio file is empty (0 frames).")
                return

            frames_processed = 0
            last_pct = -1

            while True:
                if self._is_cancelled:
                    return

                data = wf.readframes(_CHUNK_FRAMES)
                if len(data) == 0:
                    break

                frames_processed += _CHUNK_FRAMES

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        self.text_updated.emit(text)

                # Update progress
                pct = min(int((frames_processed / total_frames) * 100), 100)
                if pct != last_pct:
                    self.progress_updated.emit(pct)
                    last_pct = pct

            # Flush remaining text
            final = json.loads(recognizer.FinalResult())
            text = final.get("text", "").strip()
            if text:
                self.text_updated.emit(text)

        self.progress_updated.emit(100)
        self.finished_signal.emit()

    def _ensure_wav(self) -> str:
        """Convert the input file to 16 kHz mono WAV if necessary.

        If the file is already a .wav, we still re-encode to guarantee
        the correct sample rate and channel count.
        """
        ffmpeg = _find_ffmpeg()
        if ffmpeg is None:
            raise RuntimeError(
                "FFmpeg is not installed.\n"
                "Install it with: brew install ffmpeg (macOS)\n"
                "or download from https://ffmpeg.org"
            )

        # Create a temp WAV file
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        self._temp_wav = temp_path

        logger.info("Converting %s → %s", self._file_path, temp_path)

        result = subprocess.run(
            [
                ffmpeg,
                "-i", self._file_path,
                "-ar", str(_SAMPLE_RATE),
                "-ac", "1",
                "-y",
                temp_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg conversion failed:\n{result.stderr[:500]}"
            )

        return temp_path

    def _cleanup(self):
        """Delete temporary WAV file if it exists."""
        if self._temp_wav and os.path.exists(self._temp_wav):
            try:
                os.remove(self._temp_wav)
                logger.info("Removed temp file: %s", self._temp_wav)
            except OSError as e:
                logger.warning("Could not remove temp file: %s", e)
            self._temp_wav = None
