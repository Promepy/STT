#!/bin/bash
# install_autostart.sh — Install/uninstall Transcriber as a macOS Launch Agent
#
# Usage:
#   ./install_autostart.sh          # Install (auto-start on login)
#   ./install_autostart.sh remove   # Uninstall
#
set -e

LABEL="com.transcriber.agent"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/$LABEL.plist"
STT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$STT_DIR/venv/bin/python"
LOG_DIR="$HOME/Library/Logs/Transcriber"

# ---- Uninstall ----
if [ "$1" = "remove" ] || [ "$1" = "uninstall" ]; then
    echo "🗑  Removing Transcriber auto-start..."
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
    rm -f "$PLIST_FILE"
    echo "✅ Removed. Transcriber will no longer start on login."
    exit 0
fi

# ---- Install ----
echo "📦 Installing Transcriber as macOS Login Item..."

# Verify venv exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python venv not found at: $PYTHON"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"

# Create the Launch Agent plist
mkdir -p "$PLIST_DIR"
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$STT_DIR/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$STT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/transcriber.log</string>

    <key>StandardErrorPath</key>
    <string>$LOG_DIR/transcriber.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>QT_MAC_WANTS_LAYER</key>
        <string>1</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
EOF

# Load it now
launchctl bootstrap "gui/$(id -u)" "$PLIST_FILE" 2>/dev/null || \
    launchctl load "$PLIST_FILE" 2>/dev/null || true

echo ""
echo "✅ Transcriber will now auto-start when you log in!"
echo ""
echo "   Plist:   $PLIST_FILE"
echo "   Logs:    $LOG_DIR/"
echo ""
echo "   To stop:    launchctl stop $LABEL"
echo "   To start:   launchctl start $LABEL"
echo "   To remove:  ./install_autostart.sh remove"
