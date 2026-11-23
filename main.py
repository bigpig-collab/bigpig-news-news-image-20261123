#!/usr/bin/env python3
"""The World in One Day -- Monday 23 November 2026.

Draws a single broadsheet front page summing up 23 November 2026's
world news and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

Pure Python 3.13 standard library only: no Pillow, no network.
A hand-built 5x7 bitmap font draws the body text; a hand-built stroke
font with serif ticks draws the display headlines. Every scene is drawn
from primitives (rects, lines, discs, polygons) in this file.
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

    def hline(self, x, y, w, c, t=1):
        for k in range(t):
            self.rect(x, y + k, w, 1, c)

    def vline(self, x, y, h, c, t=1):
        for k in range(t):
            self.rect(x + k, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            for a in range(t):
                for b in range(t):
                    self.put(x + a - t // 2, y + b - t // 2, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.rect(cx - dx, yy, dx * 2 + 1, 1, c)

    def circle(self, cx, cy, r, c, t=1):
        steps = max(24, int(6.28 * r))
        for k in range(steps):
            a = 6.28318 * k / steps
            self.disc(cx + int(r * math.cos(a)),
                      cy + int(r * math.sin(a)), t, c)

    def tri(self, pts, c):
        pts = [(int(a), int(b)) for a, b in pts]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            inter = []
            for k in range(3):
                x0, y0 = pts[k]
                x1, y1 = pts[(k + 1) % 3]
                if y0 == y1:
                    continue
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    inter.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            if len(inter) >= 2:
                self.rect(int(min(inter)), yy, int(max(inter)) - int(min(inter)) + 1, 1, c)

    def poly(self, pts, c):
        # scanline fill for a simple polygon
        pts = [(int(a), int(b)) for a, b in pts]
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            inter = []
            n = len(pts)
            for k in range(n):
                x0, y0 = pts[k]
                x1, y1 = pts[(k + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    inter.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            inter.sort()
            for k in range(0, len(inter) - 1, 2):
                self.rect(int(inter[k]), yy, int(inter[k + 1]) - int(inter[k]) + 1, 1, c)

# ---------------------------------------------------------------- palette
PAPER = bytes([247, 241, 227])
INK = bytes([24, 28, 46])
NAVY = bytes([26, 42, 92])
NAVY2 = bytes([38, 58, 120])
RED = bytes([178, 34, 34])
RED2 = bytes([146, 24, 24])
GOLD = bytes([198, 148, 52])
TEAL = bytes([14, 110, 110])
GREEN = bytes([46, 125, 50])
AMBER = bytes([176, 118, 0])
GREY = bytes([110, 110, 105])
LGREY = bytes([214, 206, 188])
SKY = bytes([176, 205, 225])
SKY2 = bytes([142, 178, 205])
NIGHT = bytes([22, 30, 58])
WHITE = bytes([255, 255, 255])
BLACK = bytes([0, 0, 0])

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = ink. Designed in-session.
F57 = {}
def _g(ch, rows):
    F57[ch] = rows
_g("A", ["01110","10001","10001","11111","10001","10001","10001"])
_g("B", ["11110","10001","10001","11110","10001","10001","11110"])
_g("C", ["01110","10001","10000","10000","10000","10001","01110"])
_g("D", ["11110","10001","10001","10001","10001","10001","11110"])
_g("E", ["11111","10000","10000","11110","10000","10000","11111"])
_g("F", ["11111","10000","10000","11110","10000","10000","10000"])
_g("G", ["01110","10001","10000","10111","10001","10001","01111"])
_g("H", ["10001","10001","10001","11111","10001","10001","10001"])
_g("I", ["01110","00100","00100","00100","00100","00100","01110"])
_g("J", ["00111","00010","00010","00010","00010","10010","01100"])
_g("K", ["10001","10010","10100","11000","10100","10010","10001"])
_g("L", ["10000","10000","10000","10000","10000","10000","11111"])
_g("M", ["10001","11011","10101","10101","10001","10001","10001"])
_g("N", ["10001","11001","10101","10011","10001","10001","10001"])
_g("O", ["01110","10001","10001","10001","10001","10001","01110"])
_g("P", ["11110","10001","10001","11110","10000","10000","10000"])
_g("Q", ["01110","10001","10001","10001","10101","10010","01101"])
_g("R", ["11110","10001","10001","11110","10100","10010","10001"])
_g("S", ["01111","10000","10000","01110","00001","00001","11110"])
_g("T", ["11111","00100","00100","00100","00100","00100","00100"])
_g("U", ["10001","10001","10001","10001","10001","10001","01110"])
_g("V", ["10001","10001","10001","10001","10001","01010","00100"])
_g("W", ["10001","10001","10001","10101","10101","11011","10001"])
_g("X", ["10001","10001","01010","00100","01010","10001","10001"])
_g("Y", ["10001","10001","01010","00100","00100","00100","00100"])
_g("Z", ["11111","00001","00010","00100","01000","10000","11111"])
_g("0", ["01110","10001","10011","10101","11001","10001","01110"])
_g("1", ["00100","01100","00100","00100","00100","00100","01110"])
_g("2", ["01110","10001","00001","00110","01000","10000","11111"])
_g("3", ["11111","00010","00100","00010","00001","10001","01110"])
_g("4", ["00010","00110","01010","10010","11111","00010","00010"])
_g("5", ["11111","10000","11110","00001","00001","10001","01110"])
_g("6", ["00110","01000","10000","11110","10001","10001","01110"])
_g("7", ["11111","00001","00010","00100","01000","01000","01000"])
_g("8", ["01110","10001","10001","01110","10001","10001","01110"])
_g("9", ["01110","10001","10001","01111","00001","00010","01100"])
_g("a", [".....",".....",".111.","....1",".1111","1...1",".1111"])
_g("b", ["1....","1....","1.11.","1..1.","1..1.","1..1.","1.11."])
_g("c", [".....",".....",".111.","1....","1....","1....",".111."])
_g("d", ["....1","....1",".1111","1...1","1...1","1...1",".1111"])
_g("e", [".....",".....",".11..","1..1.","1111.","1....",".111."])
_g("f", ["..11.",".1..1",".1...","1111.",".1...",".1...",".1..."])
_g("g", [".....",".....",".1111","1...1","1...1",".1111","...1."])
_g("h", ["1....","1....","1.11.","1..1.","1..1.","1..1.","1..1."])
_g("i", [".....","..1..",".....",".11..","..1..","..1..",".111."])
_g("j", [".....","...1.",".....","..11.","...1.","...1.","..1.."])
_g("k", ["1....","1....","1..1.","1.1..","11...","1.1..","1..1."])
_g("l", [".11..","..1..","..1..","..1..","..1..","..1..",".111."])
_g("m", [".....",".....","11.1.","1.1.1","1.1.1","1.1.1","1.1.1"])
_g("n", [".....",".....","1.11.","1..1.","1..1.","1..1.","1..1."])
_g("o", [".....",".....",".111.","1...1","1...1","1...1",".111."])
_g("p", [".....",".....","1.11.","1..1.","1..1.","1.11.","1...."])
_g("q", [".....",".....",".1111","1...1","1...1",".1111","....1"])
_g("r", [".....",".....","1.11.","1..1.","1....","1....","1...."])
_g("s", [".....",".....",".1111","1....",".111.","....1","1111."])
_g("t", ["..1..",".1...","1111.",".1...",".1...",".1...","..11."])
_g("u", [".....",".....","1...1","1...1","1...1","1..11",".1111"])
_g("v", [".....",".....","1...1","1...1","1...1",".1.1.","..1.."])
_g("w", [".....",".....","1...1","1...1","1.1.1","1.1.1",".1.1."])
_g("x", [".....",".....","1...1",".1.1.","..1..",".1.1.","1...1"])
_g("y", [".....",".....","1...1","1...1",".1111","....1",".111."])
_g("z", [".....",".....","11111","...1.","..1..",".1...","11111"])
_g(" ", [".....",".....",".....",".....",".....",".....","....."])
_g(".", [".....",".....",".....",".....",".....",".11..",".11.."])
_g(",", [".....",".....",".....",".....",".....","..1..",".1..."])
_g(":", [".....",".....",".11..",".11..",".....",".11..",".11.."])
_g(";", [".....",".....",".11..",".11..",".....","..1..",".1..."])
_g("-", [".....",".....",".....","11111",".....",".....","....."])
_g("/", ["....1","...1.","...1.","..1..",".1...",".1...","1...."])
_g("(", ["...1.","..1..",".1...",".1...",".1...","..1..","...1."])
_g(")", [".1...","..1..","...1.","...1.","...1.","..1..",".1..."])
_g("%", ["1...1","1..1.","..1..",".1...",".1...","1..1.","1...1"])
_g("$", ["..1..",".1111","1.1.1",".111.","..1.1","1111.","..1.."])
_g("&", [".11..","1..1.","1.1..",".1...","1.1.1","1..1.",".11.1"])
_g("+", [".....","..1..","..1..","11111","..1..","..1..","....."])
_g("=", [".....",".....","11111",".....","11111",".....","....."])
_g("!", ["..1..","..1..","..1..","..1..","..1..",".....","..1.."])
_g("?", [".111.","1...1","....1","...1.","..1..",".....","..1.."])
_g('"', [".1.1.",".1.1.",".1.1.",".....",".....",".....","....."])
_g("'", [".1...",".1...","..1..",".....",".....",".....","....."])
_g("_", [".....",".....",".....",".....",".....",".....","11111"])
_g("#", [".1.1.",".1.1.","11111",".1.1.","11111",".1.1.",".1.1."])
_g("*", [".....",".1.1.",".111.","11111",".111.",".1.1.","....."])
_g("[", [".111.",".1...",".1...",".1...",".1...",".1...",".111."])
_g("]", [".111.","...1.","...1.","...1.","...1.","...1.",".111."])
_g("<", ["...1.","..1..",".1...","1....",".1...","..1..","...1."])
_g(">", [".1...","..1..","...1.","....1","...1.","..1..",".1..."])
_g("|", ["..1..","..1..","..1..","..1..","..1..","..1..","..1.."])
_g("°", [".11..","1..1.",".11..",".....",".....",".....","....."])
_g("·", [".....",".....",".....",".11..",".11..",".....","....."])
_g("—", [".....",".....",".....","11111",".....",".....","....."])
_g("–", [".....",".....",".....","11111",".....",".....","....."])
_g("’", [".1...",".1...","..1..",".....",".....",".....","....."])

def text_w(s, scale=1):
    return len(s) * 6 * scale - scale

def draw_text(cv, x, y, s, c, scale=1):
    """5x7 bitmap text, left aligned, baseline at y+7*scale."""
    cx = x
    for ch in s:
        rows = F57.get(ch, F57[" "])
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == "1":
                    cv.rect(cx + rx * scale, y + ry * scale, scale, scale, c)
        cx += 6 * scale
    return cx

def wrap_text(s, max_w, scale=1):
    """Greedy word wrap for the 5x7 font. Returns list of lines."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_para(cv, x, y, s, c, max_w, scale=1, lh=None, max_lines=None):
    lines = wrap_text(s, max_w, scale)
    if max_lines:
        lines = lines[:max_lines]
    lh = lh if lh is not None else 9 * scale
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, ln, c, scale)
    return y + len(lines) * lh

