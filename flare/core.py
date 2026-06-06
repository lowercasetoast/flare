"""
flare.core — canvas, pixel buffer, and rendering engine (with color support)
"""

from __future__ import annotations
import math
from typing import Callable

# ── ANSI color support ────────────────────────────────────────────────────────

class Color:
    """
    An RGB color. All values 0-255.

    Usage::

        Color(255, 0, 0)          # red
        Color.from_hex("#ff0000") # red from hex
        Color.RED                 # built-in constant
    """
    __slots__ = ("r", "g", "b")

    def __init__(self, r: int, g: int, b: int) -> None:
        self.r = max(0, min(255, int(r)))
        self.g = max(0, min(255, int(g)))
        self.b = max(0, min(255, int(b)))

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        h = hex_str.lstrip("#")
        return cls(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> "Color":
        """h=0-360, s=0-1, v=0-1"""
        h = h % 360
        c = v * s
        x = c * (1 - abs((h/60) % 2 - 1))
        m = v - c
        if   h < 60:  r,g,b = c,x,0
        elif h < 120: r,g,b = x,c,0
        elif h < 180: r,g,b = 0,c,x
        elif h < 240: r,g,b = 0,x,c
        elif h < 300: r,g,b = x,0,c
        else:         r,g,b = c,0,x
        return cls(int((r+m)*255), int((g+m)*255), int((b+m)*255))

    def lerp(self, other: "Color", t: float) -> "Color":
        """Linearly interpolate between this color and other (t=0..1)."""
        t = max(0.0, min(1.0, t))
        return Color(
            int(self.r + (other.r - self.r) * t),
            int(self.g + (other.g - self.g) * t),
            int(self.b + (other.b - self.b) * t),
        )

    def ansi_fg(self) -> str:
        return f"\033[38;2;{self.r};{self.g};{self.b}m"

    def ansi_bg(self) -> str:
        return f"\033[48;2;{self.r};{self.g};{self.b}m"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Color) and self.r==other.r and self.g==other.g and self.b==other.b

    def __repr__(self) -> str:
        return f"Color({self.r},{self.g},{self.b})"

    # ── built-in colors ──────────────────────────────────────────────────────
    RED     : "Color"
    GREEN   : "Color"
    BLUE    : "Color"
    WHITE   : "Color"
    BLACK   : "Color"
    YELLOW  : "Color"
    CYAN    : "Color"
    MAGENTA : "Color"
    ORANGE  : "Color"
    PINK    : "Color"

Color.RED     = Color(255,  60,  60)
Color.GREEN   = Color( 60, 220,  60)
Color.BLUE    = Color( 60, 120, 255)
Color.WHITE   = Color(255, 255, 255)
Color.BLACK   = Color(  0,   0,   0)
Color.YELLOW  = Color(255, 230,  50)
Color.CYAN    = Color( 50, 230, 230)
Color.MAGENTA = Color(230,  50, 230)
Color.ORANGE  = Color(255, 140,   0)
Color.PINK    = Color(255, 105, 180)

RESET = "\033[0m"

# ── Braille lookup ────────────────────────────────────────────────────────────

_BRAILLE_DOT = [
    [0x01, 0x08],
    [0x02, 0x10],
    [0x04, 0x20],
    [0x40, 0x80],
]
_BRAILLE_BASE = 0x2800
_BLOCK_CHARS  = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"


