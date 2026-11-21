#!/usr/bin/env python3
"""VELMARA — The Poster for a Place That Isn't There.

A travel poster for Velmara, the floating lantern isles: a sunset sky,
one great lantern-tower island floating above a sea of clouds, smaller
lantern isles beside it, and a warm ocean below.

Python 3.13, standard library only, no network, fully deterministic.
Writes /output/entry.png (1024x1024, PNG, <= 1 MiB).
"""

import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- canvas
px = bytearray(W * H * 3)


def _clip(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def hline(x0, x1, y, c):
    """Fill one horizontal run with colour c=(r,g,b)."""
    if y < 0 or y >= H:
        return
    x0 = _clip(x0, 0, W - 1)
    x1 = _clip(x1, 0, W - 1)
    if x1 < x0:
        return
    row = y * W * 3
    n = x1 - x0 + 1
    px[row + x0 * 3: row + (x1 + 1) * 3] = bytes(c) * n


def fill_rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        hline(x0, x1, y, c)


def circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        hline(cx - dx, cx + dx, cy + dy, c)


def ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * math.sqrt(max(0.0, t)))
        hline(cx - dx, cx + dx, cy + dy, c)


def triangle(x0, y0, x1, y1, x2, y2, c):
    """Filled triangle, scanline fill."""
    pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
    (ax, ay), (bx, by), (cx_, cy_) = pts
    for y in range(ay, cy_ + 1):
        xs = []
        for (px0, py0), (px1, py1) in (((ax, ay), (bx, by)),
                                       ((bx, by), (cx_, cy_)),
                                       ((ax, ay), (cx_, cy_))):
            if py0 == py1:
                continue
            if min(py0, py1) <= y < max(py0, py1) or (y == cy_ and y == max(py0, py1)):
                t = (y - py0) / float(py1 - py0)
                xs.append(px0 + t * (px1 - px0))
        if len(xs) >= 2:
            hline(int(min(xs)), int(max(xs)), y, c)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def line(x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        t = i / float(n)
        set_px(int(round(x0 + t * (x1 - x0))), int(round(y0 + t * (y1 - y0))), c)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def mix(a, b, t):
    return lerp(a, b, t)


# ---------------------------------------------------------------- palette
INDIGO = (43, 35, 80)
VIOLET = (107, 63, 110)
ROSE = (201, 111, 90)
GOLD = (242, 166, 94)
HONEY = (255, 217, 138)
CREAM = (255, 246, 221)
SUN_CORE = (255, 242, 201)
LANTERN = (255, 190, 92)
LANTERN_HOT = (255, 226, 150)
ISLE = (29, 58, 58)
ISLE_DARK = (20, 42, 46)
CLOUD = (255, 224, 196)
CLOUD_SHADOW = (232, 178, 158)
SEA_TOP = (46, 95, 107)
SEA_DEEP = (18, 48, 62)
SEA_LIGHT = (96, 158, 168)


def sky_color(y):
    """Sunset gradient from top of sky (y=0) to horizon (y=700)."""
    stops = [(0.0, INDIGO), (0.30, VIOLET), (0.55, ROSE),
             (0.78, GOLD), (1.0, HONEY)]
    t = _clip(y / 700.0, 0.0, 1.0)
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            return lerp(c0, c1, (t - t0) / (t1 - t0))
    return HONEY


def sea_color(y):
    t = _clip((y - 700) / 324.0, 0.0, 1.0)
    return lerp(SEA_TOP, SEA_DEEP, t)


# ---------------------------------------------------------------- font (5x7)
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(text, x, y, scale, color):
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    fill_rect(cx + col * scale, y + row * scale,
                              cx + (col + 1) * scale - 1,
                              y + (row + 1) * scale - 1, color)
        cx += 6 * scale


# ---------------------------------------------------------------- scene
def draw_sky():
    for y in range(0, 701):
        hline(0, W - 1, y, sky_color(y))


def draw_sun():
    cx, cy = 700, 400
    base = sky_color(cy)
    # glow rings, largest first, fine steps so the falloff reads smooth
    for r in range(300, 100, -8):
        t = (300 - r) / 200.0
        circle(cx, cy, r, mix(SUN_CORE, base, min(1.0, 0.35 + t * 0.65)))
    circle(cx, cy, 100, SUN_CORE)
    circle(cx, cy, 78, (255, 248, 220))


def draw_cloud(x, y, s, tint):
    x, y = int(x), int(y)
    ellipse(x, y, int(150 * s), int(34 * s), tint)
    ellipse(int(x - 95 * s), int(y + 8 * s), int(95 * s), int(26 * s), tint)
    ellipse(int(x + 95 * s), int(y + 8 * s), int(95 * s), int(26 * s), tint)
    ellipse(x, int(y - 14 * s), int(80 * s), int(24 * s), mix(tint, CREAM, 0.5))


def draw_stars():
    """A few faint stars in the deep indigo top of the sky."""
    for i in range(26):
        x = (i * 389 + 53) % 980 + 22
        y = (i * 173 + 41) % 220 + 40
        r = 1 + (i % 3 == 0)
        c = mix(CREAM, INDIGO, 0.25 + 0.2 * (i % 3))
        circle(x, y, r, c)


def draw_cloud_sea():
    # a rolling sea of clouds along the horizon
    for i, (x, y, s) in enumerate([(90, 648, 1.15), (330, 668, 1.35),
                                   (590, 652, 1.2), (830, 672, 1.4),
                                   (980, 650, 1.0), (210, 690, 1.0),
                                   (470, 692, 1.15), (730, 694, 1.0),
                                   (940, 692, 0.9)]):
        tint = CLOUD if i % 2 == 0 else CLOUD_SHADOW
        draw_cloud(x, y, s, tint)
    # low puffs straddling the horizon so the cloud sea melts into the ocean
    draw_cloud(150, 706, 0.9, CLOUD_SHADOW)
    draw_cloud(620, 708, 1.0, CLOUD)
    draw_cloud(880, 704, 0.8, CLOUD_SHADOW)


def draw_bird(x, y, s):
    line(x - 12 * s, y, x, y - 7 * s, ISLE_DARK)
    line(x, y - 7 * s, x + 12 * s, y, ISLE_DARK)


def draw_lantern(x, y, r):
    circle(x, y, r + 6, mix(LANTERN, sky_color(y), 0.55))
    circle(x, y, r + 2, LANTERN)
    circle(x, y, r, LANTERN_HOT)
    fill_rect(x - 1, y - r - 4, x + 1, y - r, ISLE_DARK)


def draw_island(cx, top_y, rx, ry, drop, houses=True):
    """Floating isle: domed top, tapering rock underside, lanterns."""
    ellipse(cx, top_y, rx, ry, ISLE)
    triangle(cx - rx + 18, top_y + ry // 2, cx + rx - 18, top_y + ry // 2,
             cx, top_y + drop, ISLE_DARK)
    # grassy rim highlight
    ellipse(cx, top_y - ry + 6, rx, 10, (52, 96, 84))
    if houses:
        # tiny houses with lit windows
        for hx, hw, hh in [(cx - rx // 2, 34, 26), (cx + rx // 3, 28, 22)]:
            fill_rect(hx, top_y - ry - hh + 8, hx + hw, top_y - ry + 8, ISLE_DARK)
            triangle(hx - 3, top_y - ry - hh + 8, hx + hw + 3, top_y - ry - hh + 8,
                     hx + hw // 2, top_y - ry - hh - 8, (24, 52, 52))
            fill_rect(hx + 8, top_y - ry - hh + 16, hx + 14, top_y - ry - hh + 22,
                      LANTERN_HOT)


def draw_tower(cx, base_y):
    """The great lantern tower — Velmara's landmark."""
    # stepped tower body
    fill_rect(cx - 26, base_y - 150, cx + 26, base_y, (24, 52, 52))
    fill_rect(cx - 34, base_y - 150, cx + 34, base_y - 138, ISLE_DARK)
    fill_rect(cx - 18, base_y - 196, cx + 18, base_y - 150, (24, 52, 52))
    # glowing windows up the tower
    for wy in range(base_y - 132, base_y - 10, 30):
        fill_rect(cx - 6, wy, cx + 6, wy + 12, LANTERN_HOT)
    # beacon room + dome
    fill_rect(cx - 30, base_y - 232, cx + 30, base_y - 196, ISLE_DARK)
    fill_rect(cx - 22, base_y - 226, cx + 22, base_y - 202, LANTERN_HOT)
    triangle(cx - 34, base_y - 232, cx + 34, base_y - 232, cx, base_y - 258,
             ISLE_DARK)
    # beacon glow + flame
    circle(cx, base_y - 214, 52, mix(LANTERN, sky_color(base_y - 214), 0.6))
    circle(cx, base_y - 214, 30, LANTERN)
    circle(cx, base_y - 214, 18, LANTERN_HOT)


def draw_lantern_string(x0, y0, x1, y1, n=7):
    """A sagging string of small lanterns between two points."""
    for i in range(n + 1):
        t = i / float(n)
        x = int(x0 + (x1 - x0) * t)
        sag = int(26 * 4 * t * (1 - t))
        y = int(y0 + (y1 - y0) * t) + sag
        if i:
            px0 = int(x0 + (x1 - x0) * (i - 1) / n)
            py0 = int(y0 + (y1 - y0) * (i - 1) / n) + int(26 * 4 * (i - 1) / n * (1 - (i - 1) / n))
            line(px0, py0, x, y, ISLE_DARK)
        draw_lantern(x, y + 8, 5)


def draw_sea():
    for y in range(700, H):
        hline(0, W - 1, y, sea_color(y))
    # sun reflection: warm dashes under the sun, fading with depth
    for y in range(716, 1000, 7):
        depth = (y - 716) / 284.0
        half = int(150 * (1 - depth * 0.75) + 14)
        wob = ((y * 2654435761) % 41) - 20
        c = mix(LANTERN, SEA_TOP, depth * 0.55)
        hline(700 - half + wob // 3, 700 + half + wob // 3, y, c)
    # faint broken shimmer strokes on the water
    for i, y in enumerate((760, 830, 900, 960)):
        seg = 120 + ((i * 211) % 260)
        x0 = 60 + ((i * 337) % 500)
        hline(x0, x0 + seg, y, SEA_LIGHT)
        hline(1024 - x0 - seg, 1024 - x0, y + 3, SEA_LIGHT)


def draw_frame():
    fill_rect(26, 26, W - 27, 30, HONEY)
    fill_rect(26, H - 31, W - 27, H - 27, HONEY)
    fill_rect(26, 26, 30, H - 27, HONEY)
    fill_rect(W - 31, 26, W - 27, H - 27, HONEY)


def draw_poster():
    draw_sky()
    draw_stars()
    draw_sun()
    # high wisps, kept faint so they read as dusk haze, not shapes
    draw_cloud(210, 268, 0.55, mix(CLOUD, sky_color(268), 0.72))
    draw_cloud(880, 240, 0.45, mix(CLOUD, sky_color(240), 0.72))
    # birds
    for bx, by, bs in [(300, 300, 1), (350, 330, 1), (330, 285, 1),
                       (830, 300, 1), (880, 330, 1)]:
        draw_bird(bx, by, bs)
    # side isles first, central isle last (in front)
    draw_island(205, 505, 108, 34, 128)
    draw_island(838, 528, 128, 38, 142)
    # lantern strings between the isles
    draw_lantern_string(300, 470, 420, 452)
    draw_lantern_string(610, 452, 730, 478)
    # central isle with the tower
    draw_island(512, 540, 205, 52, 190, houses=False)
    draw_tower(512, 540 - 52 + 14)
    # beacon lantern on the central isle's edge
    draw_lantern(330, 512, 7)
    draw_lantern(700, 520, 7)
    draw_sea()
    draw_cloud_sea()
    # title
    name = "VELMARA"
    scale = 16
    nx = (W - text_width(name, scale)) // 2
    ny = 66
    draw_text(name, nx + 5, ny + 5, scale, (30, 24, 58))
    draw_text(name, nx, ny, scale, CREAM)
    sub = "THE LANTERN ISLES"
    sscale = 5
    sx = (W - text_width(sub, sscale)) // 2
    sy = 196
    line(sx - 70, sy + 17, sx - 16, sy + 17, HONEY)
    line(sx + text_width(sub, sscale) + 16, sy + 17,
         sx + text_width(sub, sscale) + 70, sy + 17, HONEY)
    draw_text(sub, sx + 2, sy + 2, sscale, (30, 24, 58))
    draw_text(sub, sx, sy, sscale, (255, 233, 184))
    draw_frame()


# ---------------------------------------------------------------- PNG out
def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = os.environ.get("POSTER_OUT", "/output/entry.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    draw_poster()
    n = write_png(out)
    print(f"wrote {out} ({n} bytes)")


if __name__ == "__main__":
    main()
