#!/usr/bin/env python3
"""
Generate 5 cat mood icons for the RAM Cat menubar app.
Draws at 4x (176px) and downscales to 44px for Retina sharpness.

Moods: sleepy, comfy, alert, frazzled, panic
Output: icons/sleepy.png  icons/comfy.png  icons/alert.png
        icons/frazzled.png  icons/panic.png
"""

import os
from PIL import Image, ImageDraw, ImageFilter

S = 4          # scale factor
W = 44 * S     # working canvas: 176px → downscale to 44px
OUT_SIZE = 44
OUT_DIR = os.path.join(os.path.dirname(__file__), "icons")

# Palette
FUR       = (240, 200, 155, 255)
FUR_DARK  = (200, 155, 100, 255)
EAR_PINK  = (255, 175, 185, 255)
OUTLINE   = (90,  55,  25,  255)
NOSE      = (225, 115, 125, 255)
WHITE     = (255, 255, 255, 255)
PUPIL     = (30,  20,  10,  255)
IRIS_CALM = (100, 165, 90,  255)   # green — relaxed
IRIS_WIDE = (80,  140, 200, 255)   # blue — alarmed
MOUTH_C   = (100,  60,  30,  255)
BLUSH     = (255, 160, 150, 120)
ZZZ       = (160, 140, 200, 255)
SWEAT     = (160, 210, 255, 255)


def canvas():
    return Image.new("RGBA", (W, W), (0, 0, 0, 0))