class Canvas:
    """
    A pixel buffer that renders to a string using a chosen charset.
    Supports per-pixel color via ANSI true-color escape codes.

    Parameters
    ----------
    width, height : int
        Logical pixel dimensions.
    charset : str
        ``'braille'`` (default), ``'block'``, or a custom ramp string.
    color : bool
        Enable ANSI color output (default True).
    bg : Color, optional
        Background color applied to empty cells.
    """

    def __init__(
        self,
        width: int,
        height: int,
        charset: str = "braille",
        color: bool = True,
        bg: "Color | None" = None,
    ) -> None:
        self.width   = width
        self.height  = height
        self.charset = charset
        self.color   = color
        self.bg      = bg

        # brightness buffer 0.0-1.0
        self._buf: list[list[float]] = [
            [0.0] * width for _ in range(height)
        ]
        # color buffer — None means "use current draw color"
        self._col: list[list["Color | None"]] = [
            [None] * width for _ in range(height)
        ]
        self._groups: dict[str, object] = {}
        self._draw_color: "Color | None" = Color.WHITE

    # ── draw color ────────────────────────────────────────────────────────────

    def set_color(self, color: "Color | None") -> None:
        """Set the active drawing color for subsequent set_pixel calls."""
        self._draw_color = color

    # ── pixel ops ─────────────────────────────────────────────────────────────

    def set_pixel(
        self,
        x: int, y: int,
        value: float = 1.0,
        color: "Color | None" = None,
    ) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self._buf[y][x] = max(0.0, min(1.0, value))
            self._col[y][x] = color if color is not None else self._draw_color

    def get_pixel(self, x: int, y: int) -> float:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._buf[y][x]
        return 0.0

    def get_pixel_color(self, x: int, y: int) -> "Color | None":
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._col[y][x]
        return None

    def clear(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self._buf[y][x] = 0.0
                self._col[y][x] = None

    # ── rendering ─────────────────────────────────────────────────────────────

    def render(self) -> str:
        if self.charset == "braille":
            return self._render_braille()
        if self.charset == "block":
            return self._render_block()
        return self._render_ramp()

    def _dominant_color(self, pixels: list[tuple[int,int]]) -> "Color | None":
        """Return the most common color among a set of (x,y) pixels."""
        colors = [self._col[y][x] for x,y in pixels if self._col[y][x] is not None]
        if not colors:
            return None
        # simple majority: first non-None
        return colors[0]

    def _render_braille(self) -> str:
        cell_h, cell_w = 4, 2
        rows_c = math.ceil(self.height / cell_h)
        cols_c = math.ceil(self.width  / cell_w)
        lines: list[str] = []
        for cy in range(rows_c):
            row_chars: list[str] = []
            prev_col: "Color | None" = None
            for cx in range(cols_c):
                bits = 0
                on_pixels: list[tuple[int,int]] = []
                for dy in range(cell_h):
                    for dx in range(cell_w):
                        px, py = cx*cell_w+dx, cy*cell_h+dy
                        if self.get_pixel(px, py) >= 0.5:
                            bits |= _BRAILLE_DOT[dy][dx]
                            on_pixels.append((px, py))
                ch = chr(_BRAILLE_BASE | bits)
                if self.color and on_pixels:
                    col = self._dominant_color(on_pixels)
                    if col and col != prev_col:
                        row_chars.append(col.ansi_fg())
                        prev_col = col
                    elif not col and prev_col:
                        row_chars.append(RESET)
                        prev_col = None
                elif self.color and not on_pixels and prev_col:
                    row_chars.append(RESET)
                    prev_col = None
                row_chars.append(ch)
            if self.color and prev_col:
                row_chars.append(RESET)
            lines.append("".join(row_chars))
        return "\n".join(lines)

    def _render_block(self) -> str:
        rows_c = math.ceil(self.height / 2)
        cols_c = math.ceil(self.width  / 2)
        lines: list[str] = []
        for cy in range(rows_c):
            row_chars: list[str] = []
            prev_col: "Color | None" = None
            for cx in range(cols_c):
                idx = 0
                on_pixels: list[tuple[int,int]] = []
                px0, py0 = cx*2, cy*2
                if self.get_pixel(px0,   py0)   >= 0.5: idx |= 1; on_pixels.append((px0,   py0))
                if self.get_pixel(px0+1, py0)   >= 0.5: idx |= 2; on_pixels.append((px0+1, py0))
                if self.get_pixel(px0,   py0+1) >= 0.5: idx |= 4; on_pixels.append((px0,   py0+1))
                if self.get_pixel(px0+1, py0+1) >= 0.5: idx |= 8; on_pixels.append((px0+1, py0+1))
                ch = _BLOCK_CHARS[idx]
                if self.color and on_pixels:
                    col = self._dominant_color(on_pixels)
                    if col and col != prev_col:
                        row_chars.append(col.ansi_fg())
                        prev_col = col
                elif self.color and prev_col:
                    row_chars.append(RESET)
                    prev_col = None
                row_chars.append(ch)
            if self.color and prev_col:
                row_chars.append(RESET)
            lines.append("".join(row_chars))
        return "\n".join(lines)

    def _render_ramp(self) -> str:
        ramp = self.charset
        n    = len(ramp) - 1
        lines: list[str] = []
        for y in range(self.height):
            row_chars: list[str] = []
            prev_col: "Color | None" = None
            for x in range(self.width):
                v   = self._buf[y][x]
                ch  = ramp[round(v * n)]
                col = self._col[y][x]
                if self.color:
                    if col and col != prev_col:
                        row_chars.append(col.ansi_fg())
                        prev_col = col
                    elif not col and prev_col:
                        row_chars.append(RESET)
                        prev_col = None
                row_chars.append(ch)
            if self.color and prev_col:
                row_chars.append(RESET)
            lines.append("".join(row_chars))
        return "\n".join(lines)

    # ── display ───────────────────────────────────────────────────────────────

    def show(self) -> None:
        print(self.render())

    # ── group management ──────────────────────────────────────────────────────

    def add_group(self, name: str, group: object) -> None:
        self._groups[name] = group
        group._canvas = self  # type: ignore

    def get_group(self, name: str) -> object:
        return self._groups[name]

    def draw_group(self, name: str) -> None:
        self._groups[name].draw(self)  # type: ignore

    def draw_all(self) -> None:
        for g in self._groups.values():
            g.draw(self)  # type: ignore

    def __repr__(self) -> str:
        return f"<Canvas {self.width}×{self.height} charset={self.charset!r}>"
