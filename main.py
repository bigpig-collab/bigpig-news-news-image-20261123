#!/usr/bin/env python3
"""The World in One Day -- Monday 23 November 2026, THE DAY IN FULL.

HERO-LEAD front page: one dominant hero (Nvidia reinstates Jensen
Huang, +31.5%, Wall Street's best day since April 2025), two
secondary leads, eight scene cards, nineteen briefs -- 30 stories,
seven regions with news, dotted world map, UTC strip, DATE CHECK.

Pure Python 3.13 standard library only: no Pillow, no network.
A fresh vector stroke font is drawn in this file: a high-contrast
serif for display (thick stems, thin horizontals, serif bars, true
arcs) and a clean uniform sans for body text. Every scene is drawn
from primitives (rects, quads, discs, polygons) in this file.
Deterministic: two runs produce byte-identical PNGs.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- PNG out
def write_png(path, w, h, px):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        c = struct.pack(">I", len(payload)) + kind + payload
        c += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = c

    def rect(self, x, y, w, h, c):
        x, y, w, h = int(x), int(y), int(w), int(h)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = row

    def disc(self, cx, cy, r, c):
        cx, cy, r = int(cx), int(cy), int(r)
        if r <= 0:
            self.put(cx, cy, c)
            return
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, c)

    def poly(self, pts, c):
        pts = [(float(x), float(y)) for x, y in pts]
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.h - 1, int(math.ceil(max(ys))))
        n = len(pts)
        for yy in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    if y1 != y0:
                        xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa, xb = int(math.ceil(xs[k])), int(math.floor(xs[k + 1]))
                if xb >= xa:
                    self.rect(xa, yy, xb - xa + 1, 1, c)

    def quad(self, x0, y0, x1, y1, w, c):
        """A thick line segment as a filled quad, no end discs."""
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        if ln < 0.001:
            return
        nx, ny = -dy / ln * w / 2.0, dx / ln * w / 2.0
        self.poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                   (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], c)

    def thick(self, x0, y0, x1, y1, w, c):
        """A thick line segment as a filled quad with round joints."""
        self.quad(x0, y0, x1, y1, w, c)
        r = max(1, int(round(w / 2)))
        self.disc(x0, y0, r, c)
        self.disc(x1, y1, r, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        self.thick(x0, y0, x1, y1, w, c)

# ---------------------------------------------------------------- stroke font
# Glyphs on a 6-wide (x 0..6) by 8-tall (y 0..8) grid. Each glyph is a
# list of strokes; a stroke is "W:x,y x,y ..." where W is the width
# class: S = stem, H = horizontal, D = diagonal / curve. Serif and
# sans share the skeletons; serif renders S thick / H thin and adds
# serif bars, sans renders every stroke at one even width.
def _arc(cx, cy, rx, ry, a0, a1, n=12):
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append("%.2f,%.2f" % (cx + rx * math.cos(a),
                                  cy + ry * math.sin(a)))
    return " ".join(pts)

FONT = {
    "A": ["S:0,8 3,0 6,8", "H:1.7,5.4 4.3,5.4"],
    "B": ["S:0,0 0,8",
          "D:0,0 3.4,0 5,1.2 5,2.8 3.4,4 0,4",
          "D:0,4 3.8,4 5.4,5.2 5.4,6.8 3.8,8 0,8"],
    "C": ["D:" + _arc(3, 4, 3, 4, 50, 310)],
    "D": ["S:0,0 0,8", "D:0,0 3.2,0 5.4,2 5.4,6 3.2,8 0,8"],
    "E": ["S:0,0 0,8", "H:0,0 5.2,0", "H:0,4 4,4", "H:0,8 5.2,8"],
    "F": ["S:0,0 0,8", "H:0,0 5.2,0", "H:0,4 4,4"],
    "G": ["D:" + _arc(3, 4, 3, 4, 45, 315),
          "H:3.2,4.6 5.6,4.6", "S:5.6,4.6 5.6,7.6"],
    "H": ["S:0,0 0,8", "S:6,0 6,8", "H:0,4 6,4"],
    "I": ["H:1,0 5,0", "S:3,0 3,8", "H:1,8 5,8"],
    "J": ["H:2,0 5.6,0", "S:4.4,0 4.4,6.2",
          "D:4.4,6.2 3,8 0.8,7 0.4,5.4"],
    "K": ["S:0,0 0,8", "D:4.8,0 1.2,4.2", "D:1.8,3.6 5.4,8"],
    "L": ["S:0,0 0,8", "H:0,8 5.4,8"],
    "M": ["S:0,0 0,8", "S:6,0 6,8", "D:0,0 3,4.4 6,0"],
    "N": ["S:0,0 0,8", "S:6,0 6,8", "D:0,0 6,8"],
    "O": ["D:" + _arc(3, 4, 3, 4, 0, 360)],
    "P": ["S:0,0 0,8", "D:0,0 3.4,0 5.2,1.4 5.2,2.8 3.4,4.2 0,4.2"],
    "Q": ["D:" + _arc(3, 4, 3, 4, 0, 360), "D:3.8,5.6 5.8,8"],
    "R": ["S:0,0 0,8", "D:0,0 3.4,0 5.2,1.4 5.2,2.8 3.4,4.2 0,4.2",
          "D:2.6,4.2 5.8,8"],
    "S": ["D:5.2,1.4 3.4,0 1.2,0.8 0.6,2.2 1.6,3.6 4.4,4.4 5.4,5.6 "
          "4.6,7.2 2.6,8 0.8,7.2"],
    "T": ["H:0,0 6,0", "S:3,0 3,8"],
    "U": ["S:0,0 0,6", "S:6,0 6,6", "D:" + _arc(3, 6, 3, 2, 0, 180)],
    "V": ["D:0,0 3,8 6,0"],
    "W": ["D:0,0 1.5,8 3,4 4.5,8 6,0"],
    "X": ["D:0,0 6,8", "D:6,0 0,8"],
    "Y": ["D:0,0 3,3.6 6,0", "S:3,3.6 3,8"],
    "Z": ["H:0,0 6,0", "D:6,0 0,8", "H:0,8 6,8"],
    "0": ["D:" + _arc(3, 4, 3, 4, 0, 360)],
    "1": ["D:1.6,1.8 3.2,0.2 3.2,8", "H:1.2,8 5.2,8"],
    "2": ["D:0.6,2 1.6,0.4 4.4,0.4 5.4,1.8 5.4,3.2 2.4,5.4 0.6,8 5.6,8"],
    "3": ["D:0.8,0.4 4,0 5.4,1.4 5.4,3 3.6,4 5.4,5 5.4,6.6 4,8 0.8,7.6"],
    "4": ["D:4.4,0 0.8,5.8 5.4,5.8", "S:4.2,0 4.2,8"],
    "5": ["D:5.2,0 0.8,0 0.8,3.6 3.6,3.6 5.2,4.8 5.2,6.4 3.6,8 1.2,7.6"],
    "6": ["D:5,1 3.6,0 1.4,1.6 0.8,4 0.8,6.2 2,8 4.4,7.6 5.2,5.6 "
          "4.4,3.8 2,3.8"],
    "7": ["H:0.6,0 5.6,0", "D:5.6,0 2.6,8"],
    "8": ["D:" + _arc(3, 2, 2.2, 2, 0, 360),
          "D:" + _arc(3, 6, 2.4, 2, 0, 360)],
    "9": ["D:1,7 2.4,8 4.6,6.4 5.2,4 5.2,1.8 4,0 1.6,0.4 0.8,2.4 "
          "1.6,4.2 4,4.2"],
    ".": ["D:2.4,7 3.6,7 3.6,8 2.4,8"],
    ",": ["D:2.4,7 3.6,7 3.6,8 2.4,8", "D:3.2,8 2.2,9"],
    ":": ["D:2.4,2.2 3.6,2.2 3.6,3.4 2.4,3.4",
          "D:2.4,5.8 3.6,5.8 3.6,7 2.4,7"],
    ";": ["D:2.4,2.2 3.6,2.2 3.6,3.4 2.4,3.4",
          "D:2.4,5.8 3.6,5.8 3.6,7 2.4,7", "D:3.2,7 2.2,9"],
    "!": ["S:3,0 3,5.4", "D:2.4,7 3.6,7 3.6,8 2.4,8"],
    "?": ["D:1.4,2 1.6,0.6 4,0 5.4,1.2 5.2,2.8 4,3.8 3,4.4",
          "S:3,4.4 3,5.6", "D:2.4,7 3.6,7 3.6,8 2.4,8"],
    "'": ["D:3.4,0 2.6,2"],
    '"': ["D:2,0 1.4,1.8", "D:4.4,0 3.8,1.8"],
    "-": ["H:0.8,4 5.2,4"],
    "—": ["H:0,4 6,4"],
    "/": ["D:5,0 1,8"],
    "(": ["D:" + _arc(4.5, 4, 2.2, 4, 100, 260)],
    ")": ["D:" + _arc(1.5, 4, 2.2, 4, -80, 80)],
    "+": ["H:0.8,4 5.2,4", "S:3,1 3,7"],
    "=": ["H:0.8,2.6 5.2,2.6", "H:0.8,5.4 5.2,5.4"],
    "%": ["D:" + _arc(1.6, 2, 1.3, 1.6, 0, 360),
          "D:5.2,0 0.8,8",
          "D:" + _arc(4.4, 6, 1.3, 1.6, 0, 360)],
    "$": ["D:5.2,1.4 3.4,0 1.2,0.8 0.6,2.2 1.6,3.6 4.4,4.4 5.4,5.6 "
          "4.6,7.2 2.6,8 0.8,7.2", "S:3,-0.4 3,8.4"],
    "·": ["D:2.4,3.4 3.6,3.4 3.6,4.4 2.4,4.4"],
    " ": [],
}

# Serif bars: (x, y, dir) -- a horizontal bar centred on x at a stem
# end; dir +1 hangs below y, -1 hangs above y.
SERIFS = {
    "A": [(0, 8, -1), (6, 8, -1)],
    "B": [(0, 0, 1), (0, 8, -1)],
    "D": [(0, 0, 1), (0, 8, -1)],
    "E": [(0, 0, 1), (0, 8, -1)],
    "F": [(0, 0, 1), (0, 8, -1)],
    "H": [(0, 0, 1), (0, 8, -1), (6, 0, 1), (6, 8, -1)],
    "K": [(0, 0, 1), (0, 8, -1)],
    "L": [(0, 0, 1), (0, 8, -1)],
    "M": [(0, 0, 1), (0, 8, -1), (6, 0, 1), (6, 8, -1)],
    "N": [(0, 0, 1), (0, 8, -1), (6, 0, 1), (6, 8, -1)],
    "P": [(0, 0, 1), (0, 8, -1)],
    "R": [(0, 0, 1), (0, 8, -1)],
    "T": [(0, 0, 1), (6, 0, 1), (3, 8, -1)],
    "U": [(0, 0, 1), (6, 0, 1)],
    "Y": [(3, 8, -1)],
    "4": [(4.2, 8, -1)],
}

ADV = 7.0  # advance per glyph, in grid units

def _widths(font):
    if font == "serif":
        return {"S": 1.5, "H": 0.8, "D": 1.15}
    return {"S": 1.05, "H": 1.05, "D": 1.05}

def text_w(s, sc):
    return int(len(s) * ADV * sc)

def draw_text(cv, x, y, s, font, c, txt):
    """Draw txt (uppercased) with cap top at y; s = px per grid unit."""
    txt = txt.upper()
    ws = _widths(font)
    cx = float(x)
    for ch in txt:
        strokes = FONT.get(ch)
        if strokes is None:
            strokes = FONT.get("?", [])
        for stroke in strokes:
            wc, body = stroke.split(":", 1)
            w = ws[wc] * s
            pts = []
            for tok in body.split():
                px, py = tok.split(",")
                pts.append((cx + float(px) * s, y + float(py) * s))
            for i in range(len(pts) - 1):
                cv.quad(pts[i][0], pts[i][1], pts[i + 1][0],
                        pts[i + 1][1], max(1.0, w), c)
            if len(pts) > 1:
                r = max(1, int(round(max(1.0, w) / 2)))
                cv.disc(pts[0][0], pts[0][1], r, c)
                cv.disc(pts[-1][0], pts[-1][1], r, c)
        if font == "serif":
            for (sx, sy, d) in SERIFS.get(ch, []):
                bx = cx + sx * s
                by = y + sy * s
                bw = 2.2 * s
                bh = 0.75 * s
                if d > 0:
                    cv.rect(bx - bw / 2, by, bw, bh, c)
                else:
                    cv.rect(bx - bw / 2, by - bh, bw, bh, c)
        cx += ADV * s
    return cx

def wrap(txt, sc, max_w):
    """Greedy word wrap; returns lines fitting max_w pixels."""
    max_chars = max(1, int(max_w // (ADV * sc)))
    words = txt.split()
    lines, cur = [], ""
    for wd in words:
        if not cur:
            cur = wd
        elif len(cur) + 1 + len(wd) <= max_chars:
            cur += " " + wd
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

def draw_lines(cv, x, y, sc, font, c, lines, lh=None):
    if lh is None:
        lh = int(10 * sc) + 2
    for ln in lines:
        draw_text(cv, x, y, sc, font, c, ln)
        y += lh
    return y

# ---------------------------------------------------------------- palette
PAPER = (247, 241, 222)
CREAM = (255, 250, 235)
INK = (26, 26, 26)
NAVY = (20, 38, 77)
NAVY2 = (38, 62, 110)
RED = (179, 39, 30)
TEAL = (14, 107, 107)
GOLD = (197, 141, 28)
GREY = (110, 105, 92)
LIGHT = (232, 224, 200)
GREEN = (31, 122, 63)
ORANGE = (214, 110, 24)
PURPLE = (120, 66, 150)
WHITE = (255, 255, 255)

REGION_COLORS = {
    "EUROPE": NAVY2,
    "MIDDLE EAST": RED,
    "ASIA-PACIFIC": TEAL,
    "AMERICAS": GREEN,
    "AFRICA": GOLD,
    "OCEANIA": PURPLE,
    "WORLD": GREY,
}

# ---------------------------------------------------------------- scenes
def scene_hero(cv, x, y, w, h):
    cv.rect(x, y, w, h, NAVY)
    for gx in range(x + 12, x + w, 26):
        for gy in range(y + 10, y + h, 26):
            cv.disc(gx, gy, 1, NAVY2)
    # rising chart arrow
    cv.thick(x + 215, y + h - 48, x + w - 40, y + 42, 7, GOLD)
    cv.poly([(x + w - 40, y + 42), (x + w - 78, y + 46),
             (x + w - 58, y + 78)], GOLD)
    # rising bars
    bars = [34, 52, 44, 74, 62, 96]
    bx = x + 210
    for bh in bars:
        cv.rect(bx, y + h - 30 - bh, 30, bh, GREEN)
        bx += 36
    cv.rect(bx, y + h - 30 - 118, 30, 118, GOLD)
    # the chip
    cx, cy = x + 34, y + h // 2 - 52
    cv.rect(cx - 8, cy - 8, 166, 116, (12, 24, 52))
    cv.rect(cx, cy, 150, 100, GREEN)
    for px in range(cx + 18, cx + 140, 24):
        cv.rect(px, cy - 8, 8, 8, (180, 190, 200))
        cv.rect(px, cy + 100, 8, 8, (180, 190, 200))
    for py in range(cy + 18, cy + 90, 24):
        cv.rect(cx - 8, py, 8, 8, (180, 190, 200))
        cv.rect(cx + 150, py, 8, 8, (180, 190, 200))
    cv.rect(cx + 42, cy + 30, 66, 40, (21, 92, 47))
    draw_text(cv, cx + 43, cy + 36, 2.3, "sans", WHITE, "NVDA")
    draw_text(cv, cx + 18, cy + 82, 1.2, "sans", WHITE, "AI INSIDE")

def scene_crowdstrike(cv, x, y, w, h):
    cv.rect(x, y, w, h, (222, 232, 228))
    def shield(sx, col, label):
        pts = [(sx + 8, y + 18), (sx + 72, y + 18), (sx + 72, y + 62),
               (sx + 40, y + 104), (sx + 8, y + 62)]
        cv.poly(pts, col)
        draw_text(cv, sx + 16, y + 46, 2.0, "sans", WHITE, label)
    shield(x + 6, RED, "CRWD")
    shield(x + 66, NAVY2, "ZS")
    draw_text(cv, x + 58, y + 8, 2.2, "serif", INK, "+")

def scene_merkury(cv, x, y, w, h):
    cv.rect(x, y, w, h, (186, 210, 224))
    cv.rect(x, y + int(h * 0.62), w, h - int(h * 0.62), NAVY2)
    # sinking hull, bow up
    cv.poly([(x + 30, y + 78), (x + 118, y + 52), (x + 128, y + 66),
             (x + 52, y + 96)], (90, 96, 100))
    cv.rect(x + 96, y + 34, 8, 22, (90, 96, 100))
    # explosion + smoke
    cv.disc(x + 108, y + 30, 12, ORANGE)
    cv.disc(x + 122, y + 22, 8, GOLD)
    cv.disc(x + 92, y + 16, 7, (150, 150, 150))
    cv.disc(x + 118, y + 8, 6, (170, 170, 170))
    # seven drone boats
    for i in range(7):
        dx = x + 8 + i * 18
        dy = y + h - 22 - (i % 2) * 6
        cv.rect(dx, dy, 10, 4, WHITE)
        cv.line(dx - 8, dy + 2, dx, dy + 2, WHITE, 1)

def scene_modi(cv, x, y, w, h):
    cv.rect(x, y, w, h, (250, 232, 190))
    # dome, centre bottom
    cv.rect(x + int(0.44 * w), y + int(0.60 * h), int(0.12 * w),
            int(0.40 * h), (214, 196, 150))
    cv.disc(x + int(0.50 * w), y + int(0.60 * h), int(0.05 * w),
            (214, 196, 150))
    # India flag, left
    cv.rect(x + int(0.04 * w), y + int(0.10 * h), 3, int(0.80 * h), INK)
    fx = x + int(0.06 * w)
    fw, fh = int(0.24 * w), int(0.11 * h)
    cv.rect(fx, y + int(0.10 * h), fw, fh, (255, 153, 51))
    cv.rect(fx, y + int(0.21 * h), fw, fh, WHITE)
    cv.rect(fx, y + int(0.32 * h), fw, fh, GREEN)
    cv.disc(fx + fw // 2, y + int(0.265 * h), 3, NAVY2)
    # Nepal flag (double pennon), right
    cv.rect(x + int(0.90 * w), y + int(0.10 * h), 3, int(0.80 * h), INK)
    nx = x + int(0.92 * w)
    cv.poly([(nx, y + int(0.10 * h)), (nx + int(0.10 * w),
             y + int(0.24 * h)), (nx, y + int(0.24 * h))],
            (220, 20, 60))
    cv.poly([(nx, y + int(0.28 * h)), (nx + int(0.07 * w),
             y + int(0.40 * h)), (nx, y + int(0.40 * h))],
            (220, 20, 60))

def scene_cricket(cv, x, y, w, h):
    cv.rect(x, y, w, h, (31, 122, 63))
    cv.rect(x + int(0.25 * w), y + int(0.08 * h), int(0.50 * w),
            int(0.72 * h), (214, 196, 150))
    for dx in (0, 1, 2):
        cv.rect(x + int(0.66 * w) + dx * 7, y + int(0.14 * h), 4,
                int(0.34 * h), (240, 200, 90))
    cv.thick(x + int(0.30 * w), y + int(0.72 * h),
             x + int(0.48 * w), y + int(0.20 * h), 7, (160, 110, 60))
    cv.disc(x + int(0.86 * w), y + int(0.16 * h), 6, RED)

def scene_pmi(cv, x, y, w, h):
    cv.rect(x, y, w, h, CREAM)
    vals = [("US", 54.5), ("EZ", 51.7), ("DE", 55.0), ("FR", 46.2),
            ("UK", 52.3)]
    base = y + int(0.62 * h)
    for lx in range(x + 6, x + w - 6, 9):
        cv.rect(lx, base, 4, 2, RED)
    bx = x + int(0.06 * w)
    for lab, v in vals:
        bh = int((v - 40) / 16.0 * 0.52 * h)
        col = GREEN if v >= 50 else RED
        cv.rect(bx, base - bh, int(0.13 * w), bh, col)
        draw_text(cv, bx, y + int(0.76 * h), 0.95, "sans", INK, lab)
        bx += int(0.185 * w)

def scene_williams(cv, x, y, w, h):
    cv.rect(x, y, w, h, NAVY2)
    cv.poly([(x + int(0.06 * w), y + int(0.30 * h)),
             (x + int(0.50 * w), y + int(0.30 * h)),
             (x + int(0.28 * w), y + int(0.08 * h))], LIGHT)
    for i in range(4):
        cv.rect(x + int(0.08 * w) + i * int(0.115 * w),
                y + int(0.34 * h), int(0.06 * w), int(0.52 * h), WHITE)
    cv.rect(x + int(0.04 * w), y + int(0.86 * h), int(0.48 * w),
            int(0.08 * h), LIGHT)
    draw_text(cv, x + int(0.62 * w), y + int(0.30 * h), 2.0, "serif",
              WHITE, "%")
    draw_text(cv, x + int(0.62 * w), y + int(0.78 * h), 1.2, "sans",
              GOLD, "FED")

def scene_iran(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT)
    # derrick: A-frame with crossbars
    cv.thick(x + int(0.20 * w), y + int(0.88 * h),
             x + int(0.29 * w), y + int(0.10 * h), 3, INK)
    cv.thick(x + int(0.38 * w), y + int(0.88 * h),
             x + int(0.29 * w), y + int(0.10 * h), 3, INK)
    cv.line(x + int(0.235 * w), y + int(0.50 * h),
            x + int(0.345 * w), y + int(0.50 * h), INK, 2)
    cv.line(x + int(0.22 * w), y + int(0.72 * h),
            x + int(0.36 * w), y + int(0.72 * h), INK, 2)
    sx, sy = x + int(0.76 * w), y + int(0.30 * h)
    cv.disc(sx, sy, 13, RED)
    cv.disc(sx, sy, 9, LIGHT)
    cv.thick(sx - 9, sy - 9, sx + 9, sy + 9, 4, RED)
    draw_text(cv, x + int(0.56 * w), y + int(0.80 * h), 1.1, "sans",
              RED, "SANCTIONED")

def scene_fifa(cv, x, y, w, h):
    cv.rect(x, y, w, h, (178, 222, 178))
    bx, by = x + int(0.24 * w), y + int(0.50 * h)
    cv.disc(bx, by, int(0.36 * h), WHITE)
    cv.poly([(bx, by - 9), (bx + 8, by - 3), (bx + 5, by + 7),
             (bx - 5, by + 7), (bx - 8, by - 3)], INK)
    cv.disc(bx - 13, by - 11, 3, INK)
    cv.disc(bx + 13, by - 10, 3, INK)
    cv.disc(bx + 13, by + 11, 3, INK)
    cv.disc(bx - 13, by + 12, 3, INK)
    tx = x + int(0.66 * w)
    cv.poly([(tx, y + int(0.16 * h)), (tx + int(0.16 * w),
             y + int(0.16 * h)), (tx + int(0.13 * w), y + int(0.52 * h)),
             (tx + int(0.03 * w), y + int(0.52 * h))], GOLD)
    cv.rect(tx + int(0.06 * w), y + int(0.52 * h), int(0.04 * w),
            int(0.22 * h), GOLD)
    cv.rect(tx - int(0.02 * w), y + int(0.74 * h), int(0.20 * w),
            int(0.10 * h), GOLD)

def scene_earnings(cv, x, y, w, h):
    cv.rect(x, y, w, h, CREAM)
    candles = [(0.08, 0.55, 0.30, GREEN), (0.30, 0.35, 0.45, GREEN),
               (0.52, 0.25, 0.50, RED), (0.74, 0.45, 0.25, GREEN)]
    for fx, top, ht, col in candles:
        cx = x + int(fx * w)
        cv.rect(cx + 6, y + int(top * h), 3, int(ht * h), INK)
        cv.rect(cx, y + int((top + 0.06) * h), 15,
                int((ht - 0.12) * h), col)
    cv.thick(x + int(0.06 * w), y + int(0.85 * h),
             x + int(0.92 * w), y + int(0.15 * h), 3, GOLD)
    cv.poly([(x + int(0.92 * w), y + int(0.15 * h)),
             (x + int(0.80 * w), y + int(0.16 * h)),
             (x + int(0.87 * w), y + int(0.30 * h))], GOLD)

def scene_ariane(cv, x, y, w, h):
    cv.rect(x, y, w, h, (186, 200, 214))
    cv.rect(x + int(0.20 * w), y + int(0.82 * h), int(0.60 * w),
            int(0.10 * h), (120, 120, 120))
    rx = x + int(0.46 * w)
    cv.rect(rx, y + int(0.26 * h), int(0.08 * w), int(0.56 * h), WHITE)
    cv.poly([(rx, y + int(0.26 * h)),
             (rx + int(0.08 * w), y + int(0.26 * h)),
             (rx + int(0.04 * w), y + int(0.06 * h))], RED)
    cv.poly([(rx, y + int(0.82 * h)),
             (rx - int(0.04 * w), y + int(0.94 * h)),
             (rx, y + int(0.94 * h))], RED)
    cv.poly([(rx + int(0.08 * w), y + int(0.82 * h)),
             (rx + int(0.12 * w), y + int(0.94 * h)),
             (rx + int(0.08 * w), y + int(0.94 * h))], RED)
    cv.thick(x + int(0.08 * w), y + int(0.06 * h),
             x + int(0.92 * w), y + int(0.94 * h), 4, RED)
    cv.thick(x + int(0.92 * w), y + int(0.06 * h),
             x + int(0.08 * w), y + int(0.94 * h), 4, RED)
    cv.rect(x + int(0.68 * w), y + int(0.04 * h), int(0.28 * w),
            int(0.22 * h), RED)
    draw_text(cv, x + int(0.72 * w), y + int(0.08 * h), 1.3, "sans",
              WHITE, "HOLD")

# ---------------------------------------------------------------- dotted map
MAP_ROWS = [
    "...#########...###..............#############...",
    ".#############...........#####.################.",
    "..###########............####...##############..",
    "...#########..............###...#############...",
    "....######...............######..##########.....",
    ".....####................#######..#######......",
    ".........................#######...####........",
    "...........####...........####....#####.........",
    "...........#####...........###..................",
    "............####............##.........######...",
    "............##.........................#######..",
    "............#..................................#",
]
# (col, row) pins in MAP_ROWS coords -> story number
PINS = [(4, 3, "1"), (7, 4, "2"), (29, 5, "3"), (36, 4, "4"),
        (46, 11, "5"), (11, 2, "6"), (35, 4, "8"), (27, 2, "9"),
        (13, 7, "11")]

def draw_map(cv, x, y, w, h):
    cw = w / 48.0
    ch = h / float(len(MAP_ROWS))
    for r, row in enumerate(MAP_ROWS):
        for c in range(min(48, len(row))):
            if row[c] == "#":
                cv.disc(int(x + c * cw + cw / 2), int(y + r * ch + ch / 2),
                        1, NAVY2)
    for (c, r, num) in PINS:
        px = int(x + c * cw + cw / 2)
        py = int(y + r * ch + ch / 2)
        cv.disc(px, py, 7, RED)
        cv.disc(px, py, 7, RED)
        tw = text_w(num, 0.85)
        draw_text(cv, px - tw // 2, py - 3, 0.85, "sans", WHITE, num)

# ---------------------------------------------------------------- content
FIGURES = [
    ("+31.5%", "NVDA IN A DAY", GREEN, 3.0),
    ("$950BN", "VALUE ADDED", NAVY2, 3.0),
    ("+6.5%", "NASDAQ BEST DAY", NAVY2, 3.0),
    ("$43.9BN", "ZSCALER DEAL", INK, 3.0),
    ("24,000 CR", "NEPAL PACKAGE", TEAL, 2.1),
    ("7", "DRONES SANK SHIP", RED, 3.0),
]

REGIONS = [
    ("EUROPE", 5, NAVY2, 150, 1.35),
    ("MID EAST", 3, RED, 96, 1.2),
    ("ASIA-PAC", 3, TEAL, 96, 1.2),
    ("AMERICAS", 8, GREEN, 250, 1.35),
    ("AFRICA", 2, GOLD, 72, 1.15),
    ("OCEANIA", 8, PURPLE, 250, 1.35),
    ("WORLD", 1, GREY, 82, 1.35),
]

HERO_BODY = ("STOCK CLOSES $165.05, UP 31.5% - ITS BIGGEST ONE-DAY GAIN "
             "SINCE 2003. ABOUT $950BN RETURNS IN A SESSION. "
             "NASDAQ +6.5%, S&P +4.7%.")

SECONDARY = [
    ("2", "AMERICAS", "DEALS", scene_crowdstrike,
     "CROWDSTRIKE BUYS ZSCALER",
     "ALL-STOCK, $43.9BN, A 34% PREMIUM - ONE OF THE LARGEST CYBER "
     "DEALS ON RECORD. CLOSES H2 FY2028. (AP)"),
    ("3", "AFRICA", "WAR AT SEA", scene_merkury,
     "UKRAINE SINKS RUSSIAN WARSHIP",
     "ZELENSKY CONFIRMS: 7 DRONES SANK THE CORVETTE MERKURY OFF "
     "LIBYA; A KA-27 ABOARD DESTROYED. (AP)"),
]

CARDS = [
    ("4", "ASIA-PACIFIC", scene_modi, "SHAH-MODI: 24,000 CR",
     "INDIA PLEDGES 24,000 CRORE RUPEES TO NEPAL."),
    ("5", "OCEANIA", scene_cricket, "WELLINGTON: DRAW",
     "NZ 239/5 HOLD INDIA 720/9 DEC FOR THE DRAW."),
    ("6", "AMERICAS", scene_pmi, "US PMIS MISS",
     "SERVICES 54.7 MISS; COMPOSITE 54.6, 4-MO LOW."),
    ("7", "AMERICAS", scene_williams, "WILLIAMS: MORE HIKES",
     "MORE HIKES NEEDED, HE SAYS; A DEC HIKE IS ~97% PRICED."),
    ("8", "MIDDLE EAST", scene_iran, "IRAN: LAST LIFELINE",
     "TREASURY HITS 2 DOZEN EXCHANGE HOUSES AND FRONTS."),
    ("9", "WORLD", scene_fifa, "FIFA: USA 2031 UK 2035",
     "USA-LED BID TAKES 2031; THE UK TAKES 2035."),
    ("10", "AMERICAS", scene_earnings, "HPE BEATS, ZOOM FALLS",
     "HPE BEATS, RAISES GUIDANCE; ZOOM FALLS; SEMTECH -8%."),
    ("11", "EUROPE", scene_ariane, "ARIANE SCRUBBED",
     "GROUND FAULT HALTS COUNT; 36 LEO SATELLITES SAFE."),
]

BRIEFS_A = [
    "12 DHAKA: WAGE BOARD MEETS; TK30,000 DEMANDED",
    "13 ZELENSKY: FOUR-WAY TALKS \"TOMORROW\"",
    "14 KREMLIN: BALTIC WARNING AFTER DRONE FIRE",
    "15 DYMER: TOLL RISES TO 11",
    "16 HOUTHIS: SAUDI REFINERY HIT; 10 DEAD",
    "17 SUDAN: FIVE CHILDREN KILLED IN DRONES",
    "18 ISRAEL: COALITION TALKS RESUME",
    "19 AUSTRALIA: SOLOMONS TREATY NEAR",
    "20 ALBANESE: COP31 \"DIFFICULT TIMES\"",
    "21 CANBERRA: LAST SITTING WEEK",
]
BRIEFS_B = [
    "22 NEWSPOLL: ALBANESE TRAILS TAYLOR",
    "23 VICTORIA: EARLY VOTING OPEN",
    "24 FRED NILE DIES, 92",
    "25 HOME DEPOT: MCPHAIL TAKES OVER",
    "26 PETROBRAS: 2027-31 PLAN OUT",
    "27 BOLIDEN: EGM IN STOCKHOLM",
    "28 BOARDS & DEALS: CAPRICOR, TELUS, SITE",
    "29 TAIWAN BANS SHORT SALES; DAX +1.7%",
    "30 NZ RETAIL +2.2%; AUS PMI 46.1",
]

TIMELINE = ("UTC 09:00 BOLIDEN - 09:45 SHAH-MURMU - 13:30 CAPRICOR - "
            "14:00 HUANG BACK - 14:45 US PMIS - 16:20 $43.9BN DEAL - "
            "21:00 WILLIAMS - 21:00+ EARNINGS")

DATE_CHECK = ("BAYER SETTLEMENT FRI 20 NOV - KILLER-ROBOT TALKS ENDED "
              "SAT 21 NOV - PENNY LAW FRI 20 NOV - COP31 COLLAPSE SUN - "
              "DEMOCRATS 258 SEATS SUN - ALCARAZ ATP TITLE SUN - "
              "NIKKEI -5.06% FRI - GURU NANAK TUE 24 NOV")

# ---------------------------------------------------------------- build
def build():
    cv = Canvas(W, H, PAPER)
    X0, X1 = 14, 1010
    # kicker bar
    cv.rect(0, 0, W, 24, NAVY)
    draw_text(cv, 14, 5, 1.7, "sans", WHITE, "THE WORLD IN ONE DAY")
    rt = "30 STORIES - 7 REGIONS WITH NEWS"
    draw_text(cv, X1 - text_w(rt, 1.4), 6, 1.4, "sans", WHITE, rt)
    # masthead
    title = "MONDAY 23 NOVEMBER 2026"
    draw_text(cv, X0, 30, 5.0, "serif", INK, title)
    sub = "THE DAY IN FULL - EVERY STORY DATED MONDAY 23 NOVEMBER 2026"
    draw_text(cv, X0, 76, 1.5, "sans", RED, sub)
    pr = "PRESS 23:00 UTC"
    draw_text(cv, X1 - text_w(pr, 1.5), 76, 1.5, "sans", GREY, pr)
    cv.rect(X0, 94, X1 - X0, 2, RED)
    # figures band
    y = 100
    cell_w = (X1 - X0) // 6
    for i, (num, lab, col, nsc) in enumerate(FIGURES):
        cx = X0 + i * cell_w
        if i:
            cv.rect(cx - 1, y + 4, 1, 46, LIGHT)
        draw_text(cv, cx + 4, y + 4, nsc, "serif", col, num)
        draw_text(cv, cx + 4, y + 38, 1.25, "sans", GREY, lab)
    cv.rect(X0, y + 52, X1 - X0, 1, GREY)
    # region bar
    y = 156
    rx = X0
    for (lab, n, col, wdt, sc) in REGIONS:
        cv.rect(rx, y, wdt, 22, col)
        t = "%s %d" % (lab, n)
        draw_text(cv, rx + (wdt - text_w(t, sc)) // 2, y + 5, sc,
                  "sans", WHITE, t)
        rx += wdt
    # markets line
    y = 182
    mk = ("MARKETS: EUROZONE PMI 51.7 - GERMANY 55.0 - FRANCE 46.2 - "
          "UK 52.3 - BRENT NEAR 13-WEEK LOW - WTI BELOW $80")
    draw_text(cv, X0, y, 1.35, "sans", NAVY2, mk)
    # hero
    y = 200
    hy = y
    scene_hero(cv, X0, hy, 480, 232)
    tx = X0 + 494
    tw = X1 - tx
    cv.rect(tx - 6, hy, 2, 232, RED)
    draw_text(cv, tx, hy + 2, 1.35, "sans", RED,
              "1 - AMERICAS - MARKETS - CONFIRMED")
    draw_text(cv, tx, hy + 24, 6.5, "serif", INK, "HUANG")
    draw_text(cv, tx, hy + 80, 6.5, "serif", INK, "IS BACK")
    deck = wrap("NVIDIA BOARD REINSTATES ITS FOUNDER-CEO AFTER 11 DAYS",
                1.7, tw)
    yy = draw_lines(cv, tx, hy + 140, 1.7, "sans", INK, deck, 20)
    body = wrap(HERO_BODY, 1.45, tw)
    draw_lines(cv, tx, yy + 4, 1.45, "sans", INK, body, 16)
    # secondary leads
    y = 436
    for i, (num, region, tag, scene, head, body_txt) in enumerate(
            SECONDARY):
        sx = X0 + i * 504
        cv.rect(sx, y, 492, 124, CREAM)
        cv.rect(sx, y, 492, 2, REGION_COLORS[region])
        scene(cv, sx + 6, y + 6, 140, 112)
        stx = sx + 154
        draw_text(cv, stx, y + 8, 1.3, "sans", RED,
                  "%s - %s - %s" % (num, region, tag))
        hl = wrap(head, 2.4, 492 - 160)
        yy = draw_lines(cv, stx, y + 28, 2.4, "serif", INK, hl, 24)
        bl = wrap(body_txt, 1.35, 492 - 160)
        draw_lines(cv, stx, yy + 2, 1.35, "sans", INK, bl, 15)
    # UTC timeline strip
    y = 564
    cv.rect(0, y, W, 20, NAVY)
    tsc = 1.0
    while text_w(TIMELINE, tsc) > X1 - X0 and tsc > 0.7:
        tsc -= 0.05
    draw_text(cv, X0, y + 4, tsc, "sans", WHITE, TIMELINE)
    # cards: 2 rows x 4
    y = 588
    cw, chh, gap = 245, 96, 5
    for idx, (num, region, scene, head, body_txt) in enumerate(CARDS):
        r, c = divmod(idx, 4)
        cx = X0 + c * (cw + gap)
        cy = y + r * (chh + 4)
        cv.rect(cx, cy, cw, chh, CREAM)
        cv.rect(cx, cy, cw, 2, REGION_COLORS[region])
        scene(cv, cx + 4, cy + 6, cw - 8, 42)
        nw = text_w("%s " % num, 1.5)
        draw_text(cv, cx + 4, cy + 52, 1.5, "serif", RED, "%s " % num)
        draw_text(cv, cx + 4 + nw, cy + 52, 1.5, "serif", INK, head)
        bl = wrap(body_txt, 1.25, cw - 8)
        draw_lines(cv, cx + 4, cy + 70, 1.25, "sans", INK, bl[:2], 12)
    # briefs
    y = 788
    draw_text(cv, X0, y, 1.5, "sans", NAVY2,
              "ALSO ON MONDAY 23 NOVEMBER - 19 MORE STORIES")
    cv.rect(X0, y + 16, X1 - X0, 1, GREY)
    y += 22
    for col_list, bx in ((BRIEFS_A, X0), (BRIEFS_B, X0 + 500)):
        yy = y
        for b in col_list:
            draw_text(cv, bx, yy, 1.2, "sans", INK, b)
            yy += 13
    # bottom band: map + date check
    y = 944
    cv.rect(X0, y, X1 - X0, 1, GREY)
    draw_text(cv, X0, y + 6, 1.2, "sans", NAVY2,
              "WHERE IT HAPPENED - PINS MATCH STORY NUMBERS")
    draw_map(cv, X0, y + 18, 400, 40)
    dx = X0 + 420
    draw_text(cv, dx, y + 6, 1.3, "sans", RED,
              "DATE CHECK - LEFT OUT: NOT MONDAY 23 NOVEMBER")
    dc = wrap(DATE_CHECK, 1.15, X1 - dx)
    draw_lines(cv, dx, y + 22, 1.15, "sans", INK, dc, 12)
    # footer
    draw_text(cv, X0, 1006, 0.95, "sans", GREY,
              "SOURCES: REUTERS - AP - AFP - BLOOMBERG - SEC - S&P GLOBAL "
              "- ESPNCRICINFO - ARIANESPACE - PIB - TBS - THE SQUIZ - SMH")
    draw_text(cv, X0, 1016, 0.95, "sans", GREY,
              "CONFIRMED = REPORTED AS FACT - CLAIM = ONE SIDE'S ACCOUNT - "
              "FORECAST = DUE LATER - SCENES ARE DRAWN ILLUSTRATIONS.")
    return cv

def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    cv = build()
    n = write_png(os.path.join(out, "entry.png"), W, H, cv.px)
    print("wrote entry.png %d bytes" % n)

if __name__ == "__main__":
    main()