# ---------------------------------------------------------------- display font
# Stroke font on a 10x14 grid (x 0..10, y 0..14). Each glyph: list of
# strokes; each stroke: list of (x, y) points. Rendered with thick
# lines plus a serif tick at every stroke end on the cap or baseline.
DSTROKES = {
"A": [[(1, 14), (5, 0), (9, 14)], [(3, 9), (7, 9)]],
"B": [[(1, 0), (1, 14)], [(1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)],
      [(1, 7), (7, 7), (9, 9), (9, 12), (7, 14), (1, 14)]],
"C": [[(9, 2), (7, 0), (3, 0), (1, 2), (1, 12), (3, 14), (7, 14), (9, 12)]],
"D": [[(1, 0), (1, 14)], [(1, 0), (7, 0), (9, 2), (9, 12), (7, 14), (1, 14)]],
"E": [[(1, 0), (1, 14)], [(1, 0), (9, 0)], [(1, 7), (7, 7)], [(1, 14), (9, 14)]],
"F": [[(1, 0), (1, 14)], [(1, 0), (9, 0)], [(1, 7), (7, 7)]],
"G": [[(9, 3), (7, 0), (3, 0), (1, 2), (1, 12), (3, 14), (7, 14), (9, 12), (9, 8), (6, 8)]],
"H": [[(1, 0), (1, 14)], [(9, 0), (9, 14)], [(1, 7), (9, 7)]],
"I": [[(1, 0), (9, 0)], [(5, 0), (5, 14)], [(1, 14), (9, 14)]],
"J": [[(3, 0), (9, 0)], [(7, 0), (7, 12), (5, 14), (2, 14)]],
"K": [[(1, 0), (1, 14)], [(9, 0), (1, 7)], [(3, 9), (9, 14)]],
"L": [[(1, 0), (1, 14)], [(1, 14), (9, 14)]],
"M": [[(1, 14), (1, 0), (5, 7), (9, 0), (9, 14)]],
"N": [[(1, 14), (1, 0), (9, 14), (9, 0)]],
"O": [[(3, 0), (7, 0), (9, 2), (9, 12), (7, 14), (3, 14), (1, 12), (1, 2), (3, 0)]],
"P": [[(1, 0), (1, 14)], [(1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)]],
"Q": [[(3, 0), (7, 0), (9, 2), (9, 12), (7, 14), (3, 14), (1, 12), (1, 2), (3, 0)],
      [(6, 11), (10, 15)]],
"R": [[(1, 0), (1, 14)], [(1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)],
      [(5, 7), (9, 14)]],
"S": [[(9, 2), (7, 0), (3, 0), (1, 2), (1, 5), (3, 7), (7, 7), (9, 9), (9, 12), (7, 14), (3, 14), (1, 12)]],
"T": [[(1, 0), (9, 0)], [(5, 0), (5, 14)]],
"U": [[(1, 0), (1, 12), (3, 14), (7, 14), (9, 12), (9, 0)]],
"V": [[(1, 0), (5, 14), (9, 0)]],
"W": [[(1, 0), (3, 14), (5, 7), (7, 14), (9, 0)]],
"X": [[(1, 0), (9, 14)], [(9, 0), (1, 14)]],
"Y": [[(1, 0), (5, 7), (9, 0)], [(5, 7), (5, 14)]],
"Z": [[(1, 0), (9, 0), (1, 14), (9, 14)]],
"0": [[(3, 0), (7, 0), (9, 2), (9, 12), (7, 14), (3, 14), (1, 12), (1, 2), (3, 0)]],
"1": [[(3, 1), (5, 0), (5, 14)], [(1, 14), (9, 14)]],
"2": [[(1, 2), (3, 0), (7, 0), (9, 2), (9, 6), (1, 14), (9, 14)]],
"3": [[(1, 2), (3, 0), (7, 0), (9, 2), (9, 6), (7, 7), (9, 8), (9, 12), (7, 14), (3, 14), (1, 12)]],
"4": [[(7, 0), (7, 14)], [(1, 10), (9, 10)], [(1, 10), (7, 0)]],
"5": [[(9, 0), (1, 0), (1, 7), (7, 7), (9, 9), (9, 12), (7, 14), (3, 14), (1, 12)]],
"6": [[(9, 2), (7, 0), (3, 0), (1, 2), (1, 12), (3, 14), (7, 14), (9, 12), (9, 9), (7, 7), (1, 7)]],
"7": [[(1, 0), (9, 0), (4, 14)]],
"8": [[(3, 0), (7, 0), (9, 2), (9, 5), (7, 7), (3, 7), (1, 9), (1, 12), (3, 14), (7, 14), (9, 12), (9, 9), (7, 7)]],
"9": [[(9, 12), (7, 14), (3, 14), (1, 12), (1, 5), (3, 2), (7, 0), (9, 2), (9, 7), (7, 9), (1, 9)]],
".": [[(4, 13), (6, 13), (6, 15), (4, 15)]],
",": [[(4, 13), (6, 13), (6, 15), (4, 15)], [(5, 14), (3, 17)]],
":": [[(4, 4), (6, 4), (6, 6), (4, 6)], [(4, 11), (6, 11), (6, 13), (4, 13)]],
"-": [[(1, 7), (9, 7)]],
"/": [[(1, 14), (9, 0)]],
"'": [[(4, 0), (6, 0), (5, 3)]],
" ": [],
"%": [[(1, 1), (3, 1), (3, 3), (1, 3)], [(7, 11), (9, 11), (9, 13), (7, 13)], [(8, 0), (2, 14)]],
}

