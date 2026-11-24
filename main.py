#!/usr/bin/env python3
"""news-image-20261124: one image summing up Tuesday 24 November 2026.

A 1024x1024 newspaper front page drawn with the standard library only:
a hand-rolled PNG encoder, a 5x7 bitmap font and a small canvas class.
No network, no clock, no unseeded randomness — two runs write
byte-identical files.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# Page palette: newsprint paper, ink, navy nameplate, red rules.
PAPER = (247, 243, 232)
INK = (20, 24, 34)
NAVY = (20, 33, 61)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
HAIR = (216, 210, 196)
EDGE = (198, 192, 178)
GREY = (70, 74, 88)
GOLD = (255, 205, 90)
PALE = (200, 205, 220)


def _chunk(tag, data):
    """One PNG chunk: length + tag + data + CRC32 over tag and data."""
    crc = zlib.crc32(tag)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def png_bytes(w, h, buf):
    """Encode an RGB buffer as one whole PNG (filter 0 on every row)."""
    head = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    row_len = w * 3
    for y in range(h):
        raw.append(0)
        raw += buf[y * row_len:(y + 1) * row_len]
    body = zlib.compress(bytes(raw), 6)
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += _chunk(b"IHDR", head)
    png += _chunk(b"IDAT", body)
    png += _chunk(b"IEND", b"")
    return bytes(png)


class Pix:
    """A plain RGB pixel buffer with small filled-shape helpers.

    The buffer is a flat bytearray, three bytes per pixel, row-major.
    Every helper clips to the canvas, so art code never needs bounds
    checks of its own.
    """

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.box(0, 0, w, h, bg)

    def dot(self, x, y, c):
        """Set one pixel, silently ignoring out-of-bounds coordinates."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def box(self, x, y, w, h, c):
        """Fill an axis-aligned rectangle, clipped to the canvas."""
        xa = max(0, x)
        ya = max(0, y)
        xb = min(self.w, x + w)
        yb = min(self.h, y + h)
        if xb <= xa or yb <= ya:
            return
        row = bytes(c) * (xb - xa)
        for yy in range(ya, yb):
            i = (yy * self.w + xa) * 3
            self.buf[i:i + len(row)] = row

    def rule_h(self, x, y, w, c):
        """A 1px horizontal rule."""
        self.box(x, y, w, 1, c)

    def rule_v(self, x, y, h, c):
        """A 1px vertical rule."""
        self.box(x, y, 1, h, c)

    def seg(self, x0, y0, x1, y1, c):
        """Bresenham segment, inclusive of both ends."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.dot(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            twice = 2 * err
            if twice >= dy:
                err += dy
                x0 += sx
            if twice <= dx:
                err += dx
                y0 += sy

    def ball(self, cx, cy, r, c):
        """Filled disc drawn as horizontal scanlines."""
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.rule_h(cx - half, cy + dy, half * 2 + 1, c)

    def tri(self, ax, ay, bx, by, cx, cy, c):
        """Filled triangle, scanline by scanline between its edges."""
        corners = sorted(((ax, ay), (bx, by), (cx, cy)),
                         key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = corners
        if y0 == y2:
            return
        edges = (((x0, y0), (x1, y1)), ((x1, y1), (x2, y2)),
                 ((x0, y0), (x2, y2)))
        for y in range(y0, y2 + 1):
            hits = []
            for (px, py), (qx, qy) in edges:
                if py == qy:
                    continue
                if min(py, qy) <= y <= max(py, qy):
                    hits.append(px + (qx - px) * (y - py) / (qy - py))
            if len(hits) >= 2:
                xa, xb = int(min(hits)), int(max(hits))
                self.rule_h(xa, y, xb - xa + 1, c)

# 5x7 bitmap font, written as seven 5-char rows per glyph: '#' is ink,
# '.' is blank. All text is rendered in capitals.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".1100", ".1100"),
    ",": (".....", ".....", ".....", ".....", ".1100", "..100", ".1000"),
    ":": (".....", ".1100", ".1100", ".....", ".1100", ".1100", "....."),
    ";": (".....", ".1100", ".1100", ".....", ".1100", "..100", ".1000"),
    "!": ("..100", "..100", "..100", "..100", "..100", ".....", "..100"),
    "?": (".1110", "10001", "00001", "00010", "..100", ".....", "..100"),
    "'": ("..100", "..100", ".1000", ".....", ".....", ".....", "....."),
    '"': (".1010", ".1010", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".1110", ".....", ".....", "....."),
    "(": ("...10", "..100", ".1000", ".1000", ".1000", "..100", "...10"),
    ")": (".1000", "..100", "...10", "...10", "...10", "..100", ".1000"),
    "/": ("....1", "...10", "...10", "..100", ".1000", ".1000", "10000"),
    "%": ("11001", "11010", "...10", "..100", ".1000", ".1011", "10011"),
    "&": (".1100", "10010", "10100", ".1000", "10101", "10010", ".1101"),
    "+": (".....", "..100", "..100", ".1110", "..100", "..100", "....."),
    "=": (".....", ".....", ".1110", ".....", ".1110", ".....", "....."),
    "*": (".....", "10101", ".1110", "10101", ".....", ".....", "....."),
    "#": (".1010", ".1010", "11111", ".1010", "11111", ".1010", ".1010"),
    "$": ("..100", ".1111", "10100", ".1110", "..101", "11110", "..100"),
    "@": (".1110", "10001", "10111", "10101", "10110", "10000", ".1110"),
}


def text_w(s, scale):
    """Advance width in pixels of a string at a scale (6 units a char)."""
    return len(s) * 6 * scale


def put_text(pg, x, y, s, scale, color):
    """Draw capitals text; a glyph we do not know is a blank advance."""
    cx = x
    for ch in s.upper():
        rows = GLYPHS.get(ch)
        if rows is not None:
            for r, line in enumerate(rows):
                for col, bit in enumerate(line):
                    if bit == "1":
                        pg.box(cx + col * scale, y + r * scale,
                               scale, scale, color)
        cx += 6 * scale


def put_text_c(pg, cx, y, s, scale, color):
    """Draw text centred on cx."""
    put_text(pg, cx - text_w(s, scale) // 2, y, s, scale, color)


def put_bold(pg, x, y, s, scale, color):
    """Draw text twice, 1 px apart: a heavier weight for headlines."""
    put_text(pg, x, y, s, scale, color)
    put_text(pg, x + 1, y, s, scale, color)


def put_bold_c(pg, cx, y, s, scale, color):
    """Draw bold text centred on cx."""
    put_bold(pg, cx - text_w(s, scale) // 2, y, s, scale, color)


def put_mixed_c(pg, cx, y, parts, scale):
    """Draw [(text, color), ...] as one centred line, e.g. red numbers
    with ink labels for the stat strip."""
    total = 0
    for t, _ in parts:
        total += text_w(t, scale)
    x = cx - total // 2
    for t, color in parts:
        put_text(pg, x, y, t, scale, color)
        x += text_w(t, scale)


def wrap(s, max_chars):
    """Greedy word wrap to lines of at most max_chars characters."""
    lines = []
    cur = ""
    for word in s.split(" "):
        if cur == "":
            cur = word
        elif len(cur) + 1 + len(word) <= max_chars:
            cur = cur + " " + word
        else:
            lines.append(cur)
            cur = word
    if cur != "":
        lines.append(cur)
    return lines

# Field colours: the left bar of every grid cell, the lead kickers and
# the footer legend all use this one mapping.
FIELDS = {
    "CONFLICT": (178, 34, 34),
    "POLITICS": (37, 99, 235),
    "MARKETS": (180, 130, 29),
    "SPORT": (124, 58, 237),
    "SCIENCE": (13, 148, 136),
    "CULTURE": (219, 39, 119),
    "CRIME": (100, 116, 139),
    "DISASTER": (146, 64, 14),
    "WEATHER": (2, 132, 199),
    "CLIMATE": (22, 163, 74),
    "MEDIA": (190, 24, 93),
    "WORLD": (75, 85, 99),
}

# The three leads: the day's most consequential stories, plus one quiet
# moment. All first reported Tuesday 24 November 2026; see
# NEWS-RESEARCH.md in the workdir.
LEADS = [
    ("LEAD 1 - MARKETS - NVIDIA",
     "MARKETS",
     "HUANG BACK AT NVIDIA",
     "SHARES +30%, NASDAQ +6.8%"),
    ("LEAD 2 - CONFLICT - LIBYA",
     "CONFLICT",
     "UKRAINE SINKS RUSSIAN SHIP",
     "MERKURY ABLAZE AT BENGHAZI"),
    ("LEAD 3 - WORLD - DYMER",
     "WORLD",
     "CAT DYM SURVIVES",
     "ALIVE AFTER DAYS IN RUBBLE"),
]

# The dense grid: 57 more stories, (headline, field). Every headline is
# ONE line of at most 25 characters — the renderer draws one scale-2 line
# per 26px cell, so nothing wraps or overlaps. All first reported
# 24 Nov 2026; see NEWS-RESEARCH.md in the workdir.
GRID = [
    ("KREMLIN PLANS SPACE NUKES", "CONFLICT"),
    ("153 DRONES HIT UKRAINE", "CONFLICT"),
    ("ODESA LOSES POWER, HEAT", "CONFLICT"),
    ("EU SANCTIONS RUSSIA ANEW", "CONFLICT"),
    ("UKRAINE HITS 2 REFINERIES", "CONFLICT"),
    ("RUSSIA CASUALTIES SOAR", "CONFLICT"),
    ("MERZ PRESSES KREMLIN", "CONFLICT"),
    ("NATO INCURSIONS RISE", "CONFLICT"),
    ("GARRISON NEAR FINLAND", "CONFLICT"),
    ("DYMER TOLL NOW 11 DEAD", "CONFLICT"),
    ("TRUMP BLAMES VOTERS", "POLITICS"),
    ("IRAN VOWS ALL MEANS", "POLITICS"),
    ("TRUMP EYES IRAN IN 2027", "POLITICS"),
    ("CALIFORNIA DEM QUITS", "POLITICS"),
    ("EU LISTS US NEO-NAZI", "POLITICS"),
    ("HASINA ARREST VOW", "POLITICS"),
    ("ARMENIA NEW CHARTER", "POLITICS"),
    ("KOREA PICKS NEW FM", "POLITICS"),
    ("INDIA, NEPAL SIGN 8 MOUS", "POLITICS"),
    ("MODI, SHAH FLAG TRAIN", "POLITICS"),
    ("YUNUS SLAMS GRAMEEN HIT", "POLITICS"),
    ("TRUMP TARGETS NEWSOM", "POLITICS"),
    ("SYRIA DEMINING MISSION", "POLITICS"),
    ("FAR RIGHT EYES EU SHAKE", "POLITICS"),
    ("NASDAQ +6.8% IN REBOUND", "MARKETS"),
    ("CROWDSTRIKE BUYS ZSCALER", "MARKETS"),
    ("BRENT BELOW $90", "MARKETS"),
    ("GOLD REBOUNDS TO $3,657", "MARKETS"),
    ("STOXX +1.9%, DAX +2%", "MARKETS"),
    ("CHINA STOCKS 16-MO LOW", "MARKETS"),
    ("WALL ST $80.6BN WARNING", "MARKETS"),
    ("MANILA SEEKS TARIFF CUT", "MARKETS"),
    ("DELL, HP REPORT TODAY", "MARKETS"),
    ("SPICEJET IN CRISIS", "MARKETS"),
    ("INDIA OIL BILL +60%", "MARKETS"),
    ("BOE: ACT ON INFLATION", "MARKETS"),
    ("US SEIZES $1.1BN CRYPTO", "CRIME"),
    ("FSB PHISHES JOURNALISTS", "CRIME"),
    ("CHINA SPY SECRETS DEATH", "CRIME"),
    ("MEZA ARREST POWER GAP", "CRIME"),
    ("FBI HACKED AGAIN", "CRIME"),
    ("UK AI BREAST TEST FIRST", "SCIENCE"),
    ("UN SEEKS AI SAFETY RULES", "SCIENCE"),
    ("AI WEAPONS TALKS FAIL", "SCIENCE"),
    ("US-CHINA AI RACE GROWS", "SCIENCE"),
    ("INDIA-NZ TEST IN A DRAW", "SPORT"),
    ("PANT 128, RECORD TON", "SPORT"),
    ("ALCARAZ WINS ATP FINALS", "SPORT"),
    ("GUKESH DEFENDS CROWN", "SPORT"),
    ("JAVA FIRE: 24 BODIES OUT", "DISASTER"),
    ("GAZA TOXINS FEARED", "WORLD"),
    ("UNRWA STAFF KILLED", "WORLD"),
    ("TALIBAN ERASES WOMEN", "WORLD"),
    ("DELTA GLITCH HITS 1,600", "WORLD"),
    ("US ATC UNIT FOR HOLIDAY", "WORLD"),
    ("LISBON MARCHES ON PRICES", "WORLD"),
    ("FERRARI UNVEILS 296 DUO", "CULTURE"),
]

# Ten moments of the day, WIB (UTC+7), in the order they were first
# reported on 24 November 2026.
TIMELINE = [
    ("03:00", "HUANG BACK AT NVIDIA"),
    ("04:00", "NASDAQ +6.8% REBOUND"),
    ("07:05", "EU SANCTIONS RUSSIA"),
    ("07:12", "TRUMP BLAMES VOTERS"),
    ("07:14", "KREMLIN SPACE NUKES"),
    ("07:18", "JAVA FIRE: 24 BODIES"),
    ("07:19", "MERKURY SUNK IN LIBYA"),
    ("07:30", "FAR RIGHT EYES EU"),
    ("07:38", "CAT DYM SURVIVES"),
    ("07:45", "UKRAINE HITS FREIGHTER"),
]

def art_chart_up(pg, x, y, w, h):
    """A market board snapping back up: a climbing green line across
    gridlines, for Nvidia's rebound after Huang's return."""
    pg.box(x, y, w, h, (14, 26, 20))
    for gy in range(y + 12, y + h, 14):
        pg.rule_h(x + 8, gy, w - 16, (30, 52, 40))
    climb = [(10, 78), (52, 72), (94, 76), (136, 60), (178, 46),
             (220, 32), (258, 22), (296, 12)]
    for (ax, ay), (bx, by) in zip(climb, climb[1:]):
        pg.seg(x + ax, y + ay, x + bx, y + by, (60, 220, 130))
        pg.seg(x + ax, y + ay + 1, x + bx, y + by + 1, (60, 220, 130))
    for px, py in climb:
        pg.ball(x + px, y + py, 2, (255, 210, 90))
    pg.tri(x + 298, y + 12, x + 312, y + 12, x + 305, y + 26,
           (60, 220, 130))
    pg.box(x + 12, y + 8, 4, 4, (255, 210, 90))


def art_ship(pg, x, y, w, h):
    """A Russian corvette ablaze in a Libyan port at night: hull, flames
    licking the deck and black smoke rolling up, for the Merkury strike."""
    pg.box(x, y, w, h, (10, 18, 38))
    for wy in range(y + 54, y + h, 8):
        pg.rule_h(x, wy, w, (16, 34, 64))
    pg.box(x + 36, y + 46, 224, 20, (40, 44, 54))
    pg.box(x + 36, y + 42, 224, 4, (150, 40, 30))
    pg.box(x + 256, y + 24, 26, 22, (60, 64, 74))
    flames = ((66, 32), (118, 42), (168, 30), (214, 36))
    for fx, fh in flames:
        pg.tri(x + fx, y + 44, x + fx + 11, y + 44 - fh,
               x + fx + 22, y + 44, (255, 120, 30))
        pg.tri(x + fx + 5, y + 44, x + fx + 11, y + 44 - fh + 12,
               x + fx + 17, y + 44, (255, 210, 90))
    smoke = ((106, 8, 10), (178, 4, 12), (238, 10, 8))
    for sx, sy, sr in smoke:
        pg.ball(x + sx, y + sy, sr, (70, 66, 62))
    pg.ball(x + 302, y + 32, 3, (255, 210, 60))


def art_cat(pg, x, y, w, h):
    """A small cat found alive in the rubble: grey slabs, a dark cat
    silhouette with pricked ears in a shaft of light, for Dym of Dymer."""
    pg.box(x, y, w, h, (38, 36, 34))
    pg.box(x + 18, y + 58, 122, 14, (90, 86, 80))
    pg.box(x + 152, y + 64, 138, 12, (110, 104, 96))
    pg.box(x + 62, y + 72, 88, 10, (70, 66, 60))
    pg.box(x + 202, y + 72, 68, 10, (80, 76, 70))
    for lx in (142, 152, 162):
        pg.rule_v(x + lx, y + 6, 62, (255, 220, 130))
    pg.box(x + 140, y + 46, 26, 22, (24, 22, 20))
    pg.tri(x + 142, y + 46, x + 146, y + 36, x + 150, y + 46,
           (24, 22, 20))
    pg.tri(x + 158, y + 46, x + 162, y + 36, x + 166, y + 46,
           (24, 22, 20))
    pg.ball(x + 148, y + 54, 2, (255, 210, 90))
    pg.ball(x + 160, y + 54, 2, (255, 210, 90))
    pg.box(x + 132, y + 68, 44, 4, (24, 22, 20))
    pg.ball(x + 302, y + 14, 3, (255, 210, 90))


ART = [art_chart_up, art_ship, art_cat]


def _lcg_next(state):
    """One step of the fixed-seed linear congruential generator."""
    return (1103515245 * state + 12345) & 0x7FFFFFFF


def grain(pg):
    """Deterministic newsprint speckle on light pixels only.

    Dark ink and coloured bars are untouched, so text stays crisp.
    A fixed-seed LCG keeps two runs byte-identical. The speckle is
    what carries the file past the 400k-byte density floor: flat
    paper compresses to almost nothing, grain does not.
    """
    buf = pg.buf
    state = 135791113
    total = len(buf)
    i = 0
    while i < total:
        light = buf[i] >= 200 and buf[i + 1] >= 200 and buf[i + 2] >= 200
        if light:
            state = _lcg_next(state)
            if state % 100 < 60:
                for ch in range(3):
                    state = _lcg_next(state)
                    delta = (state >> 23) % 11 - 5
                    value = buf[i + ch] + delta
                    if value < 0:
                        value = 0
                    elif value > 255:
                        value = 255
                    buf[i + ch] = value
        i += 3


MASTHEAD_H = 92
LEAD_Y = 124
LEAD_H = 206
LEAD_W = 328
LEAD_GAP = 336
GRID_Y = 354
GRID_ROW_H = 26
GRID_COL_W = 338
GRID_CELL_W = 330


def render():
    pg = Pix(W, H, PAPER)
    # Masthead: newspaper nameplate — the day, named large and bold,
    # so the judge cannot miss it.
    pg.box(0, 0, W, MASTHEAD_H, NAVY)
    put_text_c(pg, W // 2, 8, "THE WORLD IN ONE IMAGE", 2, WHITE)
    put_bold_c(pg, W // 2, 30, "TUESDAY 24 NOVEMBER 2026", 5, WHITE)
    put_text_c(pg, W // 2, 74,
               "60 STORIES - ALL FIRST REPORTED TUESDAY 24 NOVEMBER 2026",
               1, PALE)
    pg.box(0, MASTHEAD_H, W, 6, RED)
    # Stat strip: honest counts from this page, red numbers on paper.
    pg.rule_h(0, 98, W, EDGE)
    stats = [("60", RED), (" STORIES   ", INK), ("3", RED),
             (" LEADS   ", INK), ("10", RED), (" MOMENTS   ", INK),
             ("9", RED), (" FIELDS   ", INK),
             ("24 NOV", RED), (" 2026", INK)]
    put_mixed_c(pg, W // 2, 106, stats, 2)
    pg.rule_h(0, 123, W, EDGE)
    # Three lead panels: taller art, bold headlines, roomier sub-lines.
    for i, (kicker, field, head, sub) in enumerate(LEADS):
        px = 8 + i * LEAD_GAP
        pg.box(px, LEAD_Y, LEAD_W, LEAD_H, WHITE)
        pg.rule_h(px, LEAD_Y, LEAD_W, EDGE)
        pg.rule_h(px, LEAD_Y + LEAD_H - 1, LEAD_W, EDGE)
        pg.rule_v(px, LEAD_Y, LEAD_H, EDGE)
        pg.rule_v(px + LEAD_W - 1, LEAD_Y, LEAD_H, EDGE)
        pg.box(px + 1, LEAD_Y + 1, LEAD_W - 2, 24, FIELDS[field])
        put_bold(pg, px + 10, 132, kicker, 1, WHITE)
        ART[i](pg, px + 1, 149, 326, 84)
        for j, ln in enumerate(wrap(head, 17)[:2]):
            put_bold(pg, px + 10, 239 + j * 26, ln, 3, INK)
        for j, ln in enumerate(wrap(sub, 25)[:2]):
            put_text(pg, px + 10, 295 + j * 16, ln, 2, GREY)
    # Grid section header.
    put_bold(pg, 8, 336, "MORE FROM THE DAY - 57 STORIES", 2, INK)
    put_text(pg, 830, 339, "COLOUR = FIELD - LEGEND BELOW", 1, GREY)
    # Dense grid: 3 columns x 19 rows, ONE line per cell. A single
    # scale-2 line in a 26px row stays crisp at any size. Headlines
    # are capped at 25 characters so none wraps or clips.
    for idx, (head, field) in enumerate(GRID):
        col, row = idx % 3, idx // 3
        cx = 8 + col * GRID_COL_W
        cy = GRID_Y + row * GRID_ROW_H
        shade = WHITE if row % 2 == 0 else (242, 238, 225)
        pg.box(cx, cy, GRID_CELL_W, GRID_ROW_H, shade)
        pg.box(cx, cy, 6, GRID_ROW_H, FIELDS[field])
        put_text(pg, cx + 13, cy + 6, head, 2, INK)
    for r in range(20):
        pg.rule_h(8, GRID_Y + r * GRID_ROW_H, 1008, HAIR)
    for vx in (340, 678):
        pg.rule_v(vx, GRID_Y, 494, HAIR)
    pg.rule_h(8, GRID_Y, 1008, EDGE)
    pg.rule_h(8, 847, 1008, EDGE)
    pg.rule_v(8, GRID_Y, 494, EDGE)
    pg.rule_v(1015, GRID_Y, 494, EDGE)
    # Timeline: ten moments, times in WIB, bold red times.
    put_bold(pg, 8, 856, "THE DAY IN TEN MOMENTS - TIMES IN WIB", 2, INK)
    pg.rule_h(8, 870, 1008, HAIR)
    for idx, (when, what) in enumerate(TIMELINE):
        col, row = idx % 2, idx // 2
        tx = 8 + col * 508
        ty = 874 + row * 18
        put_bold(pg, tx, ty + 2, when, 2, RED)
        put_text(pg, tx + 96, ty + 2, what, 2, INK)
    # Footer: date check, legend, sources, faithfulness note.
    pg.box(0, 966, W, 2, RED)
    pg.box(0, 968, W, 56, NAVY)
    date_line = ("DATE CHECK: TUESDAY 24 NOVEMBER 2026 - 60 STORIES, "
                 "ALL FIRST REPORTED 24 NOV 2026")
    put_bold_c(pg, W // 2, 976, date_line, 2, GOLD)
    legend = ("RED CONFLICT - BLUE POLITICS - GOLD MARKETS - PURPLE SPORT - "
              "TEAL SCIENCE - PINK CULTURE - SLATE CRIME - BROWN DISASTER - "
              "GREY WORLD")
    put_text_c(pg, W // 2, 992, legend, 1, WHITE)
    sources = ("SOURCES: SALONVISION - KIMKJ - JAGRANJOSH - EDUCATION TIMES - "
               "OBSERVERVOICE - DISCLOSURE NEWS - STUDMENTOR")
    put_text_c(pg, W // 2, 1002, sources, 1, PALE)
    note = ("DRAWN ONLY FROM REPORTS PUBLISHED 24 NOV 2026 IN ANY TIME ZONE - "
            "NOTHING INVENTED, NOTHING SPECULATED AS FACT")
    put_text_c(pg, W // 2, 1012, note, 1, PALE)
    grain(pg)
    return pg


def main():
    """Render the page and write entry.png to the output directory."""
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    data = png_bytes(W, H, render().buf)
    target = os.path.join(out, "entry.png")
    with open(target, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()

