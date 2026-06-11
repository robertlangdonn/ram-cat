#!/usr/bin/env python3
"""
make_demo.py — generates demo/ram-cat-demo.gif

Uses macOS AppKit (via PyObjC) to render text frames so real emoji appear
exactly as they do in the live menubar app. NSFont.systemFontOfSize_ uses
Apple Color Emoji automatically as a fallback — no separate emoji font needed.

Simulates a 12B model loading on Apple Silicon:
  😴 71% (idle) → 😸 loading + spinner → 😾 tight → 🙀 frazzled → 😱 PANIC
"""

import io, os
from AppKit import (
    NSImage, NSColor, NSFont, NSString, NSBezierPath,
    NSBitmapImageRep, NSForegroundColorAttributeName, NSFontAttributeName,
)
from Foundation import NSMakeSize, NSMakePoint
from PIL import Image

# ── Dimensions ────────────────────────────────────────────────────────────────
SCALE   = 2           # work at 2× for antialiasing
FW, FH  = 400, 28     # final output size
W,  H   = FW*SCALE, FH*SCALE

# ── Visual constants ──────────────────────────────────────────────────────────
BG          = (28/255,  28/255,  30/255)
FS          = 26                          # font size at 2× (= 13 px final)
Y_TEXT      = (H - FS) // 2 - 1          # vertical baseline (NSImage y=0 at bottom)
R_MARGIN    = 28                          # right margin at 2×
ITEM_GAP    = 36                          # gap between clock and RAM Cat at 2×

# ── Mood emoji map ────────────────────────────────────────────────────────────
MOOD_EMOJI = {
    "sleepy":   "😴",
    "comfy":    "😸",
    "alert":    "😾",
    "frazzled": "🙀",
    "panic":    "😱",
}

SPINNER = "⣾⣽⣻⢿⡿⣟⣯⣷"

# ── AppKit attribute dicts ────────────────────────────────────────────────────
def _attrs(color):
    return {
        NSFontAttributeName:            NSFont.systemFontOfSize_(FS),
        NSForegroundColorAttributeName: color,
    }

WHITE   = NSColor.whiteColor()
DIM     = NSColor.colorWithSRGBRed_green_blue_alpha_(0.55, 0.55, 0.58, 1.0)
SPINNER_COL = NSColor.colorWithSRGBRed_green_blue_alpha_(0.78, 0.78, 0.80, 1.0)

ATTRS_WHITE   = _attrs(WHITE)
ATTRS_DIM     = _attrs(DIM)
ATTRS_SPINNER = _attrs(SPINNER_COL)


def _tw(text, attrs=None):
    """Measure text width at 2× scale."""
    a = attrs or ATTRS_WHITE
    return NSString.stringWithString_(text).sizeWithAttributes_(a).width


def _draw(ns_draw, text, x, attrs=None):
    """Draw text at (x, Y_TEXT) and return new x."""
    a = attrs or ATTRS_WHITE
    NSString.stringWithString_(text).drawAtPoint_withAttributes_(
        NSMakePoint(x, Y_TEXT), a
    )
    return x + _tw(text, a)


def render(mood, pct, spinner="", flash_off=False):
    """
    mood     : key in MOOD_EMOJI (or any value when flash_off=True)
    pct      : integer free%
    spinner  : one braille char or ""
    flash_off: True → RAM Cat item invisible (blink-off frame)
    Returns a 400×28 RGB PIL Image.
    """
    ns_img = NSImage.alloc().initWithSize_(NSMakeSize(W, H))
    ns_img.lockFocus()

    # Background
    NSColor.colorWithSRGBRed_green_blue_alpha_(*BG, 1.0).setFill()
    NSBezierPath.fillRect_(((0, 0), (W, H)))

    # Clock (static, always visible)
    clock     = "12:34 PM"
    w_clock   = _tw(clock, ATTRS_DIM)
    x_clock   = W - R_MARGIN - w_clock
    _draw(None, clock, x_clock, ATTRS_DIM)

    # RAM Cat item
    if not flash_off:
        emoji    = MOOD_EMOJI.get(mood, "😴")
        prefix   = "RAM "
        content  = f"{emoji}{spinner}"
        free_gb  = pct / 100.0 * 16          # matches app title on a 16 GB Mac
        suffix   = f" {free_gb:.1f}G · {pct}% free"

        total_w  = (_tw(prefix) + _tw(content) +
                    (_tw(spinner, ATTRS_SPINNER) - _tw(spinner) if spinner else 0) +
                    _tw(suffix))
        # re-measure properly
        total_w = _tw(prefix) + _tw(content) + _tw(suffix)

        x = x_clock - ITEM_GAP - total_w
        x = _draw(None, prefix,  x, ATTRS_WHITE)
        x = _draw(None, emoji,   x, ATTRS_WHITE)
        if spinner:
            x = _draw(None, spinner, x, ATTRS_SPINNER)
        _draw(None, suffix, x, ATTRS_WHITE)

    ns_img.unlockFocus()

    rep  = NSBitmapImageRep.imageRepWithData_(ns_img.TIFFRepresentation())
    data = rep.representationUsingType_properties_(4, {})   # 4 = PNG
    return (Image.open(io.BytesIO(bytes(data)))
                 .resize((FW, FH), Image.LANCZOS)
                 .convert("RGB"))


# ── Animation sequence ────────────────────────────────────────────────────────
# (mood, pct, spinner, flash_off, delay_ms)

def _sp(i): return SPINNER[i % len(SPINNER)]

SEQUENCE = [
    # Idle
    *[("sleepy",   71, "",    False, 500)] * 3,
    # Flash → comfy
    *[("comfy",    64, "",    i%2==1, 100) for i in range(4)],
    # Comfy + spinner, RAM dropping
    *[("comfy",    64-i*4, _sp(i), False, 150) for i in range(5)],
    # Flash → alert
    *[("alert",    44, "",    i%2==1, 100) for i in range(4)],
    # Alert + spinner
    *[("alert",    44-i*4, _sp(i), False, 150) for i in range(4)],
    # Flash → frazzled
    *[("frazzled", 28, "",    i%2==1, 100) for i in range(4)],
    # Frazzled + spinner
    *[("frazzled", 28-i*4, _sp(i), False, 150) for i in range(4)],
    # PANIC flash (faster, more dramatic)
    *[("panic",    11, "",    i%2==1,  75) for i in range(6)],
    # Hold at PANIC
    *[("panic",    10, "",    False,  500)] * 4,
]


# ── Build and save ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "demo-v3.gif")

    print(f"Building {len(SEQUENCE)} frames with AppKit emoji rendering...")
    frames, delays = [], []
    for mood, pct, spin, flash_off, delay in SEQUENCE:
        frames.append(render(mood, pct, spin, flash_off))
        delays.append(delay)
        print(f"  {'  ' if flash_off else MOOD_EMOJI.get(mood,'?')} {pct}% {spin}",
              end="\r")

    print(f"\nSaving → {out_path}")
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=delays,
        optimize=True,
    )
    size_kb = os.path.getsize(out_path) // 1024
    print(f"Done. {size_kb} KB, {sum(delays)/1000:.1f}s loop")