def dtext_w(s, size):
    # width of display text at cap-height `size` (px)
    unit = size / 14.0
    return len(s) * 11 * unit

def draw_dtext(cv, x, y, s, size, c, slant=0.0):
    """Display stroke text. (x, y) = top-left of cap height `size` px.
    slant: shear factor for a fake italic (dx per unit y)."""
    unit = size / 14.0
    lw = max(2, int(round(size / 13.0)))
    tick = max(2, int(round(size / 16.0)))
    cx = x
    for ch in s:
        strokes = DSTROKES.get(ch.upper(), DSTROKES.get(ch, []))
        for st in strokes:
            for k in range(len(st) - 1):
                (ax, ay), (bx, by) = st[k], st[k + 1]
                x0 = cx + (ax + slant * ay) * unit
                y0 = y + ay * unit
                x1 = cx + (bx + slant * by) * unit
                y1 = y + by * unit
                cv.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), c, lw)
        # serif ticks at cap and baseline stroke ends
        for st in strokes:
            for (px_, py_) in (st[0], st[-1]):
                if py_ in (0, 14):
                    tx = cx + (px_ + slant * py_) * unit
                    ty = y + py_ * unit
                    cv.rect(int(round(tx - 2 * unit)), int(round(ty - tick // 2)),
                            int(round(4 * unit)) + 1, tick, c)
        cx += 11 * unit
    return cx

def wrap_dtext(s, max_w, size):
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if dtext_w(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_dpara(cv, x, y, s, size, c, max_w, lh=None, max_lines=None, slant=0.0):
    lines = wrap_dtext(s, max_w, size)
    if max_lines:
        lines = lines[:max_lines]
    lh = lh if lh is not None else int(size * 1.25)
    for i, ln in enumerate(lines):
        draw_dtext(cv, x, y + i * lh, ln, size, c, slant)
    return y + len(lines) * lh

# ---------------------------------------------------------------- scenes
def sky(cv, x, y, w, h, top, bot):
    # two-band sky
    cv.rect(x, y, w, h // 2 + 1, top)
    cv.rect(x, y + h // 2, w, h - h // 2, bot)

def stars(cv, x, y, w, h, n, seed=7):
    s = seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        sx = x + s % w
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        sy = y + s % (h * 2 // 3)
        cv.put(sx, sy, WHITE)
        if s % 3 == 0:
            cv.put(sx + 1, sy, WHITE)

def flag_pole(cv, x, y, hgt, cols):
    cv.vline(x, y - hgt, hgt, INK, 2)
    fw, fh = 22, 13
    for i, c in enumerate(cols):
        cv.rect(x + 2, y - hgt + i * fh // len(cols), fw, fh // len(cols) + 1, c)

def person(cv, x, y, hgt, c):
    # simple standing figure: head + body + legs
    cv.disc(x, y, max(2, hgt // 6), c)
    cv.rect(x - max(1, hgt // 12), y + hgt // 6, 2 * max(1, hgt // 12) + 1, hgt // 2, c)
    cv.line(x - 1, y + hgt // 2 + hgt // 6, x - 3, y + hgt, c, 2)
    cv.line(x + 1, y + hgt // 2 + hgt // 6, x + 3, y + hgt, c, 2)

def building(cv, x, y, w, h, c, win=bytes([255, 214, 90])):
    cv.rect(x, y, w, h, c)
    for wy in range(y + 4, y + h - 4, 9):
        for wx in range(x + 4, x + w - 4, 9):
            cv.rect(wx, wy, 4, 5, win)

def scene_un(cv, x, y, w, h):
    sky(cv, x, y, w, h, SKY, bytes([205, 225, 238]))
    # UN flag blue field, white globe emblem on a pole
    flag_pole(cv, x + w // 2 - 30, y + h - 18, 46, [NAVY2, NAVY2])
    cv.disc(x + w // 2 - 18, y + h - 52, 9, WHITE)
    cv.circle(x + w // 2 - 18, y + h - 52, 9, NAVY2, 1)
    cv.hline(x + w // 2 - 27, y + h - 52, 18, NAVY2, 1)
    # conference hall
    cv.rect(x + 14, y + h - 34, w - 28, 34, bytes([226, 214, 192]))
    cv.rect(x + 14, y + h - 40, w - 28, 7, RED2)
    for i in range(6):
        fx = x + 24 + i * (w - 48) // 6
        flag_pole(cv, fx, y + h - 40, 16, [NAVY2])
    # delegates: small heads row
    for i in range(7):
        px_ = x + 26 + i * (w - 52) // 6
        cv.disc(px_, y + h - 24, 4, INK)
        cv.rect(px_ - 5, y + h - 20, 10, 12, bytes([90, 90, 100]))

def scene_nepal(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([250, 214, 150]), bytes([238, 190, 120]))
    # Himalaya ridge
    cv.poly([(x, y + h), (x + w * 0.2, y + h * 0.35), (x + w * 0.35, y + h),
             (x + w * 0.55, y + h * 0.25), (x + w * 0.75, y + h),
             (x + w * 0.9, y + h * 0.45), (x + w, y + h)], bytes([120, 130, 150]))
    cv.disc(x + w - 26, y + 22, 13, bytes([255, 196, 66]))
    # India Gate arch
    ax, ay = x + w // 2 - 22, y + h - 52
    cv.rect(ax, ay, 44, 52, bytes([196, 158, 110]))
    cv.rect(ax + 14, ay + 16, 16, 36, SKY)
    cv.rect(ax - 6, ay - 4, 56, 6, bytes([160, 120, 70]))
    # two flags: Nepal crimson, India saffron-white-green
    flag_pole(cv, x + 18, y + h - 8, 40, [RED2, RED2])
    cv.tri([(x + 20, y + h - 48), (x + 38, y + h - 43), (x + 20, y + h - 38)], RED2)
    flag_pole(cv, x + w - 40, y + h - 8, 40, [bytes([255, 153, 51]), WHITE, GREEN])
    # handshake table
    cv.rect(x + w // 2 - 26, y + h - 12, 52, 6, bytes([120, 80, 40]))
    person(cv, x + w // 2 - 16, y + h - 34, 22, INK)
    person(cv, x + w // 2 + 16, y + h - 34, 22, NAVY)

def scene_cricket(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([168, 208, 235]), bytes([200, 225, 240]))
    cv.disc(x + w - 24, y + 20, 11, bytes([255, 196, 66]))
    # outfield + pitch
    cv.rect(x, y + h * 3 // 5, w, h * 2 // 5, bytes([86, 148, 84]))
    cv.rect(x + w // 2 - 16, y + h * 3 // 5, 32, h * 2 // 5, bytes([214, 190, 150]))
    cv.rect(x + 8, y + h * 3 // 5, w - 16, 3, bytes([240, 240, 230]))
    # stumps
    for sx in (x + w // 2 - 8, x + w // 2, x + w // 2 + 8):
        cv.vline(sx, y + h - 26, 12, bytes([255, 214, 90]), 2)
    # batsman
    person(cv, x + w // 2 - 26, y + h - 34, 26, bytes([30, 60, 120]))
    cv.line(x + w // 2 - 26, y + h - 22, x + w // 2 - 12, y + h - 8, bytes([160, 110, 60]), 3)
    # bowler
    person(cv, x + w // 2 + 34, y + h - 34, 26, bytes([178, 34, 34]))
    # ball
    cv.disc(x + w // 2 + 12, y + h - 16, 3, RED)

def scene_pmi(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([225, 232, 240]), bytes([205, 218, 230]))
    # factory
    cv.rect(x + 8, y + h - 34, 52, 34, bytes([120, 120, 125]))
    cv.rect(x + 8, y + h - 48, 8, 16, bytes([90, 90, 95]))
    cv.rect(x + 20, y + h - 44, 8, 12, bytes([90, 90, 95]))
    cv.rect(x + 66, y + h - 26, 40, 26, bytes([150, 150, 155]))
    for wx in range(x + 14, x + 56, 12):
        cv.rect(wx, y + h - 28, 6, 7, bytes([255, 214, 90]))
    # rising bar chart
    base = y + h - 8
    bars = [10, 16, 13, 22, 30]
    for i, b in enumerate(bars):
        bx = x + w - 78 + i * 14
        cv.rect(bx, base - b, 9, b, TEAL if i < 4 else RED)
    cv.line(x + w - 82, base - 34, x + w - 8, base - 2, RED, 2)

def scene_earnings(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([232, 228, 214]), bytes([214, 206, 188]))
    # laptop + chart
    cv.rect(x + w // 2 - 34, y + h - 40, 68, 34, NAVY)
    cv.rect(x + w // 2 - 30, y + h - 36, 60, 26, bytes([220, 235, 245]))
    cv.line(x + w // 2 - 26, y + h - 14, x + w // 2 - 8, y + h - 24, GREEN, 2)
    cv.line(x + w // 2 - 8, y + h - 24, x + w // 2 + 6, y + h - 18, GREEN, 2)
    cv.line(x + w // 2 + 6, y + h - 18, x + w // 2 + 26, y + h - 32, GREEN, 2)
    cv.rect(x + w // 2 - 42, y + h - 6, 84, 5, bytes([140, 140, 140]))
    cv.disc(x + 16, y + 22, 7, GOLD)
    draw_text(cv, x + 12, y + 19, "$", INK, 1)

def scene_dhaka(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([245, 220, 170]), bytes([232, 200, 140]))
    # garment factory + workers
    cv.rect(x + 8, y + h - 40, 70, 40, bytes([160, 90, 60]))
    cv.rect(x + 8, y + h - 52, 10, 14, bytes([120, 60, 40]))
    for wx in range(x + 16, x + 72, 12):
        cv.rect(wx, y + h - 34, 6, 8, bytes([255, 214, 90]))
    for i in range(5):
        person(cv, x + 92 + i * 14, y + h - 26, 20, [INK, NAVY, RED2, TEAL, bytes([90, 60, 90])][i])
    # thread spools / cloth bolts
    for i, c in enumerate([RED, GOLD, TEAL, GREEN]):
        cv.rect(x + w - 52 + i * 12, y + 8, 9, 22, c)

def scene_canberra(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([170, 200, 225]), bytes([200, 220, 235]))
    # Parliament House: flag mast + lawn + building
    cv.vline(x + w // 2, y + 8, 26, INK, 2)
    cv.rect(x + w // 2 + 2, y + 10, 18, 11, NAVY)
    cv.rect(x + w // 2 + 2, y + 10, 18, 4, WHITE)
    cv.rect(x + 10, y + h - 30, w - 20, 30, bytes([220, 214, 198]))
    cv.rect(x + 10, y + h - 36, w - 20, 6, bytes([180, 170, 150]))
    for i in range(7):
        cx = x + 22 + i * (w - 44) // 6
        cv.rect(cx, y + h - 28, 6, 26, bytes([120, 110, 90]))
    cv.rect(x, y + h - 6, w, 6, bytes([86, 148, 84]))

def scene_poll(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([235, 232, 220]), bytes([220, 214, 198]))
    # ballot box
    cv.rect(x + w // 2 - 26, y + h - 34, 52, 30, NAVY)
    cv.rect(x + w // 2 - 30, y + h - 40, 60, 7, RED2)
    cv.rect(x + w // 2 - 6, y + h - 44, 12, 5, WHITE)
    draw_text(cv, x + w // 2 - 22, y + h - 28, "VOTE", WHITE, 1)
    # two poll bars (below the tag chip)
    cv.rect(x + 10, y + 18, 60, 9, RED2)
    cv.rect(x + 10, y + 32, 44, 9, NAVY2)
    draw_text(cv, x + 74, y + 19, "56", INK, 1)
    draw_text(cv, x + 58, y + 33, "44", INK, 1)

def scene_rocket(cv, x, y, w, h):
    sky(cv, x, y, w, h, NIGHT, bytes([40, 52, 90]))
    stars(cv, x, y, w, h, 18, 11)
    # Ariane 6: white body, orange boosters, flame
    rx = x + w // 2
    cv.rect(rx - 8, y + 12, 16, 34, WHITE)
    cv.rect(rx - 8, y + 12, 16, 6, RED)
    cv.tri([(rx - 8, y + 12), (rx + 8, y + 12), (rx, y + 2)], RED)
    cv.rect(rx - 15, y + 30, 6, 16, bytes([200, 200, 200]))
    cv.rect(rx + 9, y + 30, 6, 16, bytes([200, 200, 200]))
    cv.tri([(rx - 6, y + 46), (rx + 6, y + 46), (rx, y + h - 6)], bytes([255, 160, 40]))
    cv.tri([(rx - 3, y + 46), (rx + 3, y + 46), (rx, y + h - 14)], bytes([255, 220, 90]))
    # smoke
    for i, r in enumerate([7, 9, 11]):
        cv.disc(rx - 18 + i * 16, y + h - 8, r, bytes([200, 200, 205]))
    # satellite
    cv.rect(x + w - 30, y + 8, 12, 6, GOLD)
    cv.rect(x + w - 38, y + 10, 8, 2, NAVY2)
    cv.rect(x + w - 18, y + 10, 8, 2, NAVY2)

def scene_gurdwara(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([255, 214, 130]), bytes([245, 190, 90]))
    cv.disc(x + w - 22, y + 18, 12, bytes([255, 240, 180]))
    # gurdwara: dome + hall
    cv.rect(x + 12, y + h - 30, w - 24, 30, bytes([235, 220, 190]))
    cv.disc(x + w // 2, y + h - 30, 16, GOLD)
    cv.rect(x + w // 2 - 16, y + h - 32, 32, 4, GOLD)
    cv.vline(x + w // 2, y + h - 58, 12, INK, 2)
    cv.rect(x + w // 2 - 8, y + h - 22, 16, 22, bytes([120, 70, 40]))
    for i in range(4):
        cx = x + 24 + i * (w - 48) // 3
        cv.rect(cx, y + h - 24, 5, 16, bytes([120, 70, 40]))
    # candles row
    for i in range(6):
        cx = x + 14 + i * (w - 28) // 5
        cv.rect(cx, y + h - 8, 3, 6, WHITE)
        cv.disc(cx + 1, y + h - 10, 2, bytes([255, 180, 40]))

def scene_dymer(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([60, 60, 80]), bytes([90, 80, 90]))
    cv.disc(x + w - 24, y + 16, 10, bytes([220, 220, 200]))
    # ruined block: leaning walls + rubble
    cv.poly([(x + 14, y + h), (x + 14, y + 18), (x + 44, y + 10), (x + 44, y + h)], bytes([110, 100, 95]))
    cv.poly([(x + 50, y + h), (x + 50, y + 26), (x + 84, y + 34), (x + 84, y + h)], bytes([90, 82, 78]))
    for wx in range(x + 18, x + 42, 9):
        cv.rect(wx, y + 22, 5, 6, bytes([40, 40, 50]))
    # searchlight beam + crane
    cv.tri([(x + w - 12, y + h - 6), (x + w - 30, y + 8), (x + w - 6, y + 8)], bytes([255, 240, 160]))
    cv.line(x + 8, y + h - 6, x + w - 40, y + 10, bytes([200, 160, 40]), 3)
    # rubble + rescuer
    for i in range(5):
        cv.rect(x + 48 + i * 9, y + h - 10, 7, 6, bytes([130, 120, 110]))
    person(cv, x + w - 22, y + h - 24, 18, bytes([255, 160, 40]))

def scene_cop31(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([205, 210, 225]), bytes([190, 195, 210]))
    # plenary hall, empty chairs, no-deal banner
    cv.rect(x + 8, y + h - 34, w - 16, 34, bytes([150, 130, 110]))
    cv.rect(x + 8, y + h - 40, w - 16, 6, bytes([120, 100, 80]))
    for i in range(8):
        cx = x + 18 + i * (w - 36) // 7
        cv.rect(cx, y + h - 28, 10, 14, bytes([90, 90, 100]))
        cv.disc(cx + 5, y + h - 32, 3, bytes([200, 180, 150]))
    # globe + red cross
    cv.disc(x + w // 2, y + 24, 16, bytes([110, 170, 110]))
    cv.disc(x + w // 2 - 5, y + 20, 7, bytes([70, 130, 180]))
    cv.line(x + w // 2 - 12, y + 12, x + w // 2 + 12, y + 36, RED, 4)
    cv.line(x + w // 2 + 12, y + 12, x + w // 2 - 12, y + 36, RED, 4)
    cv.rect(x + w - 64, y + 8, 52, 12, RED2)
    draw_text(cv, x + w - 61, y + 11, "NO DEAL", WHITE, 1)

def scene_japan(cv, x, y, w, h):
    sky(cv, x, y, w, h, bytes([250, 230, 200]), bytes([240, 200, 160]))
    cv.disc(x + w // 2, y + 22, 14, RED)
    # torii gate
    cv.rect(x + w // 2 - 34, y + h - 46, 68, 5, RED2)
    cv.rect(x + w // 2 - 28, y + h - 38, 56, 4, RED2)
    cv.rect(x + w // 2 - 24, y + h - 38, 5, 38, RED2)
    cv.rect(x + w // 2 + 19, y + h - 38, 5, 38, RED2)
    cv.rect(x + w // 2 - 2, y + h - 38, 4, 38, RED2)
    # closed shutter
    cv.rect(x + w // 2 - 26, y + h - 14, 52, 8, bytes([120, 110, 100]))
    draw_text(cv, x + 8, y + 16, "LABOUR", INK, 1)
    draw_text(cv, x + 8, y + 26, "THANKSGIVING", INK, 1)

LEAD_SCENES = [scene_un, scene_nepal, scene_cricket]
CARD_SCENES = [scene_pmi, scene_earnings, scene_dhaka, scene_canberra,
               scene_poll, scene_rocket, scene_gurdwara, scene_dymer,
               scene_cop31, scene_japan]

def tag_chip(cv, x, y, tag, scale=1):
    """Coloured tag pill: CONFIRMED green / REPORTED blue / CLAIM amber /
    PENDING grey / FORECAST purple-grey / ONGOING teal."""
    cols = {"CONFIRMED": GREEN, "REPORTED": NAVY2, "CLAIM": AMBER,
            "PENDING": GREY, "FORECAST": bytes([100, 80, 140]),
            "ONGOING": TEAL}
    c = cols.get(tag, GREY)
    wdt = len(tag) * 6 * scale + 6 * scale
    cv.rect(x, y, wdt, 9 * scale, c)
    draw_text(cv, x + 3 * scale, y + scale, tag, WHITE, scale)
    return wdt

# ---------------------------------------------------------------- world map
# Land as (x0, y0, x1, y1) blocks on a 96x32 grid; dots drawn for cells
# inside any block. Grid: lon -180..180 -> x, lat 90..-90 -> y.
MAP_BLOCKS = [
    (3, 3, 19, 6), (4, 7, 18, 11), (7, 12, 14, 13), (10, 14, 13, 15),
    (24, 1, 27, 3), (50, 2, 55, 4), (46, 5, 56, 8), (46, 8, 49, 9),
    (45, 4, 46, 5), (46, 10, 58, 15), (47, 16, 54, 19), (49, 20, 52, 22),
    (59, 20, 60, 22), (57, 8, 62, 11), (57, 3, 88, 5), (58, 6, 88, 9),
    (64, 10, 84, 12), (74, 13, 80, 15), (76, 16, 86, 18), (88, 6, 91, 9),
    (80, 20, 90, 23), (82, 24, 88, 25), (93, 24, 95, 27),
    (22, 15, 29, 19), (23, 20, 28, 23), (25, 24, 27, 27),
]
MAP_PINS = {  # story number -> (lon, lat)
    1: (6.1, 46.2), 2: (77.2, 28.6), 3: (174.8, -41.3), 4: (-0.1, 51.5),
    5: (-74.0, 40.7), 6: (90.4, 23.8), 7: (149.1, -35.3), 8: (151.2, -33.9),
    9: (-52.9, 5.2), 10: (74.9, 31.6), 11: (30.3, 50.8), 12: (30.7, 36.9),
    13: (139.7, 35.7),
}

def draw_map(cv, x, y, cell=5, rows=29):
    cv.rect(x, y, 96 * cell, rows * cell, bytes([203, 220, 233]))
    land = bytes([96, 110, 128])
    for gy in range(rows):
        for gx in range(96):
            for (x0, y0, x1, y1) in MAP_BLOCKS:
                if x0 <= gx <= x1 and y0 <= gy <= y1:
                    cv.rect(x + gx * cell + 1, y + gy * cell + 1, 2, 2, land)
                    break
    for num, (lon, lat) in sorted(MAP_PINS.items()):
        gx = int((lon + 180) / 360 * 96)
        gy = int((90 - lat) / 180 * 32)
        if gy >= rows:
            continue
        px_, py_ = x + gx * cell + 2, y + gy * cell + 2
        cv.disc(px_, py_, 8, RED)
        cv.circle(px_, py_, 8, WHITE, 1)
        s = str(num)
        draw_text(cv, px_ - (len(s) * 6 - 1) // 2, py_ - 3, s, WHITE, 1)

# ---------------------------------------------------------------- content
FIGURES = [
    ("139/4", "NZ, day 5,", "Wellington"),
    ("213", "runs NZ trail", "by"),
    ("6", "wickets India", "need"),
    ("4M", "garment workers,", "Dhaka talks"),
    ("20%", "gas set aside,", "Canberra plan"),
    ("54.5", "US flash PMI", "forecast"),
]
REGIONS = [
    ("EUROPE", 6, TEAL), ("MIDDLE EAST", 0, RED), ("ASIA-PACIFIC", 8, AMBER),
    ("AMERICAS", 9, NAVY), ("AFRICA", 0, GREEN), ("OCEANIA", 8, bytes([100, 80, 140])),
    ("WORLD", 1, GREY),
]
UTC_ITEMS = ["22:00 Day 5 resumes", "00:02 UN talks continue",
             "09:00 Boliden EGM", "13:30 Capricor call", "14:45 US PMIs",
             "21:00 Williams speaks", "21:00+ HPE, Zoom"]
LEADS = [
    dict(num=1, scene=scene_un, chip="REPORTED",
         stat="00:02 UTC", kicker="1 GENEVA · UN · DIPLOMACY",
         headline="KILLER ROBOTS: TALKS GO ON",
         body="Nations agree to keep negotiating a treaty on lethal autonomous weapons; the Geneva talks run on.",
         source="salonvision"),
    dict(num=2, scene=scene_nepal, chip="REPORTED",
         stat="NEW DELHI", kicker="2 NEW DELHI · INDIA · DIPLOMACY",
         headline="SHAH MEETS MODI IN DELHI",
         body="Nepal's PM holds bilateral talks with Modi in New Delhi, day two of his state visit to India.",
         source="observervoice"),
    dict(num=3, scene=scene_cricket, chip="REPORTED",
         stat="DAY 5 LIVE", kicker="3 WELLINGTON · CRICKET · TEST",
         headline="WELLINGTON: NZ 139/4, TRAIL 213",
         body="Conway and Ravindra fall early on day five; India need six wickets, NZ bat to save the draw.",
         source="ESPNcricinfo"),
]
CARDS = [
    dict(num=4, scene=scene_pmi, chip="FORECAST",
         kicker="4 EUROPE · ECONOMY (SAXO)",
         headline="FLASH PMIS TODAY",
         body="France, Germany, euro, UK, US flash PMIs; US mfg seen 54.5."),
    dict(num=5, scene=scene_earnings, chip="PENDING",
         kicker="5 NEW YORK · MARKETS (TV)",
         headline="EARNINGS TONIGHT",
         body="HPE, Zoom, Agilent, Symbotic, Jacobs, Semtech report."),
    dict(num=6, scene=scene_dhaka, chip="PENDING",
         kicker="6 DHAKA · LABOUR (CBD)",
         headline="DHAKA WAGE TALKS",
         body="Wage board meets on a new minimum for 4m garment workers."),
    dict(num=7, scene=scene_canberra, chip="REPORTED",
         kicker="7 CANBERRA · POLITICS (SQUIZ)",
         headline="LAST SITTING WEEK",
         body="Gas reservation plan and tax bills lead the final week."),
    dict(num=8, scene=scene_poll, chip="REPORTED",
         kicker="8 SYDNEY · POLLS (SQUIZ)",
         headline="ALBANESE TRAILS",
         body="Albanese trails Taylor as preferred PM for the first time."),
    dict(num=9, scene=scene_rocket, chip="FORECAST",
         kicker="9 GUIANA · SPACE (FRONTIER)",
         headline="LEO LAUNCH DUE",
         body="Amazon Leo satellites ride Ariane 6 from French Guiana."),
    dict(num=10, scene=scene_gurdwara, chip="REPORTED",
         kicker="10 AMRITSAR · FAITH",
         headline="GURU NANAK DAY",
         body="Guru Nanak Jayanti observed across India and the world."),
    dict(num=11, scene=scene_dymer, chip="ONGOING",
         kicker="11 DYMER · UKRAINE (AJ)",
         headline="DYMER RESCUE ON",
         body="Rescue goes on at the Kyiv block hit Sunday; 11 missing."),
    dict(num=12, scene=scene_cop31, chip="REPORTED",
         kicker="12 ANTALYA · CLIMATE (TBS)",
         headline="AFTER COP31",
         body="Guterres 'deeply disappointed'; the work moves to Bonn."),
    dict(num=13, scene=scene_japan, chip="REPORTED",
         kicker="13 TOKYO · HOLIDAY (ASM)",
         headline="JAPAN SHUT",
         body="Japan closed for Labour Thanksgiving; no data, markets shut."),
]
BRIEFS = [
    (14, "Americas", "Petrobras 2027-31 plan"),
    (15, "Americas", "Home Depot new CEO"),
    (16, "Americas", "Williams speaks 21:00"),
    (17, "Oceania", "Victoria voting open"),
    (18, "Oceania", "Rev Fred Nile, 92"),
    (19, "Oceania", "NZ retail sales due"),
    (20, "Asia-Pacific", "China PMIs due"),
    (21, "Asia-Pacific", "India PMIs due"),
    (22, "Oceania", "Australia PMIs due"),
    (23, "Asia-Pacific", "Bon Om Touk"),
    (24, "Asia-Pacific", "Trip.com reports"),
    (25, "Americas", "Jacobs after close"),
    (26, "Americas", "Semtech after close"),
    (27, "Oceania", "Sydney schools fill again"),
    (28, "Americas", "Capricor call 08:30"),
    (29, "Europe", "Boliden EGM 10:00 CET"),
    (30, "Americas", "Telus-Quebecor talks"),
    (31, "Europe", "Bending Spoons unlocked"),
    (32, "Americas", "SITE Centers delists"),
    (33, "World", "PCE, GDP due Wed"),
    (34, "Americas", "Wall St after sell-off"),
]
DATE_CHECK = ("DATE CHECK — Left out as other days' news: COP31 collapse, no deal "
    "(Sun) · 186 drones over Kyiv (Sat night-Sun) · Democrats clinch 258 House "
    "seats (Sun) · Alcaraz wins ATP Finals (Sun) · Liverpool 4-0 Man Utd (Sun) · "
    "Korea minister quits (Sun) · South Sudan raid, 24 killed (Sun) · WHO Ebola "
    "team trapped (Sun) · UKMTO tankers hit (Fri-Sat) · MV Star Line (7 Nov) · "
    "Nvidia probe (Fri) · 'El Chapo Isidro' (Sat) · Bayelsa toll 26 (Fri-Sun) · "
    "Verstappen wins Vegas GP (Sun). Sunday's real count: 186 drones, not 400.")
SOURCES = ("Sources: Reuters, AP, AFP, Al Jazeera, ESPNcricinfo, The Squiz, SMH, TBS, "
    "TradingView, Saxo, FXEmpire, Asian Sense, FrontierPicks, salonvision.")
CERTAINTY = ("CERTAINTY: REPORTED = the day's wires · CLAIM = one side's account · "
    "FORECAST = still to happen when drawn · Scenes are drawn illustrations, not photographs.")

# ---------------------------------------------------------------- layout
def draw_page(cv):
    M = 24
    X0, X1 = M, W - M
    CW = X1 - X0
    cv.rect(0, 0, W, H, PAPER)
    # top line
    draw_text(cv, X0, 8, "THE WORLD IN ONE DAY", INK, 1)
    right = "32 STORIES · 5 REGIONS WITH NEWS · EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    draw_text(cv, X1 - text_w(right, 1), 8, right, INK, 1)
    cv.hline(X0, 22, CW, INK, 2)
    # masthead
    mast = "MONDAY 23 NOVEMBER 2026"
    mw = dtext_w(mast, 46)
    draw_dtext(cv, X0 + (CW - mw) / 2, 28, mast, 46, NAVY)
    # red lead line, fake italic
    lead = "Killer robots, Modi-Shah talks, and a Test hanging in the balance"
    lw = dtext_w(lead, 17)
    draw_dtext(cv, X0 + (CW - lw) / 2, 92, lead, 17, RED, slant=0.15)
    cv.hline(X0, 114, CW, INK, 2)
    # figures band: 6 cells
    fy, fh = 118, 54
    cellw = CW / 6
    for i, (num, l1, l2) in enumerate(FIGURES):
        cx = X0 + i * cellw
        nw = dtext_w(num, 30)
        draw_dtext(cv, cx + (cellw - nw) / 2, fy, num, 30, RED)
        ly = fy + 36
        for j, ln in enumerate((l1, l2)):
            wdt = text_w(ln, 1)
            draw_text(cv, cx + (cellw - wdt) / 2, ly + j * 9, ln, INK, 1)
        if i:
            cv.vline(int(cx), fy + 2, fh - 4, LGREY, 1)
    cv.hline(X0, fy + fh, CW, INK, 1)
    # region bar
    ry, rh = 176, 22
    segw = CW / 7
    for i, (name, cnt, col) in enumerate(REGIONS):
        sx = X0 + i * segw
        cv.rect(int(sx), ry, int(segw) + 1, rh, col)
        lab = "%s %d" % (name, cnt)
        wdt = text_w(lab, 1)
        draw_text(cv, int(sx + (segw - wdt) / 2), ry + 8, lab, WHITE, 1)
    # UTC strip
    uy = 202
    cv.rect(X0, uy, CW, 20, NAVY)
    utc = "UTC — " + " · ".join(UTC_ITEMS)
    draw_text(cv, X0 + 8, uy + 7, utc, WHITE, 1)
    # leads: 3 columns
    ly0, lcolw, lgap = 228, 318, 11
    for i, ld in enumerate(LEADS):
        lx = X0 + i * (lcolw + lgap)
        ld["scene"](cv, lx, ly0, lcolw, 150)
        cv.rect(lx, ly0, lcolw, 150, bytes([0, 0, 0, 0])) if False else None
        # kicker bar on scene, top-left; stat box top-right
        tag = ld["chip"]
        tw = len(tag) * 6 + 6
        cv.rect(lx, ly0, tw + 8, 14, RED)
        draw_text(cv, lx + 4, ly0 + 4, tag, WHITE, 1)
        st = ld["stat"]
        sw = len(st) * 6 + 8
        cv.rect(lx + lcolw - sw, ly0, sw, 14, WHITE)
        draw_text(cv, lx + lcolw - sw + 4, ly0 + 4, st, INK, 1)
        # frame
        cv.rect(lx, ly0, lcolw, 1, INK)
        cv.rect(lx, ly0 + 149, lcolw, 1, INK)
        cv.rect(lx, ly0, 1, 150, INK)
        cv.rect(lx + lcolw - 1, ly0, 1, 150, INK)
        # kicker, headline, body, source
        ky = ly0 + 158
        draw_text(cv, lx, ky, ld["kicker"], RED, 1)
        hy = ky + 12
        draw_dpara(cv, lx, hy, ld["headline"], 23, NAVY, lcolw, lh=28, max_lines=2)
        by = hy + 58
        draw_para(cv, lx, by, ld["body"], INK, lcolw, scale=2, lh=18, max_lines=4)
        sy = by + 76
        draw_text(cv, lx, sy, "(" + ld["source"] + ")", GREY, 1)
    # cards: 2 rows x 5
    cy0, ccolw, cgap, crowh, crgap = 546, 188, 8, 115, 6
    for i, cd in enumerate(CARDS):
        row, col = divmod(i, 5)
        cx = X0 + col * (ccolw + cgap)
        cy = cy0 + row * (crowh + crgap)
        cd["scene"](cv, cx, cy, ccolw, 52)
        cv.rect(cx, cy, ccolw, 1, INK)
        cv.rect(cx, cy + 51, ccolw, 1, INK)
        cv.rect(cx, cy, 1, 52, INK)
        cv.rect(cx + ccolw - 1, cy, 1, 52, INK)
        tag = cd["chip"]
        tw = len(tag) * 6 + 6
        cv.rect(cx, cy, tw + 6, 12, RED)
        draw_text(cv, cx + 3, cy + 3, tag, WHITE, 1)
        ky = cy + 58
        draw_text(cv, cx, ky, cd["kicker"], RED, 1)
        hy = ky + 11
        draw_dtext(cv, cx, hy, cd["headline"], 14, NAVY)
        by = hy + 19
        draw_para(cv, cx, by, cd["body"], INK, ccolw, scale=1, lh=9, max_lines=2)
    # map + also
    my0 = 788
    draw_text(cv, X0, my0, "WHERE IT HAPPENED", RED, 1)
    draw_text(cv, X0 + 150, my0, "pins match story numbers", GREY, 1)
    draw_map(cv, X0, my0 + 12, cell=5, rows=29)
    ax0 = X0 + 488
    draw_text(cv, ax0, my0, "ALSO ON MONDAY 23 NOVEMBER — 21 MORE STORIES", RED, 1)
    colw = 240
    for i, (num, region, txt) in enumerate(BRIEFS):
        col = 0 if i < 11 else 1
        row = i if i < 11 else i - 11
        bx = ax0 + col * (colw + 8)
        by = my0 + 14 + row * 13
        draw_text(cv, bx, by, "%d %s: %s" % (num, region, txt), INK, 1)
    # date check box
    dy0 = 952
    cv.rect(X0, dy0, CW, 40, PAPER)
    cv.rect(X0, dy0, CW, 2, RED)
    cv.rect(X0, dy0 + 38, CW, 2, RED)
    cv.rect(X0, dy0, 2, 40, RED)
    cv.rect(X0 + CW - 2, dy0, 2, 40, RED)
    draw_para(cv, X0 + 6, dy0 + 3, DATE_CHECK, RED2, CW - 12, scale=1, lh=9, max_lines=4)
    # footer
    draw_text(cv, X0, 998, SOURCES, INK, 1)
    draw_text(cv, X0, 1010, CERTAINTY, GREY, 1)

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, W, H, cv.px)
    print("wrote %s (%d bytes)" % (path, size))

if __name__ == "__main__":
    main()
