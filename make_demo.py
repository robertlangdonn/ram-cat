#!/usr/bin/env python3
"""
make_demo.py — generates demo/ram-cat-demo.gif

Simulates a 12B model loading on Apple Silicon:
  😴 71% (idle) → 😸 loading → 😾 tight → 🙀 frazzled → 😱 PANIC

Works at 2x (800×56) then downscales to 400×28 for sharp text.
Uses cat PNG icons + Helvetica; Apple Color Emoji can't be loaded
by FreeType (SBIX/CBDT format).
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ── Dimensions ────────────────────────────────────────────────────────────────
SCALE    = 2
FINAL_W  = 400
FINAL_H  = 28
W, H     = FINAL_W * SCALE, FINAL_H * SCALE  # 800 × 56

# ── Colours ───────────────────────────────────────────────────────────────────
BG       = (28, 28, 30)
FG       = (255, 255, 255)
DIM      = (120, 120, 125)    # clock / secondary text
SPINNER_C = (200, 200, 205)   # slightly dimmed spinner

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_SIZE = 26                # at 2×; = 13px final
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
font      = ImageFont.truetype(FONT_PATH, FONT_SIZE)
font_dim  = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# ── Icon size ─────────────────────────────────────────────────────────────────
ICON_PX   = 40                # at 2×; = 20px final

# ── Spinner chars ─────────────────────────────────────────────────────────────
SPINNER = "⣾⣽⣻⢿⡿⣟⣯⣷"

# ── Load & cache mood icons at target size ────────────────────────────────────
_ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
_icons = {}

def _icon(name):
    if name not in _icons:
        src = Image.open(os.path.join(_ICONS_DIR, f"{name}.png")).convert("RGBA")
        _icons[name] = src.resize((ICON_PX, ICON_PX), Image.LANCZOS)
    return _icons[name]


# ── Frame builder ─────────────────────────────────────────────────────────────

def frame(mood, pct, spinner=""):
    """
    mood    : "sleepy" | "comfy" | "alert" | "frazzled" | "panic" | None (flash)
    pct     : integer free%
    spinner : one braille char, or ""
    Returns a 400×28 RGB PIL Image.
    """
    img = Image.new("RGBA", (W, H), (*BG, 255))
    d   = ImageDraw.Draw(img)

    # Right-side clock (static context, makes it look like a real menubar)
    CLOCK = "12:34 PM"
    R_MARGIN = 14 * SCALE  # 14px right margin at 2×
    GAP      = 18 * SCALE  # gap between clock and RAM Cat item

    w_clock = font_dim.getlength(CLOCK)
    x_clock = W - R_MARGIN - int(w_clock)
    y_text  = (H - 19) // 2   # 19 = measured text height at this size; center vertically

    d.text((x_clock, y_text), CLOCK, font=font_dim, fill=DIM)

    # RAM Cat item — right-align to the left of the clock
    if mood is not None:
        icon_img   = _icon(mood)
        prefix     = "RAM "
        suffix     = f" {pct}%"
        w_prefix   = int(font.getlength(prefix))
        w_icon     = ICON_PX
        w_spinner  = int(font.getlength(spinner)) if spinner else 0
        w_suffix   = int(font.getlength(suffix))
        total_w    = w_prefix + w_icon + w_spinner + w_suffix

        x = x_clock - GAP - total_w
        y_icon = (H - ICON_PX) // 2

        d.text((x, y_text), prefix, font=font, fill=FG)
        x += w_prefix

        img.paste(icon_img, (x, y_icon), icon_img)
        x += w_icon

        if spinner:
            d.text((x, y_text), spinner, font=font, fill=SPINNER_C)
            x += w_spinner

        d.text((x, y_text), suffix, font=font, fill=FG)

    else:
        # Flash frame — show "RAM     XX%" with icon gap blank
        prefix  = "RAM "
        suffix  = f" {pct}%"
        blank_w = ICON_PX
        total_w = int(font.getlength(prefix)) + blank_w + int(font.getlength(suffix))

        x = x_clock - GAP - total_w
        d.text((x, y_text), prefix, font=font, fill=DIM)
        x += int(font.getlength(prefix)) + blank_w
        d.text((x, y_text), suffix, font=font, fill=DIM)

    return img.resize((FINAL_W, FINAL_H), Image.LANCZOS).convert("RGB")


# ── Animation sequence ────────────────────────────────────────────────────────
#
# Each entry: (mood_or_None, free_pct, spinner_char, delay_ms)

def _spin(i):
    return SPINNER[i % len(SPINNER)]

SEQUENCE = [
    # ── Idle at 71% ─────────────────────────────────────────────────────────
    *[("sleepy",   71, "",       500)] * 3,

    # ── Flash: comfy ────────────────────────────────────────────────────────
    *[(("comfy" if i % 2 == 0 else None), 64, "", 100) for i in range(4)],

    # ── Comfy + spinner, RAM dropping ────────────────────────────────────────
    *[("comfy",    64 - i * 4,  _spin(i), 150) for i in range(5)],

    # ── Flash: alert ─────────────────────────────────────────────────────────
    *[(("alert" if i % 2 == 0 else None), 44, "", 100) for i in range(4)],

    # ── Alert + spinner ───────────────────────────────────────────────────────
    *[("alert",    44 - i * 4,  _spin(i), 150) for i in range(4)],

    # ── Flash: frazzled ───────────────────────────────────────────────────────
    *[(("frazzled" if i % 2 == 0 else None), 28, "", 100) for i in range(4)],

    # ── Frazzled + spinner ────────────────────────────────────────────────────
    *[("frazzled", 28 - i * 4,  _spin(i), 150) for i in range(4)],

    # ── PANIC flash (faster, more dramatic) ──────────────────────────────────
    *[(("panic" if i % 2 == 0 else None), 11, "", 75) for i in range(6)],

    # ── Hold at PANIC ─────────────────────────────────────────────────────────
    *[("panic",    10, "",       500)] * 4,
]


# ── Build and save ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ram-cat-demo.gif")

    print(f"Building {len(SEQUENCE)} frames...")
    frames  = []
    delays  = []
    for mood, pct, spin, delay in SEQUENCE:
        frames.append(frame(mood, pct, spin))
        delays.append(delay)

    print(f"Saving → {out_path}")
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
