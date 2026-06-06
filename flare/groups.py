"""
flare.groups — shape grouping, translation, and transform pipeline.

A :class:`Group` holds a list of :class:`Shape` objects (or other
groups via nesting). Groups can be translated, scaled, and rotated as
a unit.  Every shape inside renders relative to the group's origin.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Canvas


# ── Transform matrix (2-D affine, column-major 3×3) ─────────────────────────

class Transform:
    """
    A 2-D affine transform stored as a 3×3 matrix.

    Supports chained :meth:`translate`, :meth:`rotate`, :meth:`scale`.
    """

    def __init__(self) -> None:
        self._m = [1.0, 0.0, 0.0,
                   0.0, 1.0, 0.0,
                   0.0, 0.0, 1.0]

    # ── matrix multiply ──────────────────────────────────────────────────────

    def _mul(self, other: list[float]) -> "Transform":
        a, b = self._m, other
        t = Transform()
        t._m = [
            a[0]*b[0] + a[1]*b[3] + a[2]*b[6],
            a[0]*b[1] + a[1]*b[4] + a[2]*b[7],
            a[0]*b[2] + a[1]*b[5] + a[2]*b[8],
            a[3]*b[0] + a[4]*b[3] + a[5]*b[6],
            a[3]*b[1] + a[4]*b[4] + a[5]*b[7],
            a[3]*b[2] + a[4]*b[5] + a[5]*b[8],
            a[6]*b[0] + a[7]*b[3] + a[8]*b[6],
            a[6]*b[1] + a[7]*b[4] + a[8]*b[7],
            a[6]*b[2] + a[7]*b[5] + a[8]*b[8],
        ]
        return t

    def translate(self, dx: float, dy: float) -> "Transform":
        """Return a new Transform with translation applied."""
        mat = [1.0, 0.0, float(dx),
               0.0, 1.0, float(dy),
               0.0, 0.0, 1.0]
        return self._mul(mat)

    def rotate(self, angle_deg: float) -> "Transform":
        """Return a new Transform rotated *angle_deg* degrees (CCW)."""
        r = math.radians(angle_deg)
        c, s = math.cos(r), math.sin(r)
        mat = [c,  -s, 0.0,
               s,   c, 0.0,
               0.0, 0.0, 1.0]
        return self._mul(mat)

    def scale(self, sx: float, sy: float | None = None) -> "Transform":
        """Return a new Transform scaled by sx (and optionally sy)."""
        if sy is None:
            sy = sx
        mat = [float(sx), 0.0,       0.0,
               0.0,       float(sy), 0.0,
               0.0,       0.0,       1.0]
        return self._mul(mat)

    def apply(self, x: float, y: float) -> tuple[float, float]:
        """Apply this transform to point (x, y) → (x′, y′)."""
        m = self._m
        nx = m[0] * x + m[1] * y + m[2]
        ny = m[3] * x + m[4] * y + m[5]
        return nx, ny

    @classmethod
    def identity(cls) -> "Transform":
        """Return the identity transform."""
        return cls()

    def __repr__(self) -> str:
        m = self._m
        return (
            f"Transform([{m[0]:.2f}, {m[1]:.2f}, {m[2]:.2f}] "
            f"[{m[3]:.2f}, {m[4]:.2f}, {m[5]:.2f}])"
        )


# ── Shape wrapper ────────────────────────────────────────────────────────────

@dataclass
class Shape:
    """
    A drawable object: a callable that accepts ``(canvas, transform)``
    and draws itself after applying the combined transform.

    Parameters
    ----------
    draw_fn : callable(canvas, transform)
        The drawing function.  It receives the accumulated :class:`Transform`
        from the group hierarchy so it can warp its pixel coordinates.
    name : str, optional
        Human-readable label for debugging.
    visible : bool
        Whether this shape is drawn.
    """

    draw_fn: Callable[["Canvas", Transform], None]
    name: str = ""
    visible: bool = True
    transform: Transform = field(default_factory=Transform.identity)

    def draw(self, canvas: "Canvas", parent_transform: Transform | None = None) -> None:
        """Draw this shape with its own + parent transform applied."""
        if not self.visible:
            return
        combined = parent_transform or Transform.identity()
        # combine: parent first, then this shape's own
        combined = combined._mul(self.transform._m)  # type: ignore[attr-defined]
        self.draw_fn(canvas, combined)


# ── Group ────────────────────────────────────────────────────────────────────

class Group:
    """
    A named container of :class:`Shape` and/or nested :class:`Group` objects.

    All children render in the coordinate space produced by the group's
    own :class:`Transform`.

    Parameters
    ----------
    name : str
        Label for this group.
    transform : Transform, optional
        Initial transform (identity by default).
    """

    def __init__(
        self,
        name: str = "",
        transform: Transform | None = None,
    ) -> None:
        self.name = name
        self.transform: Transform = transform or Transform.identity()
        self._children: list[Shape | "Group"] = []
        self._canvas: "Canvas | None" = None

    # ── child management ─────────────────────────────────────────────────────

    def add(self, child: "Shape | Group") -> "Group":
        """Add a :class:`Shape` or nested :class:`Group`. Returns *self*."""
        self._children.append(child)
        return self

    def remove(self, child: "Shape | Group") -> None:
        """Remove a child shape or group."""
        self._children.remove(child)

    def clear(self) -> None:
        """Remove all children."""
        self._children.clear()

    def get_child(self, name: str) -> "Shape | Group":
        """Find a child by name (shallow search)."""
        for c in self._children:
            if c.name == name:
                return c
        raise KeyError(f"No child named {name!r}")

    # ── transform helpers ────────────────────────────────────────────────────

    def translate(self, dx: float, dy: float) -> "Group":
        """Apply an additional translation to this group. Returns *self*."""
        self.transform = self.transform.translate(dx, dy)
        return self

    def rotate(self, angle_deg: float) -> "Group":
        """Apply an additional rotation to this group. Returns *self*."""
        self.transform = self.transform.rotate(angle_deg)
        return self

    def scale(self, sx: float, sy: float | None = None) -> "Group":
        """Apply an additional scale to this group. Returns *self*."""
        self.transform = self.transform.scale(sx, sy)
        return self

    def move_to(self, x: float, y: float) -> "Group":
        """Reset the group's translation to (x, y). Returns *self*."""
        m = self.transform._m
        self.transform._m = [
            m[0], m[1], float(x),
            m[3], m[4], float(y),
            m[6], m[7], m[8],
        ]
        return self

    def reset_transform(self) -> "Group":
        """Reset this group's transform to identity. Returns *self*."""
        self.transform = Transform.identity()
        return self

    # ── drawing ──────────────────────────────────────────────────────────────

    def draw(
        self,
        canvas: "Canvas",
        parent_transform: Transform | None = None,
    ) -> None:
        """
        Draw all children onto *canvas*, combining *parent_transform* with
        this group's own transform.
        """
        combined = (parent_transform or Transform.identity())._mul(
            self.transform._m  # type: ignore[attr-defined]
        )
        for child in self._children:
            if isinstance(child, Group):
                child.draw(canvas, combined)
            else:
                child.draw(canvas, combined)

    def __repr__(self) -> str:
        return (
            f"<Group {self.name!r} children={len(self._children)} "
            f"transform={self.transform}>"
        )
