#!/usr/bin/env python3
"""
generate_icon.py — Generate app.icns and tray bar icon PNGs for the Transcriber app.

Uses Pillow to draw a microphone icon, then macOS sips+iconutil to create .icns.

Usage:
    python generate_icon.py
"""

import os
import subprocess
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw


ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def draw_mic_icon(size: int, bg_color: str = "#1a1a1a", fg_color: str = "#2ecc71") -> Image.Image:
    """Draw a simple microphone icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    margin = int(size * 0.06)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=bg_color)

    # Microphone body (rounded rectangle)
    cx, cy = size // 2, size // 2
    mic_w = int(size * 0.22)
    mic_h = int(size * 0.32)
    mic_r = int(mic_w * 0.45)
    mic_top = cy - int(size * 0.22)
    draw.rounded_rectangle(
        [cx - mic_w, mic_top, cx + mic_w, mic_top + mic_h],
        radius=mic_r, fill=fg_color
    )

    # Microphone arc (the holder)
    arc_w = int(size * 0.28)
    arc_top = cy - int(size * 0.18)
    arc_bot = cy + int(size * 0.14)
    line_w = max(2, int(size * 0.04))
    draw.arc(
        [cx - arc_w, arc_top, cx + arc_w, arc_bot],
        start=0, end=180, fill=fg_color, width=line_w
    )

    # Stand (vertical line)
    stand_top = arc_bot - line_w // 2
    stand_bot = cy + int(size * 0.26)
    draw.line([cx, stand_top, cx, stand_bot], fill=fg_color, width=line_w)

    # Base (horizontal line)
    base_w = int(size * 0.15)
    draw.line([cx - base_w, stand_bot, cx + base_w, stand_bot], fill=fg_color, width=line_w)

    return img


def generate_app_icon():
    """Generate app.icns using iconutil."""
    iconset_dir = os.path.join(ASSETS_DIR, "app.iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    # Sizes required for .icns
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for s in sizes:
        img = draw_mic_icon(s)
        img.save(os.path.join(iconset_dir, f"icon_{s}x{s}.png"))
        # @2x versions
        if s <= 512:
            img2x = draw_mic_icon(s * 2)
            img2x.save(os.path.join(iconset_dir, f"icon_{s}x{s}@2x.png"))

    # Use iconutil to create .icns
    icns_path = os.path.join(ASSETS_DIR, "app.icns")
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
            check=True, capture_output=True
        )
        print(f"✅ Created {icns_path}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  iconutil failed: {e.stderr.decode()}")
        # Fallback: just use the 512px PNG
        fallback = os.path.join(iconset_dir, "icon_512x512.png")
        print(f"   Using fallback PNG: {fallback}")


def generate_tray_icons():
    """Generate tray bar icons for different states."""
    os.makedirs(ASSETS_DIR, exist_ok=True)

    states = {
        "tray_idle": ("#2a2a2a", "#888888"),      # gray mic on dark bg
        "tray_recording": ("#2a2a2a", "#e74c3c"),  # red mic
        "tray_paused": ("#2a2a2a", "#f1c40f"),     # yellow mic
    }

    for name, (bg, fg) in states.items():
        for size in [16, 32, 64]:
            img = draw_mic_icon(size, bg_color=bg, fg_color=fg)
            path = os.path.join(ASSETS_DIR, f"{name}_{size}.png")
            img.save(path)
        print(f"✅ Created {name} icons")


if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    generate_tray_icons()
    generate_app_icon()
    print("\nDone! Icons are in:", ASSETS_DIR)
