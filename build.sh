#!/bin/bash
# build.sh — Build the Transcriber as a standalone macOS .app
#
# Usage:
#   ./build.sh
#
# Output:
#   dist/Transcriber.app
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Building Transcriber.app..."

# Ensure we're in the venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install PyInstaller if needed
if ! python -m PyInstaller --version &>/dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Generate icons if not present
if [ ! -f "assets/app.icns" ]; then
    echo "🎨 Generating icons..."
    python generate_icon.py
fi

# Clean previous builds
rm -rf build dist

# Find vosk native library path
VOSK_DIR=$(python -c "import vosk, os; print(os.path.dirname(vosk.__file__))")
echo "   Vosk dir: $VOSK_DIR"

# Run PyInstaller
echo "📦 Packaging with PyInstaller..."
python -m PyInstaller \
    --name "Transcriber" \
    --windowed \
    --icon "assets/app.icns" \
    --osx-bundle-identifier "com.transcriber.app" \
    --add-data "models:models" \
    --add-data "assets:assets" \
    --add-binary "${VOSK_DIR}/libvosk.dyld:vosk" \
    --collect-all "vosk" \
    --hidden-import "vosk" \
    --hidden-import "pyaudio" \
    --noconfirm \
    --clean \
    main.py

# ---- Post-build: fix macOS Launch Services compatibility ----
APP_DIR="dist/Transcriber.app"
MACOS_DIR="$APP_DIR/Contents/MacOS"
PLIST="$APP_DIR/Contents/Info.plist"

echo "🔧 Applying macOS fixes..."

# Rename the PyInstaller binary and create a shell wrapper
# This fixes SIGSEGV in Qt's darwin permission plugin when launched via Finder/open
mv "$MACOS_DIR/Transcriber" "$MACOS_DIR/Transcriber-bin"
cat > "$MACOS_DIR/Transcriber" << 'WRAPPER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export QT_MAC_WANTS_LAYER=1
exec "$DIR/Transcriber-bin" "$@"
WRAPPER
chmod +x "$MACOS_DIR/Transcriber"

# Patch Info.plist
/usr/libexec/PlistBuddy -c "Add :NSMicrophoneUsageDescription string 'Transcriber needs microphone access for speech-to-text.'" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString 1.0.0" "$PLIST"

# Re-sign after modifications
codesign --force --deep --sign - "$APP_DIR"

echo ""
echo "✅ Build complete!"
echo "   App:  dist/Transcriber.app"
echo ""
echo "To install:"
echo "   cp -r dist/Transcriber.app /Applications/"
echo ""
echo "To run:"
echo "   open dist/Transcriber.app"
