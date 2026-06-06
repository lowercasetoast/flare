"""
flare.image — convert raster images (PIL/Pillow) or raw pixel data to Canvas.

If Pillow is not installed, :func:`from_pil` will raise :class:`ImportError`
with a helpful message, but the rest of flare continues to work.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Canvas


def from_pil(
    pil_image,
    canvas: "Canvas | None" = None,
    *,
    width: int | None = None,
    height: int | None = None,
    threshold: float = 0.5,
    invert: bool = False,
    dither: bool = False,
    grayscale: bool = False,
) -> "Canvas":
    """
    Convert a Pillow ``Image`` object to a :class:`~flare.core.Canvas`.

    Parameters
    ----------
    pil_image : PIL.Image.Image
        Source image (any mode).
    canvas : Canvas, optional
        Target canvas.  If omitted a new one is created sized to fit the
        image at the requested *width* / *height*.
    width, height : int, optional
        Output canvas pixel dimensions.  Defaults to the image size.
        If only one is given the other is derived preserving aspect ratio.
    threshold : float
        0.0–1.0 brightness cutoff for on/off pixels (braille/block mode).
    invert : bool
        Swap light and dark.
    dither : bool
        Apply simple Floyd–Steinberg dithering before thresholding.
    grayscale : bool
        Store 0.0–1.0 brightness instead of binary on/off.
        Useful with custom ramp charsets.

    Returns
    -------
    Canvas
    """
    try:
        from PIL import Image as _Image
    except ImportError:  # pragma: no cover
        raise ImportError(
            "Pillow is required for image conversion. "
            "Install with: pip install Pillow"
        )

    from .core import Canvas

    img = pil_image.convert("L")  # greyscale

    orig_w, orig_h = img.size
    tgt_w, tgt_h = _resolve_size(orig_w, orig_h, width, height)

    img = img.resize((tgt_w, tgt_h), _Image.LANCZOS)
    pixels = list(img.getdata())  # flat list of 0..255

    if canvas is None:
        canvas = Canvas(tgt_w, tgt_h)

    if dither:
        pixels = _floyd_steinberg(pixels, tgt_w, tgt_h)

    for y in range(tgt_h):
        for x in range(tgt_w):
            v = pixels[y * tgt_w + x] / 255.0
            if invert:
                v = 1.0 - v
            if grayscale:
                canvas.set_pixel(x, y, v)
            else:
                canvas.set_pixel(x, y, 1.0 if v >= threshold else 0.0)

    return canvas


def from_file(
    path: str,
    canvas: "Canvas | None" = None,
    **kwargs,
) -> "Canvas":
    """
    Load an image from *path* on disk and convert it to a Canvas.

    All keyword arguments are forwarded to :func:`from_pil`.
    """
    try:
        from PIL import Image as _Image
    except ImportError:  # pragma: no cover
        raise ImportError(
            "Pillow is required for image loading. "
            "Install with: pip install Pillow"
        )
    img = _Image.open(path)
    return from_pil(img, canvas, **kwargs)


def from_pixels(
    pixels: list[list[float]],
    canvas: "Canvas | None" = None,
    *,
    threshold: float = 0.5,
    grayscale: bool = False,
) -> "Canvas":
    """
    Convert a 2-D list of float values (0.0–1.0) to a Canvas.

    Parameters
    ----------
    pixels : list[list[float]]
        Row-major grid of brightness values.
    canvas : Canvas, optional
        Target canvas; created if omitted.
    threshold : float
        Cutoff for binary on/off.
    grayscale : bool
        Store raw brightness instead of binary.
    """
    from .core import Canvas

    h = len(pixels)
    w = max(len(row) for row in pixels) if h else 0

    if canvas is None:
        canvas = Canvas(w, h)

    for y, row in enumerate(pixels):
        for x, v in enumerate(row):
            pv = max(0.0, min(1.0, float(v)))
            if grayscale:
                canvas.set_pixel(x, y, pv)
            else:
                canvas.set_pixel(x, y, 1.0 if pv >= threshold else 0.0)

    return canvas


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_size(
    orig_w: int, orig_h: int,
    width: int | None, height: int | None,
) -> tuple[int, int]:
    if width is None and height is None:
        return orig_w, orig_h
    if width is not None and height is not None:
        return width, height
    ar = orig_w / max(orig_h, 1)
    if width is not None:
        return width, max(1, round(width / ar))
    return max(1, round(height * ar)), height  # type: ignore[arg-type]


def _floyd_steinberg(
    pixels: list[int], w: int, h: int
) -> list[float]:
    """Apply Floyd–Steinberg dithering in-place (0..255 → 0/255)."""
    buf = [float(p) / 255.0 for p in pixels]
    for y in range(h):
        for x in range(w):
            old = buf[y * w + x]
            new = 1.0 if old >= 0.5 else 0.0
            buf[y * w + x] = new
            err = old - new
            if x + 1 < w:
                buf[y * w + x + 1]           += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    buf[(y+1) * w + x - 1]   += err * 3 / 16
                buf[(y+1) * w + x]            += err * 5 / 16
                if x + 1 < w:
                    buf[(y+1) * w + x + 1]   += err * 1 / 16
    # convert back to 0/255 integers for uniform downstream handling
    return [255 if v >= 0.5 else 0 for v in buf]