def base(draw, ears_up=True, ear_squish=False):
    """Head, ears, nose — shared by all moods."""
    cx, cy = W // 2, W // 2 + 4 * S

    # Head
    hr = 27 * S
    draw.ellipse(
        [cx - hr, cy - hr + 2*S, cx + hr, cy + hr + 2*S],
        fill=FUR, outline=OUTLINE, width=max(1, S // 2),
    )

    # Ears
    if ear_squish:   # panic — ears flatten back
        le = [(cx-26*S, cy-18*S), (cx-16*S, cy-30*S), (cx-6*S,  cy-20*S)]
        re = [(cx+26*S, cy-18*S), (cx+16*S, cy-30*S), (cx+6*S,  cy-20*S)]
        lei = [(cx-23*S, cy-19*S), (cx-16*S, cy-27*S), (cx-9*S,  cy-21*S)]
        rei = [(cx+23*S, cy-19*S), (cx+16*S, cy-27*S), (cx+9*S,  cy-21*S)]
    else:
        le  = [(cx-26*S, cy-20*S), (cx-14*S, cy-34*S), (cx-4*S,  cy-20*S)]
        re  = [(cx+26*S, cy-20*S), (cx+14*S, cy-34*S), (cx+4*S,  cy-20*S)]
        lei = [(cx-23*S, cy-21*S), (cx-14*S, cy-30*S), (cx-7*S,  cy-21*S)]
        rei = [(cx+23*S, cy-21*S), (cx+14*S, cy-30*S), (cx+7*S,  cy-21*S)]

    for pts in (le, re):
        draw.polygon(pts, fill=FUR_DARK, outline=OUTLINE)
    for pts in (lei, rei):
        draw.polygon(pts, fill=EAR_PINK)

    # Nose
    draw.polygon(
        [(cx, cy+4*S), (cx-3*S, cy-1*S), (cx+3*S, cy-1*S)],
        fill=NOSE,
    )

    return cx, cy


def eye_open(draw, x, y, r, iris=IRIS_CALM, pupil_r_frac=0.45):
    """Open circular eye."""
    draw.ellipse([x-r, y-r, x+r, y+r], fill=WHITE, outline=OUTLINE, width=max(1, S//2))
    ir = int(r * 0.72)
    draw.ellipse([x-ir, y-ir, x+ir, y+ir], fill=iris)
    pr = int(r * pupil_r_frac)
    draw.ellipse([x-pr, y-pr, x+pr, y+pr], fill=PUPIL)
    # highlight
    hl = max(2, int(r * 0.22))
    draw.ellipse([x-r//3-hl, y-r//2-hl, x-r//3+hl, y-r//2+hl], fill=WHITE)


def eye_closed(draw, x, y, r):
    """Closed eye — curved line (happy squint)."""
    draw.arc([x-r, y-r//2, x+r, y+r//2], start=0, end=180,
             fill=OUTLINE, width=max(1, S//2))


def eye_line(draw, x, y, r):
    """Straight line — sleepy."""
    draw.line([x-r, y, x+r, y], fill=OUTLINE, width=max(1, S//2))


def mouth_smile(draw, cx, cy, sad=False):
    if sad:
        draw.arc([cx-5*S, cy+4*S, cx+5*S, cy+10*S],
                 start=180, end=360, fill=MOUTH_C, width=max(1, S//2))
    else:
        draw.arc([cx-5*S, cy+4*S, cx+5*S, cy+10*S],
                 start=0, end=180, fill=MOUTH_C, width=max(1, S//2))


def mouth_open(draw, cx, cy, size=4):
    """Panic open-mouth O."""
    s = size * S
    draw.ellipse([cx-s, cy+3*S, cx+s, cy+3*S+s*2],
                 fill=(50, 20, 10, 255), outline=MOUTH_C, width=max(1, S//2))


def finish(img):
    """Downscale to OUT_SIZE with high-quality antialiasing."""
    return img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)


def blush_marks(draw, cx, cy):
    for dx in (-14*S, 14*S):
        for px in range(-3*S, 3*S):
            for py in range(-S, S):
                alpha = max(0, 80 - int((px**2 + py**2)**0.5 * 8))
                if alpha > 0:
                    draw.point([cx+dx+px, cy+3*S+py],
                               fill=(*BLUSH[:3], alpha))


# ─── MOOD 1: SLEEPY ──────────────────────────────────────────────────────────
def make_sleepy():
    img = canvas()
    d = ImageDraw.Draw(img)
    cx, cy = base(d)

    ey = cy - 5 * S
    eye_line(d, cx - 12*S, ey, 7*S)
    eye_line(d, cx + 12*S, ey, 7*S)

    # droopy lids
    d.arc([cx-19*S, ey-3*S, cx-5*S, ey+3*S], start=0, end=180,
          fill=FUR_DARK, width=S)
    d.arc([cx+5*S,  ey-3*S, cx+19*S, ey+3*S], start=0, end=180,
          fill=FUR_DARK, width=S)

    mouth_smile(d, cx, cy)

    # ZZZ
    for i, ch in enumerate("z z"):
        sz = (5 - i) * S
        d.text((cx + 18*S + i*5*S, cy - 22*S - i*4*S), ch,
               fill=(*ZZZ[:3], 200))

    return finish(img)


# ─── MOOD 2: COMFY ───────────────────────────────────────────────────────────
def make_comfy():
    img = canvas()
    d = ImageDraw.Draw(img)
    cx, cy = base(d)

    ey = cy - 5 * S
    eye_open(d, cx - 12*S, ey, 7*S, IRIS_CALM, 0.4)
    eye_open(d, cx + 12*S, ey, 7*S, IRIS_CALM, 0.4)
    blush_marks(d, cx, cy)
    mouth_smile(d, cx, cy)
    return finish(img)


# ─── MOOD 3: ALERT ───────────────────────────────────────────────────────────
def make_alert():
    img = canvas()
    d = ImageDraw.Draw(img)
    cx, cy = base(d)

    ey = cy - 5 * S
    eye_open(d, cx - 12*S, ey, 8*S, IRIS_CALM, 0.5)
    eye_open(d, cx + 12*S, ey, 8*S, IRIS_CALM, 0.5)
    mouth_smile(d, cx, cy, sad=False)

    # sweat drop
    d.ellipse([cx+20*S, cy-16*S, cx+24*S, cy-12*S], fill=(*SWEAT[:3], 200))
    d.polygon([(cx+22*S, cy-20*S), (cx+19*S, cy-13*S), (cx+25*S, cy-13*S)],
              fill=(*SWEAT[:3], 200))
    return finish(img)


# ─── MOOD 4: FRAZZLED ────────────────────────────────────────────────────────
def make_frazzled():
    img = canvas()
    d = ImageDraw.Draw(img)
    cx, cy = base(d)

    ey = cy - 5 * S
    # wide eyes, blue iris
    eye_open(d, cx - 12*S, ey, 9*S, IRIS_WIDE, 0.35)
    eye_open(d, cx + 12*S, ey, 9*S, IRIS_WIDE, 0.35)
    mouth_smile(d, cx, cy, sad=True)

    # stress lines on forehead
    for offset in (-6*S, 6*S):
        x0 = cx + offset
        d.line([x0, cy-26*S, x0+2*S, cy-20*S], fill=OUTLINE, width=max(1, S//2))

    # multiple sweat drops
    for dx, dy in [(18*S, -18*S), (22*S, -10*S)]:
        d.ellipse([cx+dx, cy+dy, cx+dx+4*S, cy+dy+4*S], fill=(*SWEAT[:3], 200))

    return finish(img)


# ─── MOOD 5: PANIC ───────────────────────────────────────────────────────────
def make_panic():
    img = canvas()
    d = ImageDraw.Draw(img)
    cx, cy = base(d, ear_squish=True)

    ey = cy - 4 * S
    # massive eyes, tiny pupils = full dread
    eye_open(d, cx - 12*S, ey, 11*S, IRIS_WIDE, 0.2)
    eye_open(d, cx + 12*S, ey, 11*S, IRIS_WIDE, 0.2)
    mouth_open(d, cx, cy, size=5)

    # lots of sweat
    for dx, dy in [(16*S, -20*S), (20*S, -12*S), (23*S, -4*S)]:
        d.ellipse([cx+dx, cy+dy, cx+dx+5*S, cy+dy+5*S], fill=(*SWEAT[:3], 220))
        d.polygon([(cx+dx+2*S, cy+dy-4*S), (cx+dx-1*S, cy+dy+1*S), (cx+dx+5*S, cy+dy+1*S)],
                  fill=(*SWEAT[:3], 220))

    # action lines
    for angle_offset in range(-3, 4, 2):
        x0 = cx - 28*S
        d.line([x0 + angle_offset*2*S, cy-8*S, x0-4*S + angle_offset*2*S, cy-8*S],
               fill=(*OUTLINE[:3], 120), width=max(1, S//2))

    return finish(img)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
ICONS = {
    "sleepy":   make_sleepy,
    "comfy":    make_comfy,
    "alert":    make_alert,
    "frazzled": make_frazzled,
    "panic":    make_panic,
}

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, fn in ICONS.items():
        path = os.path.join(OUT_DIR, f"{name}.png")
        fn().save(path)
        print(f"  ✓ {path}")
    print("Done.")
