"""
flare — unicode/braille terminal graphics library.

Quick start::

    import flare
    c = flare.Canvas(120, 60)
    flare.draw_circle(c, 60, 30, 20, filled=True, color=flare.Color.CYAN)
    c.show()

Animation studio::

    from flare.studio import Studio, Easing
    from flare.core import Color

    s = Studio(120, 60, fps=24)
    ball = s.add_track("ball", "circle2d")
    ball.keyframe(0,  x=10, y=30, radius=6, filled=True, color=Color.RED)
    ball.keyframe(48, x=110,y=30, radius=6, filled=True, color=Color.BLUE,
                  easing=Easing.EASE_IN_OUT_BOUNCE)
    s.play()
"""

from .core import Canvas, Color
from .shapes import (
    draw_pixel, draw_line, draw_rect, draw_circle,
    draw_ellipse, draw_triangle, draw_polygon,
    draw_text, draw_bezier, draw_gradient_rect,
)
from .groups    import Group, Shape, Transform
from .image     import from_pil, from_file, from_pixels
from .threed    import Camera, Mesh, Scene, make_cube, make_sphere, make_plane
from .animation import Animation, frames
from . import charsets
from . import studio as studio

__all__ = [
    # canvas + color
    "Canvas", "Color",
    # shapes
    "draw_pixel", "draw_line", "draw_rect", "draw_circle",
    "draw_ellipse", "draw_triangle", "draw_polygon",
    "draw_text", "draw_bezier", "draw_gradient_rect",
    # groups
    "Group", "Shape", "Transform",
    # image
    "from_pil", "from_file", "from_pixels",
    # 3-D
    "Camera", "Mesh", "Scene", "make_cube", "make_sphere", "make_plane",
    # animation
    "Animation", "frames",
    # modules
    "charsets", "studio",
]

__version__ = "0.2.0"
