#!/usr/bin/env python3
"""The World in One Day -- Monday 23 November 2026, EVENING EDITION.

Draws a single evening-edition front page summing up 23 November
2026's world news -- the day as it ended, outcomes first -- and
writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

Pure Python 3.13 standard library only: no Pillow, no network.
A hand-built vector stroke font draws every letter; every scene is
drawn from primitives (rects, lines, discs, polygons) in this file.
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
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        r = max(0, (w - 1) // 2)
        while True:
            if r:
                self.disc(x0, y0, r, c)
            else:
                self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def poly(self, pts, c):
        # filled polygon, scanline fill
        pts = [(int(x), int(y)) for x, y in pts]
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for yy in range(max(0, min(ys)), min(self.h - 1, max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    if y1 != y0:
                        xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(xs[k]), yy, int(xs[k + 1]) - int(xs[k]) + 1, 1, c)

    def outline(self, pts, c, w=1):
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            self.line(x0, y0, x1, y1, c, w)

# ---------------------------------------------------------------- stroke font
# Glyphs on a 5-wide (x 0..4) by 7-tall (y 0..6) grid. Each glyph is a
# list of polylines; each polyline is "xy xy ..." with x,y one digit.
FONT = {
    "A": ["06 20", "20 46", "14 34"],
    "B": ["00 06", "00 30 41 32 02", "02 32 43 46 36 06"],
    "C": ["40 20 00 06 46 26"],
    "D": ["00 06", "00 30 41 45 36 06"],
    "E": ["40 00 06 46", "03 43"],
    "F": ["40 00 06", "03 43"],
    "G": ["40 20 00 06 46 36 34 44"],
    "H": ["00 06", "40 46", "03 43"],
    "I": ["10 30", "20 26", "06 46"],
    "J": ["00 40", "30 36", "36 46 06 02"],
    "K": ["00 06", "40 02", "02 46"],
    "L": ["00 06 46"],
    "M": ["00 06", "06 23", "23 40", "40 46"],
    "N": ["00 06", "06 40", "40 46"],
    "O": ["04 00 40 46 06 04"],
    "P": ["00 06", "00 40 42 32 02"],
    "Q": ["04 00 40 46 06 04", "24 46"],
    "R": ["00 06", "00 40 42 32 02", "02 46"],
    "S": ["40 00 04 34 44 46 06"],
    "T": ["00 40", "20 26"],
    "U": ["00 06 46 40"],
    "V": ["00 46 40"],
    "W": ["00 06 23 46 40"],
    "X": ["00 46", "40 06"],
    "Y": ["00 23", "40 23", "23 26"],
    "Z": ["00 40 06 46"],
    "0": ["04 00 40 46 06 04"],
    "1": ["12 20 26", "06 46"],
    "2": ["02 00 40 42 44 06 46"],
    "3": ["00 40 42 32", "32 42 44 46 06"],
    "4": ["04 34", "00 24", "24 26"],
    "5": ["40 00 03 43 46 06"],
    "6": ["40 00 06 46 44 34 04"],
    "7": ["00 40", "40 06"],
    "8": ["00 40 46 06 00", "02 42"],
    "9": ["00 40 44 04 00", "44 46"],
    ".": ["25 26"],
    ",": ["25 26", "25 16"],
    ":": ["22 23", "25 26"],
    ";": ["22 23", "25 26", "25 16"],
    "!": ["20 23", "25 26"],
    "?": ["02 00 40 42 32 23", "25 26"],
    "'": ["22 01"],
    '"': ["12 01", "32 21"],
    "-": ["03 43"],
    "/": ["40 06"],
    "(": ["30 10 06 26 32"],
    ")": ["10 30 46 26 12"],
    "+": ["20 26", "03 43"],
    "=": ["02 42", "04 44"],
    "*": ["20 26", "02 42", "00 46", "40 06"],
    "<": ["40 02", "02 46"],
    ">": ["00 42", "42 06"],
    "_": ["06 46"],
    "[": ["30 00 06 36"],
    "]": ["10 40 46 16"],
    "%": ["01 11 21 12 02 01", "40 06", "23 33 43 34 24 23"],
    " ": [],
}


def glyph_width(ch):
    return 6  # advance in grid units (5 + 1 gap)


def text_w(s, sc):
    return int(len(s) * 6 * sc)


def draw_text(cv, x, y, s, w, c, s_):
    """Draw text at grid scale s (float ok), stroke width w."""
    s_ = s_.upper()
    cx = float(x)
    for ch in s_:
        strokes = FONT.get(ch)
        if strokes is None:
            ch2 = "?" if ch != " " else " "
            strokes = FONT.get(ch2, [])
        for stroke in strokes:
            pts = stroke.split()
            coords = [(int(p[0]), int(p[1])) for p in pts]
            for i in range(len(coords) - 1):
                x0, y0 = coords[i]
                x1, y1 = coords[i + 1]
                cv.line(cx + x0 * s, y + y0 * s, cx + x1 * s, y + y1 * s, c, w)
        cx += 6 * s
    return cx


def wrap(s_, width_chars):
    """Greedy word wrap to a max char count per line."""
    words = s_.split()
    lines, cur = [], ""
    for wd in words:
        if not cur:
            cur = wd
        elif len(cur) + 1 + len(wd) <= width_chars:
            cur += " " + wd
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_lines(cv, x, y, s, w, c, lines, lh=None):
    if lh is None:
        lh = int(8 * s) + 2
    for ln in lines:
        draw_text(cv, x, y, s, w, c, ln)
        y += lh
    return y

# ---------------------------------------------------------------- palette
PAPER = (247, 241, 222)
INK = (26, 26, 26)
NAVY = (20, 38, 77)
NAVY2 = (38, 62, 110)
RED = (179, 39, 30)
TEAL = (14, 107, 107)
GOLD = (197, 141, 28)
CREAM = (255, 250, 235)
GREY = (110, 105, 92)
LIGHT = (232, 224, 200)
GREEN = (31, 122, 63)
ORANGE = (214, 110, 24)

REGION_COLORS = {
    "EUROPE": (38, 62, 110),
    "MIDDLE EAST": (179, 39, 30),
    "ASIA-PACIFIC": (14, 107, 107),
    "AMERICAS": (31, 122, 63),
    "AFRICA": (197, 141, 28),
    "OCEANIA": (120, 66, 150),
    "WORLD": (110, 105, 92),
}

# ---------------------------------------------------------------- scenes
def scene_cricket(cv, x, y, w, h):
    # stumps, bat, ball on a green strip; "DRAW" implied by the art
    cv.rect(x, y, w, h, (31, 122, 63))
    cv.rect(x, y + h - 12, w, 12, (21, 92, 47))
    # pitch strip
    cv.rect(x + 18, y + 8, w - 36, h - 24, (214, 196, 150))
    # stumps
    sx = x + w // 2 - 4
    for dx in (-14, 0, 14):
        cv.rect(sx + dx, y + 14, 5, 34, GOLD)
    cv.rect(sx - 14, y + 11, 33, 4, GOLD)
    # bat leaning
    cv.line(x + 30, y + h - 14, x + 52, y + 22, (120, 82, 40), 7)
    cv.line(x + 52, y + 22, x + 58, y + 12, (120, 82, 40), 5)
    # ball
    cv.disc(x + w - 34, y + 26, 8, RED)
    cv.disc(x + w - 34, y + 26, 8, RED)
    # score tag
    cv.rect(x + w - 78, y + h - 26, 74, 20, INK)
    draw_text(cv, x + w - 72, y + h - 22, 1.2, 1, CREAM, "239/5")


def scene_flags(cv, x, y, w, h):
    # India flag (left) + Nepal pennon (right) over a saffron band
    cv.rect(x, y, w, h, (255, 240, 205))
    # India flag
    fx, fy, fw, fh = x + 12, y + 14, 62, 40
    cv.rect(fx, fy, fw, 13, (255, 153, 51))
    cv.rect(fx, fy + 13, fw, 14, CREAM)
    cv.rect(fx, fy + 27, fw, 13, (19, 136, 8))
    cv.disc(fx + fw // 2, fy + 20, 6, NAVY)
    # Nepal pennon (simplified double triangle)
    nx, ny = x + 92, y + 12
    cv.poly([(nx, ny), (nx + 34, ny + 18), (nx, ny + 26)], (220, 20, 60))
    cv.poly([(nx, ny + 26), (nx + 30, ny + 40), (nx, ny + 46)], (220, 20, 60))
    cv.line(nx, ny, nx, ny + 52, NAVY, 3)
    # handshake arc
    cv.line(x + 14, y + h - 12, x + w - 14, y + h - 12, NAVY, 2)


def scene_rocket(cv, x, y, w, h):
    # Ariane 64 on the pad, held: big red X across the sky
    cv.rect(x, y, w, h, (20, 38, 77))
    # stars
    for sx, sy in ((12, 10), (30, 22), (w - 18, 12), (w - 30, 30), (w - 60, 8)):
        cv.disc(x + sx, y + sy, 2, CREAM)
    # pad
    cv.rect(x + 10, y + h - 14, w - 20, 8, (110, 105, 92))
    # boosters
    for bx in (-34, 34):
        cv.rect(x + w // 2 + bx - 7, y + 34, 14, h - 48, (200, 200, 200))
    # core
    cv.rect(x + w // 2 - 11, y + 18, 22, h - 32, CREAM)
    cv.poly([(x + w // 2 - 11, y + 18), (x + w // 2 + 11, y + 18),
             (x + w // 2, y + 2)], RED)
    cv.rect(x + w // 2 - 11, y + 44, 22, 8, NAVY)
    # red X = scrubbed
    cv.line(x + 6, y + 6, x + w - 6, y + h - 6, RED, 7)
    cv.line(x + w - 6, y + 6, x + 6, y + h - 6, RED, 7)
    cv.rect(x + 8, y + h - 30, 66, 18, RED)
    draw_text(cv, x + 12, y + h - 26, 1.2, 1, CREAM, "HOLD")


# ---------------------------------------------------------------- content
LEADS = [
    ("WELLINGTON: A DRAW AFTER 120 OVERS",
     "Mitchell 49* and Phillips 26* bat 43 overs as NZ, 239/5, hold "
     "India after 720/9 declared. Conway 65.",
     "ESPNCRICINFO / ICC", scene_cricket),
    ("MODI AND SHAH: 24,000 CRORE FOR NEPAL",
     "India pledges 24,000 crore Nepali rupees, a joint vision for "
     "both nations, and a new Ayodhya-Janakpur train.",
     "PIB / AFP", scene_flags),
    ("ARIANE 6: THE LAUNCH THAT NEVER LEFT",
     "A fault in ground systems halts the count for 36 Amazon Leo "
     "satellites; the rocket stays safe on the pad until Tuesday.",
     "ARIANESPACE", scene_rocket),
]

SCOREBOARD = [
    ("239/5", "NZ DRAW, 120 OVERS"),
    ("720/9 DEC", "INDIA'S LEAD: 352"),
    ("24,000 CR", "NEPAL PACKAGE"),
    ("36", "LEO SATS SCRUBBED"),
    ("51.7", "EUROZONE PMI"),
    ("+2.2 PCT", "NZ RETAIL, Q3"),
]

# (country, composite PMI, region colour key)
PMI_BARS = [
    ("IND", 56.3, "ASIA-PACIFIC"),
    ("GER", 55.0, "EUROPE"),
    ("UK", 52.3, "EUROPE"),
    ("EURO", 51.7, "EUROPE"),
    ("FRA", 46.2, "EUROPE"),
    ("AUS", 46.1, "OCEANIA"),
]

BRIEFS = [
    ("EUROPE", "ZELENSKY: FOUR-WAY TALKS 'TOMORROW'",
     "Urges four-party talks 'as soon as possible' in a video address to NATO."),
    ("EUROPE", "KREMLIN WARNS OF BALTIC ESCALATION",
     "A Ukrainian drone sets Sparta II ablaze; it drifts into Finnish waters."),
    ("EUROPE", "DYMER TOLL RISES TO 11",
     "Rescue goes on at the block hit Sunday; debris falls on Kyiv schools Monday."),
    ("MIDDLE EAST", "HOUTHIS CLAIM SAUDI REFINERY HIT",
     "A Saudi strike hits Hodeida; 10 people are reported dead."),
    ("AFRICA", "SUDAN: FIVE CHILDREN KILLED",
     "Drone attacks strike homes in Khartoum and Omdurman."),
    ("MIDDLE EAST", "IRAN VOWS TO COUNTER US BLOCKADE",
     "Tehran says it will use 'all available means'."),
    ("MIDDLE EAST", "ISRAEL: COALITION TALKS RESUME",
     "Eisenkot meets Netanyahu's party; he calls settler attacks 'Jewish terrorism'."),
    ("OCEANIA", "AUSTRALIA NEARS SOLOMONS TREATY",
     "Canberra is close to a treaty with Solomon Islands, a minister says."),
    ("OCEANIA", "ALBANESE: COP31 'DIFFICULT TIMES'",
     "The PM blames geopolitics for the Antalya collapse."),
    ("ASIA-PACIFIC", "DHAKA: WAGE BOARD MEETS",
     "Workers demand Tk30,000 a month, up from Tk12,500; owners are to table their offer."),
    ("OCEANIA", "CANBERRA: LAST SITTING WEEK",
     "The gas reservation plan - up to 20 pct set aside from 2028 - heads the agenda."),
    ("OCEANIA", "NEWSPOLL: ALBANESE TRAILS TAYLOR",
     "The PM falls behind the Coalition leader as preferred PM for the first time."),
    ("OCEANIA", "VICTORIA: EARLY VOTING OPEN",
     "State polls are on Saturday 28 Nov; the Coalition leads 56-44."),
    ("OCEANIA", "FRED NILE DIES AT 92",
     "The former NSW MP and long-serving Christian Democrat dies."),
    ("AMERICAS", "HOME DEPOT: MCPHAIL TAKES OVER",
     "Richard McPhail takes office as chief executive."),
    ("AMERICAS", "PETROBRAS SETS OUT 2027-31 PLAN",
     "The state oil firm presents its five-year strategy."),
    ("EUROPE", "BOLIDEN HOLDS EGM IN STOCKHOLM",
     "Shareholders meet at 10:00 CET on a share issue."),
    ("AMERICAS", "BOARDS AND DEALS",
     "Capricor calls; Telus meets Quebecor; Spoons lock-up ends; SITE delists."),
]

TONIGHT = [
    "US FLASH PMIS 14:45 GMT - FORECAST: MFG 54.5, SERVICES 55.6",
    "FED'S WILLIAMS SPEAKS 21:00 GMT",
    "EARNINGS AFTER CLOSE: HPE, ZOOM, AGILENT, SYM, J, SMTC",
]

DATECHECK = [
    "KILLER-ROBOT TALKS ENDED SAT 21 NOV - NO BINDING RULES",
    "PENNY LAW FRI 20 NOV - COP31 COLLAPSED SUN - DEMOCRATS 258 SUN",
    "ALCARAZ ATP FINALS SUN - NIKKEI -5.06 PCT FRI; JAPAN SHUT MON",
]

# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)

    # ---- header 0..76: navy masthead
    cv.rect(0, 0, W, 76, NAVY)
    cv.rect(0, 72, W, 4, GOLD)
    draw_text(cv, 24, 14, 3.4, 3, CREAM, "THE WORLD IN ONE DAY")
    draw_text(cv, 24, 48, 1.7, 2, GOLD, "MONDAY 23 NOVEMBER 2026 - EVENING EDITION")
    draw_text(cv, 800, 16, 2.2, 2, CREAM, "34 STORIES")
    draw_text(cv, 800, 46, 1.5, 2, (200, 205, 220), "PRESS 12:30 UTC")

    # ---- scoreboard 76..156: "the day, decided"
    draw_text(cv, 24, 84, 1.5, 2, RED, "THE DAY, DECIDED - OUTCOMES, NOT FORECASTS")
    bw, bh = 162, 52
    for i, (num, lab) in enumerate(SCOREBOARD):
        x = 16 + i * (bw + 6)
        y = 104
        cv.rect(x, y, bw, bh, CREAM)
        cv.rect(x, y, bw, 3, REGION_COLORS["EUROPE"] if i % 2 == 0 else RED)
        draw_text(cv, x + 8, y + 8, 2.0, 2, INK, num)
        draw_text(cv, x + 8, y + 34, 1.1, 1, GREY, lab)

    # ---- leads 156..384: three horizontal strips
    ly = 156
    for k, (head, body, src, scene) in enumerate(LEADS):
        y0 = ly + k * 76
        cv.rect(0, y0, W, 1, LIGHT)
        scene(cv, 16, y0 + 6, 150, 64)
        draw_text(cv, 182, y0 + 6, 2.6, 2, NAVY, head)
        lines = wrap(body, 66)
        draw_lines(cv, 182, y0 + 32, 1.9, 2, INK, lines[:2], lh=17)
        draw_text(cv, 182, y0 + 66, 1.1, 1, GREY, "SOURCE: " + src)
        cv.rect(16, y0 + 70, W - 32, 1, LIGHT)
    cv.rect(0, 384, W, 1, INK)

    # ---- markets 384..456: horizontal PMI bars + market lines
    draw_text(cv, 24, 392, 1.7, 2, NAVY, "MARKETS: THE PMI DAY")
    draw_text(cv, 400, 392, 1.7, 2, RED, "ASIA SLIDES AS AI FEARS SPREAD")
    # 50-line at value 50 -> x = 56 + (50-40)*6 = 116
    cv.line(116, 406, 116, 452, GREY, 1)
    for i, (name, val, reg) in enumerate(PMI_BARS):
        by = 406 + i * 8
        draw_text(cv, 24, by, 1.0, 1, INK, name)
        blen = int((val - 40) * 6)
        cv.rect(56, by + 1, blen, 5, REGION_COLORS[reg])
        draw_text(cv, 56 + blen + 4, by, 1.0, 1, INK, str(val))
    mlines = wrap(
        "Taiwan bans short sales from Monday, its third curb this "
        "month. DAX up 1.7 pct. NZ retail jumps 2.2 pct in Q3, four "
        "times the forecast.", 52)
    draw_lines(cv, 400, 410, 1.5, 2, INK, mlines[:3], lh=15)

    # ---- briefs header 456..476
    cv.rect(0, 456, W, 20, NAVY2)
    draw_text(cv, 24, 460, 1.5, 2, CREAM, "THE WORLD IN BRIEF")
    draw_text(cv, 300, 461, 1.2, 1, (210, 214, 228),
              "EUROPE 10 - MIDDLE EAST 3 - ASIA-PACIFIC 5 - AMERICAS 6 - AFRICA 1 - OCEANIA 9")

    # ---- briefs 476..908: two columns x 9
    col_w = 496
    for idx, (reg, title, body) in enumerate(BRIEFS):
        col = idx // 9
        row = idx % 9
        x = 16 + col * (col_w + 16)
        y = 482 + row * 48
        cv.rect(x, y + 2, 10, 10, REGION_COLORS[reg])
        draw_text(cv, x + 16, y, 1.9, 2, INK, title)
        blines = wrap(body, 44)
        draw_lines(cv, x + 16, y + 18, 1.7, 2, (60, 58, 50), blines[:2], lh=14)
        if row < 8:
            cv.rect(x, y + 44, col_w - 16, 1, LIGHT)

    # ---- tonight + date check 908..976
    cv.rect(16, 908, 496, 68, CREAM)
    cv.rect(16, 908, 496, 3, RED)
    draw_text(cv, 28, 916, 1.5, 2, RED, "TONIGHT, STILL TO COME")
    for i, t in enumerate(TONIGHT):
        draw_text(cv, 28, 934 + i * 13, 1.2, 1, INK, t)
    cv.rect(512, 908, 496, 68, CREAM)
    cv.rect(512, 908, 496, 3, NAVY)
    draw_text(cv, 524, 916, 1.5, 2, NAVY, "DATE CHECK - NOT MONDAY")
    for i, t in enumerate(DATECHECK):
        draw_text(cv, 524, 934 + i * 13, 1.2, 1, INK, t)

    # ---- footer 976..1024
    draw_text(cv, 24, 984, 1.4, 1, GREY,
              "SOURCES: ESPNCRICINFO, ICC, AP, PIB, MEA, AFP, ARIANESPACE, S AND P GLOBAL, TBS, THE SQUIZ, SMH.")
    draw_text(cv, 24, 1002, 1.4, 1, GREY,
              "ALL STORIES MONDAY 23 NOVEMBER 2026 UNLESS MARKED. CONFIRMED = REPORTED AS FACT - FORECAST = DUE LATER.")
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    n = write_png(path, W, H, cv.px)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
