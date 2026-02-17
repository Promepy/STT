# 🎙️ Transcriber — Setup Guide

A step-by-step guide to install and run the **Transcriber** app on **Windows**, **macOS**, and **Linux**.

Transcriber is a fully offline, real-time speech-to-text desktop app built with Python, PyQt6, Vosk, and PyAudio. It captures microphone (and optionally system audio) and transcribes speech to text files locally — no internet required.

---

## 📦 What's in the Zip

After extracting the zip, you should have this structure:

```
Transcriber/
├── main.py                  # Entry point
├── ui.py                    # PyQt6 UI
├── audio_engine.py          # Mic capture & mixing
├── transcription_engine.py  # Vosk integration
├── autosave.py              # Auto-save manager
├── settings.py              # Persistent settings
├── tray_icon.py             # System tray icon
├── generate_icon.py         # Icon generator (optional)
├── assets/                  # Tray icon images
│   ├── tray_idle_32.png
│   ├── tray_recording_32.png
│   └── tray_paused_32.png
├── models/                  # Vosk model (see Step 3)
│   └── vosk-model-small-en-us-0.15/
├── output/                  # Transcription output folder
└── setup.md                 # This file
```

---

## 📋 Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9 or higher | Must include `pip` and `venv` |
| PortAudio | Latest | Required by PyAudio for audio capture |
| Git | Optional | Only if cloning instead of using zip |

---

# 🍎 macOS Setup

## Step 1 — Install Python

If you don't have Python 3.9+, install it via Homebrew:

```bash
brew install python@3.11
```

Verify:

```bash
python3 --version
```

## Step 2 — Install PortAudio

PyAudio needs PortAudio. Install it via Homebrew:

```bash
brew install portaudio
```

## Step 3 — Download the Vosk Model

Download the small English model from:

> **https://alphacephei.com/vosk/models**

Look for: **`vosk-model-small-en-us-0.15`**

Direct link:
```
https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
```

Extract the model folder and place it inside the `models/` directory:

```
Transcriber/
└── models/
    └── vosk-model-small-en-us-0.15/
        ├── conf/
        ├── graph/
        ├── am/
        └── ...
```

> **Tip:** You can use a larger model for better accuracy. Just place it in `models/` and rename the folder to `vosk-model-small-en-us-0.15`, or update the model path in `transcription_engine.py`.

## Step 4 — Create Virtual Environment & Install Dependencies

Open Terminal, navigate to the Transcriber folder, and run:

```bash
cd /path/to/Transcriber

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install vosk pyaudio PyQt6
```

## Step 5 — Run the App

```bash
cd /path/to/Transcriber
source venv/bin/activate
python main.py
```

The Transcriber window will appear, and a tray icon will show in the menu bar.

## Step 6 — System Audio Capture (Optional)

To transcribe system audio (meetings, videos, etc.), you need **BlackHole** — a free virtual audio driver.

### Install BlackHole

```bash
brew install blackhole-2ch
sudo reboot
```

### Create a Multi-Output Device

This lets you hear audio AND capture it simultaneously.

1. Open **Audio MIDI Setup** (Spotlight → "Audio MIDI Setup")
2. Click **+** → **Create Multi-Output Device**
3. Check both:
   - ☑ Your speakers/headphones
   - ☑ BlackHole 2ch
4. Make sure speakers are listed **first** (drag to reorder)
5. Right-click the Multi-Output Device → **Use This Device For Sound Output**

### Enable in Transcriber

1. Open Transcriber → click ⚙ **Settings**
2. Under **Audio Sources**, check **BlackHole 2ch**
3. Adjust gain as needed (80% recommended for system audio)
4. Click **Save**

> For full details, see `system-audio-setup.md`.

## Step 7 — Auto-Start on Boot (macOS)

To make Transcriber launch automatically when you log in, create a **Launch Agent**.

### Install Auto-Start

```bash
cd /path/to/Transcriber

# Make the script executable
chmod +x install_autostart.sh

# Run it
./install_autostart.sh
```

This creates a LaunchAgent plist at `~/Library/LaunchAgents/com.transcriber.agent.plist`.

### What it does

