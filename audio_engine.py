"""
audio_engine.py — Microphone detection and multi-stream audio capture using PyAudio.

Supports opening multiple input devices simultaneously, applying per-source
gain, and mixing them into a single output buffer for the recognizer.
"""

import struct
import pyaudio


# Audio constants
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 4000  # frames per buffer
BYTES_PER_SAMPLE = 2  # int16


def _clamp16(value: int) -> int:
    """Clamp an integer to int16 range."""
    return max(-32768, min(32767, value))


class AudioEngine:
    """Handles PyAudio initialization, mic listing, and multi-stream management."""

    def __init__(self):
        self._pa: pyaudio.PyAudio | None = None
        # List of (stream, gain) tuples for multi-source capture
        self._streams: list[tuple[pyaudio.Stream, float]] = []

    # ---- Lifecycle ----

    def init(self):
        """Initialize the PyAudio instance."""
        if self._pa is None:
            self._pa = pyaudio.PyAudio()

    def terminate(self):
        """Release all PyAudio resources."""
        self.close_streams()
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None

    # ---- Device listing ----

    def list_input_devices(self) -> list[dict]:
        """Return a list of available input (microphone) devices.

        Each dict contains: index, name, max_input_channels.
        """
        self.init()
        devices = []
        for i in range(self._pa.get_device_count()):
            info = self._pa.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                devices.append({
                    "index": i,
                    "name": info["name"],
                    "max_input_channels": info["maxInputChannels"],
                })
        return devices

    # ---- Multi-stream control ----

    def open_streams(self, sources: list[dict]):
        """Open an audio input stream for each enabled source.

        Args:
            sources: list of {"device_index": int, "gain": float, "enabled": bool}
        """
        self.init()
        self.close_streams()

        for src in sources:
            if not src.get("enabled", False):
                continue
            device_index = src["device_index"]
            gain = src.get("gain", 1.0)
            try:
                stream = self._pa.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE,
                    input_device_index=device_index,
                )
                self._streams.append((stream, gain))
            except OSError:
                # Skip devices that fail to open
                continue

        if not self._streams:
            raise RuntimeError("No audio streams could be opened. Check your device settings.")

    def read_and_mix(self) -> bytes:
        """Read one chunk from every active stream, apply gain, and mix.

        Returns a single int16 buffer suitable for the Vosk recognizer.
        Returns empty bytes if no streams are active.
        """
        if not self._streams:
            return b""

        mixed = [0] * CHUNK_SIZE

        for stream, gain in self._streams:
            try:
                if not stream.is_active():
                    continue
                raw = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            except OSError:
                continue

            # Unpack int16 samples
            samples = struct.unpack(f"<{CHUNK_SIZE}h", raw)
            for i, s in enumerate(samples):
                mixed[i] += int(s * gain)

        # Clamp to int16 range and pack
        clamped = [_clamp16(s) for s in mixed]
        return struct.pack(f"<{CHUNK_SIZE}h", *clamped)

    def close_streams(self):
        """Stop and close all open audio streams."""
        for stream, _ in self._streams:
            try:
                if stream.is_active():
                    stream.stop_stream()
                stream.close()
            except OSError:
                pass
        self._streams.clear()

    # ---- Legacy single-stream (kept for compatibility) ----

    def open_stream(self, device_index: int | None = None) -> pyaudio.Stream:
        """Open a single audio input stream (legacy)."""
        self.open_streams([{"device_index": device_index or 0, "gain": 1.0, "enabled": True}])
        return self._streams[0][0] if self._streams else None

    def read_chunk(self) -> bytes:
        """Read from single stream (legacy). Uses read_and_mix internally."""
        return self.read_and_mix()

    def close_stream(self):
        """Close single stream (legacy)."""
        self.close_streams()
