# 🎙️ Transcriber

A lightweight, **fully offline** speech-to-text desktop app. Captures microphone audio (and optionally system audio) and transcribes it live using [Vosk](https://alphacephei.com/vosk/) — no internet required. Also supports **transcribing audio/video files** directly.

Built with **Python**, **PyQt6**, **Vosk**, **PyAudio**, and **FFmpeg**. Runs on macOS, Windows, and Linux.

---

## ✨ Features

- **Real-time transcription** — see text appear as you speak
- **Media file transcription** — transcribe audio/video files (MP4, MOV, MKV, AVI, MP3, WAV, M4A, AAC, FLAC) with live progress
- **100% offline** — no data leaves your machine
- **Multi-source audio** — mic, system audio, or both simultaneously
- **Per-source gain control** — individual volume sliders for each input
- **Session controls** — Start / Pause / Resume / Stop
- **Autosave** — periodic save to prevent data loss during long sessions
- **System tray icon** — control recording from the menu bar / taskbar
- **Persistent settings** — mic selection, save path, and autosave interval remembered across sessions
- **Cross-platform** — works on macOS, Windows, and Linux

---

## 🖥️ Screenshot

```
┌────────────────────────────────────────────────────────┐
│  ●  Start  Pause  Stop  Transcribe File        ⚙      │
├────────────────────────────────────────────────────────┤
│  ████████████████████████░░░░░░░░░░░░░░░░  58%        │  ← progress bar (file mode)
├────────────────────────────────────────────────────────┤
│                                                        │
│        Live transcription appears here...              │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Transcriber/
├── main.py                  # App entry point — wires everything together
├── ui.py                    # PyQt6 UI (main window, settings dialog, styling)
├── audio_engine.py          # Multi-device audio capture & mixing via PyAudio
├── transcription_engine.py  # Vosk model loading & speech recognition
├── file_transcriber.py      # Media file transcription worker (FFmpeg + Vosk)
├── autosave.py              # QTimer-based periodic file save
├── settings.py              # Persistent settings via QSettings
├── tray_icon.py             # System tray icon with context menu
├── generate_icon.py         # Utility to generate tray icon PNGs
├── install_autostart.sh     # macOS Launch Agent installer (auto-start on login)
├── requirements.txt         # Python dependencies
├── setup.md                 # Full setup guide for Windows, macOS, and Linux
├── assets/                  # Tray icon images (idle, recording, paused)
├── models/                  # Vosk model directory (not tracked — see setup)
└── output/                  # Saved transcription .txt files (not tracked)
```

---

## 🚀 Quick Start

> **Full setup instructions** for all platforms are in [`setup.md`](setup.md).

### 1. Install system dependencies

**macOS:** `brew install portaudio ffmpeg`
**Ubuntu/Debian:** `sudo apt install portaudio19-dev python3-venv ffmpeg`
**Windows:** Install [FFmpeg](https://ffmpeg.org/download.html) and add to PATH

### 2. Create virtual environment & install packages

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Download the Vosk model

Download [vosk-model-small-en-us-0.15](https://alphacephei.com/vosk/models) and extract it into `models/`:

```
models/vosk-model-small-en-us-0.15/
```

### 4. Run

```bash
python main.py
```

---

## 🏗️ Architecture

```
Microphone(s) → AudioEngine → Vosk TranscriptionEngine → UI Display
                  (PyAudio)        (KaldiRecognizer)         ↓
                                                        AutosaveManager
                                                             ↓
                                                         .txt file
```

| Component | File | Role |
|-----------|------|------|
| Entry point | [`main.py`](main.py) | Creates `QApplication`, wires all components, manages session lifecycle |
| UI | [`ui.py`](ui.py) | Main window, settings dialog, dark theme, button state machine |
| Audio capture | [`audio_engine.py`](audio_engine.py) | Lists input devices, opens multiple streams, applies gain, mixes to mono |
| Speech recognition | [`transcription_engine.py`](transcription_engine.py) | Loads Vosk model, feeds audio chunks, returns final & partial text |
| File transcription | [`file_transcriber.py`](file_transcriber.py) | Converts media files via FFmpeg, streams through Vosk, emits progress |
| Autosave | [`autosave.py`](autosave.py) | QTimer that periodically flushes buffered text to the open file |
| Settings | [`settings.py`](settings.py) | Reads/writes save path, autosave interval, and audio sources via QSettings |
| Tray icon | [`tray_icon.py`](tray_icon.py) | System tray with Start/Pause/Stop menu, state-aware icon colors |

### Threading Model

- **Main thread** — UI rendering, autosave timer, settings
- **QThread worker (live)** — audio capture + Vosk processing (emits signals to update UI)
- **QThread worker (file)** — FFmpeg conversion + chunked Vosk processing with progress (emits signals to update UI)

---

## ⚙️ Configuration

Open the **⚙ Settings** panel in the app to configure:

| Setting | Default | Description |
|---------|---------|-------------|
| Audio Sources | First available mic | Select and enable/disable multiple input devices with individual gain |
| Save Location | `./output/` | Where transcription `.txt` files are saved |
| Autosave Interval | 5 minutes | How often buffered text is flushed to disk |

Settings are persisted via `QSettings` and restored on next launch.

---

## 🔊 System Audio Capture

To transcribe system audio (meetings, YouTube, etc.):

| OS | Method |
|----|--------|
| **macOS** | Install [BlackHole](https://github.com/ExistentialAudio/BlackHole) + create Multi-Output Device |
| **Windows** | Enable Stereo Mix, or install [VB-CABLE](https://vb-audio.com/Cable/) |
| **Linux** | Use PulseAudio/PipeWire monitor source |

See [`setup.md`](setup.md) for detailed instructions per platform.

---

## 🔁 Auto-Start on Boot

| OS | Method | Details |
|----|--------|---------|
| **macOS** | Launch Agent | Run [`install_autostart.sh`](install_autostart.sh) |
| **Windows** | Startup folder / Task Scheduler | Create a `.bat` file (see [`setup.md`](setup.md)) |
| **Linux** | `.desktop` autostart / systemd | Create `~/.config/autostart/transcriber.desktop` (see [`setup.md`](setup.md)) |

---

## 📝 Output

### Live Recording

Each recording session creates a timestamped file:

```
output/transcription_20260217_153000.txt
```

- **Start** → creates a new file
- **Pause** → keeps the same file open
- **Stop** → finalizes and closes the file

### File Transcription

Each file transcription creates an output file named after the source:

```
output/meeting_recording_transcript_20260217_153000.txt
```

- **Transcribe File** → select media file → transcript saved automatically
- **Cancel** → stops mid-transcription, partial transcript is kept

---

## 🔗 Links

- [Vosk Speech Recognition](https://alphacephei.com/vosk/)
- [Vosk Models Download](https://alphacephei.com/vosk/models)
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)
- [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [BlackHole (macOS)](https://github.com/ExistentialAudio/BlackHole)

---

## 📄 License

This project is for personal use.