- Launches `main.py` using the project's virtual environment Python
- Runs automatically every time you log in
- Logs output to `~/Library/Logs/Transcriber/`

### Manual Control

```bash
# Stop the running instance
launchctl stop com.transcriber.agent

# Start it manually
launchctl start com.transcriber.agent

# Remove auto-start entirely
./install_autostart.sh remove
```

### Alternative: Login Items (GUI method)

If you prefer not to use the script:

1. Open **System Settings** → **General** → **Login Items**
2. Click **+**
3. Navigate to your Transcriber folder
4. Select `main.py` (this may not work reliably for Python scripts — the Launch Agent method above is recommended)

---

# 🪟 Windows Setup

## Step 1 — Install Python

1. Download Python 3.11+ from **https://www.python.org/downloads/windows/**
2. Run the installer
3. **Important:** Check ✅ **"Add Python to PATH"** during installation
4. Complete the installation

Verify in Command Prompt or PowerShell:

```cmd
python --version
```

## Step 2 — Download the Vosk Model

Download the small English model:

```
https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
```

Extract it into the `models/` folder:

```
Transcriber\
└── models\
    └── vosk-model-small-en-us-0.15\
        ├── conf\
        ├── graph\
        ├── am\
        └── ...
```

## Step 3 — Create Virtual Environment & Install Dependencies

Open **Command Prompt** or **PowerShell**, navigate to the Transcriber folder:

```cmd
cd C:\path\to\Transcriber

:: Create virtual environment
python -m venv venv

:: Activate it
venv\Scripts\activate

:: Install dependencies
pip install vosk pyaudio PyQt6
```

