#!/usr/bin/env python3
"""makefun-news-20261119: one-page newspaper front page summing up the
world news of Thursday 19 November 2026, drawn with pure Python stdlib.

No dependencies, no network, no randomness, no clock: the same bytes are
produced on every run. Output: $MAKEFUN_OUTPUT_DIR/entry.png (1024x1024).
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 242, 231)
CARD = (255, 253, 246)
WHITE = (255, 255, 255)
INK = (17, 17, 17)
RED = (185, 28, 28)
BLUE = (29, 78, 216)
LIGHT_BLUE = (191, 219, 254)
GREY = (120, 113, 108)
ORANGE = (234, 88, 12)
GOLD = (250, 204, 21)
GREEN = (22, 163, 74)

# ---------------------------------------------------------------------------
# 5x7 pixel font, hand-typed. Each glyph is 7 rows of 5 cells ("1" = ink).
# Covers A-Z, 0-9 and . , : ' - ! ? ( ) % $ & / and a centred bullet.
# ---------------------------------------------------------------------------
FONT = {
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
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "\u2022": ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def border(self, x, y, w, h, color, thick=2):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def filled_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def circle(self, cx, cy, r, color, thick=2):
        for a in range(360):
            rad = math.radians(a)
            x = int(cx + r * math.cos(rad))
            y = int(cy + r * math.sin(rad))
            self.fill_rect(x, y, thick, thick, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Scanline fill of a triangle.
        ys = sorted([y0, y1, y2])
        for y in range(ys[0], ys[2] + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                     (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= y < max(ay, by) or y == ys[2]:
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            if len(xs) >= 2:
                xa = int(min(xs))
                xb = int(max(xs))
                self.hline(xa, y, xb - xa + 1, color)


def text_width(text, scale):
    text = text.upper()
    return len(text) * 6 * scale - scale if text else 0


def wrap_text(text, max_width, scale):
    words = text.upper().split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_text(cv, x, y, text, scale, color):
    text = text.upper()
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, y, text, scale, color, x0=0, x1=W):
    w = text_width(text, scale)
    draw_text(cv, x0 + (x1 - x0 - w) // 2, y, text, scale, color)


def draw_wrapped(cv, x, y, text, scale, color, max_width, line_gap=4):
    lines = wrap_text(text, max_width, scale)
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * (7 * scale + line_gap), line, scale, color)
    return y + len(lines) * (7 * scale + line_gap)


# ---------------------------------------------------------------------------
# Pictograms (simple shapes inside a 72x72 box at x, y)
# ---------------------------------------------------------------------------
def pic_scales(cv, x, y):
    cv.fill_rect(x, y, 72, 72, WHITE)
    cv.border(x, y, 72, 72, INK, 2)
    cx = x + 36
    cv.vline(cx, y + 8, 44, INK, 3)
    cv.hline(x + 10, y + 10, 52, INK, 3)
    cv.line(x + 10, y + 12, x + 18, y + 30, INK, 2)
    cv.line(x + 62, y + 12, x + 54, y + 30, INK, 2)
    cv.triangle(x + 12, y + 30, x + 24, y + 30, cx - 12, y + 44, BLUE)
    cv.triangle(x + 48, y + 30, x + 60, y + 30, cx + 12, y + 44, BLUE)
    cv.hline(x + 12, y + 30, 13, INK, 2)
    cv.hline(x + 48, y + 30, 13, INK, 2)
    cv.hline(x + 14, y + 52, 44, INK, 3)


def pic_bridge(cv, x, y):
    cv.fill_rect(x, y, 72, 72, WHITE)
    cv.border(x, y, 72, 72, INK, 2)
    cv.fill_rect(x + 8, y + 46, 56, 4, INK)
    cv.fill_rect(x + 14, y + 18, 6, 30, INK)
    cv.fill_rect(x + 52, y + 18, 6, 30, INK)
    # Suspension cable: shallow curve between the two tower tops.
    cable = [(x + 17, y + 20), (x + 24, y + 28), (x + 30, y + 33),
             (x + 36, y + 34), (x + 42, y + 33), (x + 48, y + 28),
             (x + 55, y + 20)]
    for i in range(len(cable) - 1):
        cv.line(cable[i][0], cable[i][1], cable[i + 1][0],
                cable[i + 1][1], RED, 2)
    # Vertical suspenders from cable down to the deck.
    for sx in (x + 24, x + 30, x + 36, x + 42, x + 48):
        cv.vline(sx, y + 30, 16, BLUE, 2)
    cv.hline(x + 8, y + 54, 56, BLUE, 3)


def pic_flame(cv, x, y):
    cv.fill_rect(x, y, 72, 72, WHITE)
    cv.border(x, y, 72, 72, INK, 2)
    cv.triangle(x + 18, y + 58, x + 54, y + 58, x + 36, y + 12, ORANGE)
    cv.triangle(x + 24, y + 58, x + 48, y + 58, x + 36, y + 30, RED)
    cv.filled_circle(x + 36, y + 52, 7, GOLD)


def pic_chart(cv, x, y):
    cv.fill_rect(x, y, 72, 72, WHITE)
    cv.border(x, y, 72, 72, INK, 2)
    cv.vline(x + 12, y + 10, 50, INK, 3)
    cv.hline(x + 12, y + 58, 50, INK, 3)
    pts = [(x + 14, y + 50), (x + 26, y + 42), (x + 36, y + 46),
           (x + 46, y + 30), (x + 58, y + 16)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN, 3)
    cv.line(x + 58, y + 16, x + 52, y + 18, GREEN, 3)
    cv.line(x + 58, y + 16, x + 56, y + 23, GREEN, 3)
    for px, py in pts:
        cv.filled_circle(px, py, 3, RED)


# ---------------------------------------------------------------------------
# Flags for the lead story: USA / China / Russia panels, 304x52 each.
# ---------------------------------------------------------------------------
def flag_usa(cv, x, y, w, h):
    stripe = h // 7
    for i in range(7):
        color = RED if i % 2 == 0 else WHITE
        cv.fill_rect(x, y + i * stripe, w, stripe, color)
    cv.fill_rect(x, y, w // 2, stripe * 4, BLUE)
    for r in range(3):
        for c in range(5):
            cv.filled_circle(x + 14 + c * 28, y + 6 + r * 9, 2, WHITE)


def flag_china(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, RED)
    cv.filled_circle(x + 56, y + h // 2, 10, GOLD)
    for dx, dy in ((100, -14), (118, -4), (118, 12), (100, 18)):
        cv.filled_circle(x + dx, y + h // 2 + dy, 4, GOLD)


def flag_russia(cv, x, y, w, h):
    third = h // 3
    cv.fill_rect(x, y, w, third, WHITE)
    cv.fill_rect(x, y + third, w, third, BLUE)
    cv.fill_rect(x, y + 2 * third, w, h - 2 * third, RED)


# ---------------------------------------------------------------------------
# PNG encoder: RGB 8-bit, zlib level 9, no time chunks, fully deterministic.
# ---------------------------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# Layout: newspaper front page, 1024x1024.
# ---------------------------------------------------------------------------
def draw_page():
    cv = Canvas(W, H, PAPER)

    # Masthead
    draw_text_centered(cv, 30, "THE WORLD", 11, INK)
    cv.fill_rect(32, 118, 960, 6, RED)
    cv.fill_rect(32, 128, 960, 2, INK)
    draw_text_centered(cv, 142, "THURSDAY 19 NOVEMBER 2026", 4, INK)
    draw_text_centered(cv, 178, "WORLD NEWS IN ONE PAGE", 2, RED)
    cv.fill_rect(32, 204, 960, 2, INK)

    # Lead story box
    cv.fill_rect(32, 212, 960, 238, CARD)
    cv.border(32, 212, 960, 238, INK, 3)
    draw_text(cv, 48, 226, "LEAD STORY - APEC SUMMIT, SHENZHEN", 2, RED)
    # Small globe at the right of the kicker line
    cv.circle(936, 236, 16, BLUE, 2)
    cv.vline(936, 222, 28, BLUE, 2)
    cv.hline(922, 236, 28, BLUE, 2)
    draw_text(cv, 48, 252, "TRUMP, XI AND PUTIN", 5, INK)
    draw_text(cv, 48, 293, "MEET IN SHENZHEN", 5, INK)
    draw_wrapped(cv, 48, 338,
                 "FIRST THREE-WAY SUMMIT ON THE APEC SIDELINES - JOINT "
                 "DECLARATION ON NUCLEAR RISKS AND ENERGY",
                 2, INK, 928, line_gap=4)
    flag_usa(cv, 48, 384, 304, 52)
    flag_china(cv, 360, 384, 304, 52)
    flag_russia(cv, 672, 384, 304, 52)
    cv.border(48, 384, 304, 52, INK, 2)
    cv.border(360, 384, 304, 52, INK, 2)
    cv.border(672, 384, 304, 52, INK, 2)

    # 2x2 grid of supporting stories
    stories = [
        (32, 466, RED, "UN COURT RULES MYANMAR COMMITTED GENOCIDE",
         "ICJ: FIRST RULING OF ITS KIND - ROHINGYA CRACKDOWN IN RAKHINE, 2017",
         pic_scales),
        (520, 466, BLUE, "UKRAINE HITS CRIMEA BRIDGE A THIRD TIME",
         "RAIL TRAFFIC HALTED AFTER NEW STRIKE THIS WEEK",
         pic_bridge),
        (32, 670, RED, "IRAN WAR: 'SEE WHAT HAPPENS' AFTER JAN 1",
         "TRUMP PLAYS DOWN DIRTY-BOMB REPORT - HOUTHI MISSILE DAMAGES "
         "RIYADH TOWER",
         pic_flame),
        (520, 670, BLUE, "ANTHROPIC IPO SMASHES RECORDS",
         "$83 A SHARE - ABOUT $81.3 BILLION RAISED",
         pic_chart),
    ]
    for (sx, sy, accent, headline, summary, pic) in stories:
        cv.fill_rect(sx, sy, 472, 188, CARD)
        cv.border(sx, sy, 472, 188, INK, 2)
        cv.fill_rect(sx, sy, 472, 6, accent)
        draw_wrapped(cv, sx + 16, sy + 16, headline, 3, INK, 440, line_gap=4)
        pic(cv, sx + 16, sy + 100)
        draw_wrapped(cv, sx + 104, sy + 102, summary, 2, INK, 352,
                     line_gap=3)

    # Ticker bar
    cv.fill_rect(32, 874, 960, 78, INK)
    draw_wrapped(cv, 48, 886,
                 "GAZA: IDF PUSHES PAST YELLOW LINE \u2022 N. KOREA EXPANDS "
                 "ENRICHMENT, IAEA SAYS \u2022 CYCLONE NEARS INDIA'S EAST "
                 "COAST \u2022 MARKETS: HANG SENG -2.8% \u2022 BRENT $89 "
                 "\u2022 GTA 6 LAUNCHES TODAY",
                 2, WHITE, 928, line_gap=4)

    # Footer
    cv.fill_rect(32, 962, 960, 2, INK)
    draw_text_centered(cv, 972, "SOURCES: REUTERS, AP, DPA, NYT - 19 NOV 2026",
                       2, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_page()
    write_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
