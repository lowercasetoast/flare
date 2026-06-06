"""
flare.studio.objects — draw interpolated 2-D and 3-D objects from track state.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ..core import Canvas


def _col(props: dict, key: str = "color"):
    return props.get(key)


class Obj2D:
    """
    Draws a 2-D shape onto a canvas given an interpolated props dict.

    Supported kinds and their properties
    --------------------------------------
    circle2d   : x, y, radius, filled=False, color
    rect2d     : x, y, w, h, filled=False, color
    line2d     : x0, y0, x1, y1, color
    triangle2d : x0,y0, x1,y1, x2,y2, filled=False, color
    polygon2d  : points [(x,y)...], filled=False, color
    ellipse2d  : x, y, rx, ry, filled=False, color
    bezier2d   : points [(x,y)...], steps=200, color
    text2d     : x, y, text, color
    pixel      : x, y, value=1.0, color
    gradient   : x, y, w, h, color_a, color_b, direction='horizontal'
    """

    @staticmethod
    def draw(canvas: "Canvas", kind: str, props: dict[str, Any]) -> None:
        from .. import shapes
        kind = kind.lower()

        if kind == "circle2d":
            shapes.draw_circle(
                canvas,
                int(props.get("x", 0)), int(props.get("y", 0)),
                int(props.get("radius", props.get("r", 5))),
                filled=bool(props.get("filled", False)),
                color=_col(props),
            )

        elif kind == "rect2d":
            shapes.draw_rect(
                canvas,
                int(props.get("x", 0)), int(props.get("y", 0)),
                int(props.get("w", 10)), int(props.get("h", 10)),
                filled=bool(props.get("filled", False)),
                color=_col(props),
            )

        elif kind == "line2d":
            shapes.draw_line(
                canvas,
                int(props.get("x0", 0)), int(props.get("y0", 0)),
                int(props.get("x1", 10)), int(props.get("y1", 10)),
                color=_col(props),
            )

        elif kind == "triangle2d":
            shapes.draw_triangle(
                canvas,
                int(props.get("x0",0)), int(props.get("y0",0)),
                int(props.get("x1",10)), int(props.get("y1",20)),
                int(props.get("x2",20)), int(props.get("y2",0)),
                filled=bool(props.get("filled", False)),
                color=_col(props),
            )

        elif kind == "ellipse2d":
            shapes.draw_ellipse(
                canvas,
                int(props.get("x",0)), int(props.get("y",0)),
                int(props.get("rx",10)), int(props.get("ry",5)),
                filled=bool(props.get("filled",False)),
                color=_col(props),
            )

        elif kind == "polygon2d":
            pts = props.get("points", [])
            pts = [(int(p[0]), int(p[1])) for p in pts]
            shapes.draw_polygon(canvas, pts,
                                filled=bool(props.get("filled", False)),
                                color=_col(props))

        elif kind == "bezier2d":
            pts = props.get("points", [])
            pts = [(int(p[0]), int(p[1])) for p in pts]
            shapes.draw_bezier(canvas, pts,
                               steps=int(props.get("steps", 200)),
                               color=_col(props))

        elif kind == "text2d":
            shapes.draw_text(
                canvas,
                int(props.get("x", 0)), int(props.get("y", 0)),
                str(props.get("text", "")),
                color=_col(props),
            )

        elif kind == "pixel":
            shapes.draw_pixel(
                canvas,
                int(props.get("x",0)), int(props.get("y",0)),
                float(props.get("value", 1.0)),
                color=_col(props),
            )

        elif kind == "gradient":
            shapes.draw_gradient_rect(
                canvas,
                int(props.get("x",0)), int(props.get("y",0)),
                int(props.get("w",10)), int(props.get("h",10)),
                props.get("color_a"), props.get("color_b"),
                direction=props.get("direction","horizontal"),
            )


class Obj3D:
    """
    Draws a 3-D mesh onto a canvas given an interpolated props dict.

    Props
    -----
    mesh    : flare.threed.Mesh object
    camera  : flare.threed.Camera object
    rx, ry, rz : rotation angles in degrees
    tx, ty, tz : translation
    sx, sy, sz : scale (default 1.0)
    color   : Color
    draw_points : bool
    """

    @staticmethod
    def draw(canvas: "Canvas", props: dict[str, Any]) -> None:
        from .. import threed
        from ..threed import Scene

        mesh   = props.get("mesh")
        camera = props.get("camera", threed.Camera())
        if mesh is None:
            return

        mesh.reset_transform()
        sx = props.get("sx", props.get("scale", 1.0))
        sy = props.get("sy", sx)
        sz = props.get("sz", sx)
        mesh.scale(sx, sy, sz)
        mesh.rotate_x(props.get("rx", 0))
        mesh.rotate_y(props.get("ry", 0))
        mesh.rotate_z(props.get("rz", 0))
        mesh.translate(props.get("tx", 0), props.get("ty", 0), props.get("tz", 0))

        col = props.get("color")
        if col:
            canvas.set_color(col)

        scene = Scene(camera)
        scene.add(mesh)
        scene.render_to(canvas, draw_points=bool(props.get("draw_points", False)))

        if col:
            canvas.set_color(None)