> **Note on PyAudio:** On Windows, `pip install pyaudio` usually works directly without needing PortAudio separately. If you get errors, install the prebuilt wheel:
>
> ```cmd
> pip install pipwin
> pipwin install pyaudio
> ```
>
> Or download the `.whl` file from [Christoph Gohlke's page](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) matching your Python version and install it with:
>
> ```cmd
> pip install PyAudio‑0.2.14‑cp311‑cp311‑win_amd64.whl
> ```

## Step 4 — Run the App

```cmd
cd C:\path\to\Transcriber
venv\Scripts\activate
python main.py
```

## Step 5 — System Audio Capture (Optional)

Windows has a built-in feature called **Stereo Mix** that can capture system audio.

### Enable Stereo Mix

1. Right-click the **🔊 speaker icon** in the taskbar → **Sound Settings**
2. Scroll down → **More sound settings** (or open Control Panel → Sound)
3. Go to the **Recording** tab
4. Right-click in the empty area → check **Show Disabled Devices**
5. Right-click **Stereo Mix** → **Enable**
6. Right-click **Stereo Mix** → **Properties** → set the level to 100

### Use in Transcriber

Once enabled, Stereo Mix will appear as an input device in Transcriber's Settings → Audio Sources. Check it to capture system audio.

> **If Stereo Mix is not available:** Some audio drivers (especially Realtek on laptops) hide it. You can use the free **VB-CABLE Virtual Audio Device** instead:
>
> 1. Download from **https://vb-audio.com/Cable/**
> 2. Install and reboot
> 3. Set your system output to **CABLE Input (VB-Audio Virtual Cable)**
> 4. In Transcriber, select **CABLE Output** as the input source
>
> Note: With VB-CABLE, you won't hear audio from speakers unless you also set up monitoring in the sound settings.

## Step 6 — Auto-Start on Boot (Windows)

### Method 1: Startup Folder (Recommended)

Create a batch file to run Transcriber and place it in the Startup folder.

**1. Create `start_transcriber.bat`:**

Create a file named `start_transcriber.bat` in the Transcriber folder with this content:

```bat
@echo off
cd /d "C:\path\to\Transcriber"
call venv\Scripts\activate
start /min python main.py
```

> Replace `C:\path\to\Transcriber` with the actual path.

**2. Create a shortcut in the Startup folder:**

1. Press **Win + R**, type `shell:startup`, press Enter
2. This opens the Startup folder
3. Right-click inside → **New** → **Shortcut**
4. Browse to `C:\path\to\Transcriber\start_transcriber.bat`
5. Name it "Transcriber"
6. Click Finish

Now Transcriber will start automatically every time you log in.

### Method 2: Task Scheduler (Advanced)

For more control (e.g., delayed start, run hidden):

1. Open **Task Scheduler** (search in Start Menu)
2. Click **Create Basic Task**
3. Name: `Transcriber`
4. Trigger: **When I log on**
5. Action: **Start a program**
6. Program/script: `C:\path\to\Transcriber\venv\Scripts\pythonw.exe`
7. Arguments: `main.py`
8. Start in: `C:\path\to\Transcriber`
9. Click Finish

> **Tip:** Use `pythonw.exe` instead of `python.exe` to run without a console window.

### To Remove Auto-Start

- **Startup Folder method:** Press Win + R → `shell:startup` → delete the shortcut
- **Task Scheduler method:** Open Task Scheduler → find "Transcriber" → Delete

---

# 🐧 Linux Setup

## Step 1 — Install Python and System Dependencies

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv portaudio19-dev
```

### Fedora

```bash
sudo dnf install python3 python3-pip python3-virtualenv portaudio-devel
```

### Arch Linux

```bash
sudo pacman -S python python-pip portaudio
```

## Step 2 — Download the Vosk Model

```bash
cd /path/to/Transcriber/models

wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
```

Resulting structure:

```
Transcriber/
└── models/
    └── vosk-model-small-en-us-0.15/
```

## Step 3 — Create Virtual Environment & Install Dependencies

```bash
cd /path/to/Transcriber

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install vosk pyaudio PyQt6
```

> **Note:** If `pip install pyaudio` fails, make sure `portaudio19-dev` (Debian/Ubuntu) or `portaudio-devel` (Fedora) is installed. You may also need:
>
> ```bash
> sudo apt install python3-dev  # Ubuntu/Debian
> ```

## Step 4 — Run the App

```bash
cd /path/to/Transcriber
source venv/bin/activate
python main.py
```

## Step 5 — System Audio Capture (Optional)

On Linux, **PulseAudio** (or PipeWire) can create a virtual monitor device to capture system audio.

### Using PulseAudio Monitor

PulseAudio automatically creates a "Monitor" source for each output device. This allows you to capture whatever audio is playing on your speakers.

**1. Find the monitor source:**

```bash
pactl list short sources
```

Look for something like:

```
alsa_output.pci-0000_00_1f.3.analog-stereo.monitor
```

**2. Use in Transcriber:**

The monitor source will appear as an input device in Transcriber's Settings → Audio Sources. Enable it to capture system audio.

### Using PipeWire (Modern Linux)

If you're on PipeWire (default on Fedora 34+, Ubuntu 22.10+):

```bash
# List available sources
pw-cli list-objects | grep -A2 "node.name"
```

PipeWire is compatible with PulseAudio, so monitor sources work the same way.

### Optional: PulseAudio Virtual Sink (Advanced)

If you want a dedicated virtual device:

```bash
# Load a virtual null sink
pactl load-module module-null-sink sink_name=transcriber_sink sink_properties=device.description="Transcriber_Sink"

# Route system audio to it (replace with your actual sink)
pactl set-default-sink transcriber_sink

# The corresponding monitor source will be available as input:
# transcriber_sink.monitor
```

To remove it:

```bash
pactl unload-module module-null-sink
```

## Step 6 — Auto-Start on Boot (Linux)

### Method 1: Desktop Autostart File (Recommended)

Works on GNOME, KDE, XFCE, and most desktop environments.

**1. Create the autostart file:**

```bash
mkdir -p ~/.config/autostart
```

**2. Create `transcriber.desktop`:**

```bash
cat > ~/.config/autostart/transcriber.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Transcriber
Comment=Offline speech-to-text transcription
Exec=/path/to/Transcriber/venv/bin/python /path/to/Transcriber/main.py
Path=/path/to/Transcriber
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
```

> Replace `/path/to/Transcriber` with the actual absolute path.

**3. Make it executable:**

```bash
chmod +x ~/.config/autostart/transcriber.desktop
```

### Method 2: Systemd User Service (Advanced)

For headless or more controlled setups:

**1. Create the service file:**

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/transcriber.service << 'EOF'
[Unit]
Description=Transcriber - Offline Speech to Text
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=/path/to/Transcriber
ExecStart=/path/to/Transcriber/venv/bin/python /path/to/Transcriber/main.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=QT_QPA_PLATFORM=xcb

[Install]
WantedBy=default.target
EOF
```

> Replace `/path/to/Transcriber` with the actual absolute path.

**2. Enable and start:**

```bash
systemctl --user daemon-reload
systemctl --user enable transcriber.service
systemctl --user start transcriber.service
```

**3. Check status:**

```bash
systemctl --user status transcriber.service
```

**4. View logs:**

```bash
journalctl --user -u transcriber.service -f
```

### To Remove Auto-Start

- **Desktop file method:** `rm ~/.config/autostart/transcriber.desktop`
- **Systemd method:**
  ```bash
  systemctl --user disable transcriber.service
  systemctl --user stop transcriber.service
  rm ~/.config/systemd/user/transcriber.service
  systemctl --user daemon-reload
  ```

---

# 🔧 Troubleshooting

## All Platforms

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'vosk'` | Activate the venv first: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows) |
| `FileNotFoundError: Vosk model not found` | Ensure the model is extracted in `models/vosk-model-small-en-us-0.15/` |
| `No audio input devices found` | Check that your microphone is connected and not muted |
| App window doesn't appear | Check `error.log` in the Transcriber folder for details |
| Tray icon not visible | Some Linux DEs need a tray extension (e.g., AppIndicator on GNOME) |

## macOS Specific

| Issue | Solution |
|-------|----------|
| PyAudio install fails | Run `brew install portaudio` first |
| BlackHole not appearing | Reboot after install; check with `kextstat \| grep BlackHole` |
| No system audio being captured | Set system output to Multi-Output Device (System Settings → Sound → Output) |
| LaunchAgent not working | Check logs at `~/Library/Logs/Transcriber/` |

## Windows Specific

| Issue | Solution |
|-------|----------|
| PyAudio install fails | Try `pip install pipwin && pipwin install pyaudio` |
| `python` not found | Reinstall Python and check ✅ "Add to PATH" |
| Stereo Mix not available | Use VB-CABLE (see Step 5 above) |
| Console window stays open | Use `pythonw.exe` instead of `python.exe` |

## Linux Specific

| Issue | Solution |
|-------|----------|
| PyAudio install fails | Install `portaudio19-dev` and `python3-dev` |
| No system audio monitor | Ensure PulseAudio/PipeWire is running: `pulseaudio --check` |
| Qt platform error | Install: `sudo apt install libxcb-xinerama0 libxcb-cursor0` |
| Systemd service won't start | Check `DISPLAY` and `QT_QPA_PLATFORM` environment variables |

---

# 📝 Quick Reference

## Commands at a Glance

### macOS

```bash
# First time setup
brew install portaudio
cd /path/to/Transcriber
python3 -m venv venv
source venv/bin/activate
pip install vosk pyaudio PyQt6

# Run
source venv/bin/activate && python main.py

# Auto-start
./install_autostart.sh

# Remove auto-start
./install_autostart.sh remove
```

### Windows

```cmd
:: First time setup
cd C:\path\to\Transcriber
python -m venv venv
venv\Scripts\activate
pip install vosk pyaudio PyQt6

:: Run
venv\Scripts\activate && python main.py

:: Auto-start → place .bat shortcut in shell:startup
```

### Linux

```bash
# First time setup (Ubuntu/Debian)
sudo apt install python3 python3-pip python3-venv portaudio19-dev
cd /path/to/Transcriber
python3 -m venv venv
source venv/bin/activate
pip install vosk pyaudio PyQt6

# Run
source venv/bin/activate && python main.py

# Auto-start → create ~/.config/autostart/transcriber.desktop
```

---

## 🔗 Useful Links

- [Vosk Models (download)](https://alphacephei.com/vosk/models)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [BlackHole (macOS system audio)](https://github.com/ExistentialAudio/BlackHole)
- [VB-CABLE (Windows virtual audio)](https://vb-audio.com/Cable/)
