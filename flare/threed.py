"""
flare.threed — translate 3-D geometry into a 2-D Canvas.

Provides a minimal software renderer: perspective projection, model/view
transforms, and wireframe or point-cloud drawing.  No external libraries
required.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Canvas


# ── 3-D vector helpers ────────────────────────────────────────────────────────

Vec3 = tuple[float, float, float]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

def _scale(v: Vec3, s: float) -> Vec3:
    return (v[0]*s, v[1]*s, v[2]*s)

def _dot(a: Vec3, b: Vec3) -> float:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

def _norm(v: Vec3) -> Vec3:
    n = math.sqrt(_dot(v, v))
    return _scale(v, 1.0 / n) if n else (0.0, 0.0, 0.0)

def _mat4_identity() -> list[float]:
    return [
        1,0,0,0,
        0,1,0,0,
        0,0,1,0,
        0,0,0,1,
    ]

def _mat4_mul(a: list[float], b: list[float]) -> list[float]:
    out = [0.0] * 16
    for row in range(4):
        for col in range(4):
            out[row*4+col] = sum(a[row*4+k] * b[k*4+col] for k in range(4))
    return out

def _mat4_apply(m: list[float], x: float, y: float, z: float) -> tuple[float, float, float, float]:
    w_ = m[12]*x + m[13]*y + m[14]*z + m[15]
    return (
        m[0]*x + m[1]*y + m[2]*z + m[3],
        m[4]*x + m[5]*y + m[6]*z + m[7],
        m[8]*x + m[9]*y + m[10]*z + m[11],
        w_ if w_ != 0 else 1.0,
    )


# ── Camera ────────────────────────────────────────────────────────────────────

@dataclass
class Camera:
    """
    A perspective camera.

    Parameters
    ----------
    position : Vec3
        World-space eye position.
    target : Vec3
        World-space look-at point.
    up : Vec3
        Up vector (default Y-up).
    fov_deg : float
        Vertical field of view in degrees.
    near, far : float
        Clip plane distances.
    """

    position: Vec3 = (0.0, 0.0, -5.0)
    target: Vec3   = (0.0, 0.0,  0.0)
    up: Vec3       = (0.0, 1.0,  0.0)
    fov_deg: float = 60.0
    near: float    = 0.1
    far: float     = 1000.0

    def view_matrix(self) -> list[float]:
        """Return the 4×4 column-major view (look-at) matrix."""
        f = _norm(_sub(self.target, self.position))
        r = _norm(_cross(f, _norm(self.up)))
        u = _cross(r, f)
        px, py, pz = self.position
        return [
             r[0],  r[1],  r[2], -_dot(r, self.position),
             u[0],  u[1],  u[2], -_dot(u, self.position),
            -f[0], -f[1], -f[2],  _dot(f, self.position),
             0,     0,     0,     1,
        ]

    def projection_matrix(self, aspect: float) -> list[float]:
        """Return a 4×4 perspective projection matrix."""
        fov_rad = math.radians(self.fov_deg)
        t = math.tan(fov_rad / 2)
        n, f = self.near, self.far
        return [
            1/(aspect*t), 0,      0,                0,
            0,            1/t,    0,                0,
            0,            0,    -(f+n)/(f-n),      -2*f*n/(f-n),
            0,            0,     -1,                0,
        ]


# ── Mesh ─────────────────────────────────────────────────────────────────────

@dataclass
class Mesh:
    """
    A 3-D mesh consisting of vertices and optional edge/face lists.

    Parameters
    ----------
    vertices : list of Vec3
        3-D positions.
    edges : list of (int, int)
        Index pairs for wireframe rendering.
    faces : list of list[int]
        Index triplets (or quads) for face rendering.
    name : str
    """

    vertices: list[Vec3] = field(default_factory=list)
    edges: list[tuple[int, int]] = field(default_factory=list)
    faces: list[list[int]] = field(default_factory=list)
    name: str = ""
    transform: list[float] = field(default_factory=_mat4_identity)

    # ── transforms ──────────────────────────────────────────────────────────

    def translate(self, dx: float, dy: float, dz: float) -> "Mesh":
        """Apply a world-space translation to this mesh. Returns *self*."""
        m = _mat4_identity()
        m[3], m[7], m[11] = dx, dy, dz
        self.transform = _mat4_mul(m, self.transform)
        return self

    def rotate_x(self, deg: float) -> "Mesh":
        """Rotate around the X axis. Returns *self*."""
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        m = _mat4_identity()
        m[5], m[6], m[9], m[10] = c, -s, s, c
        self.transform = _mat4_mul(m, self.transform)
        return self

    def rotate_y(self, deg: float) -> "Mesh":
        """Rotate around the Y axis. Returns *self*."""
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        m = _mat4_identity()
        m[0], m[2], m[8], m[10] = c, s, -s, c
        self.transform = _mat4_mul(m, self.transform)
        return self

    def rotate_z(self, deg: float) -> "Mesh":
        """Rotate around the Z axis. Returns *self*."""
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        m = _mat4_identity()
        m[0], m[1], m[4], m[5] = c, -s, s, c
        self.transform = _mat4_mul(m, self.transform)
        return self

    def scale(self, sx: float, sy: float | None = None, sz: float | None = None) -> "Mesh":
        """Scale the mesh. Returns *self*."""
        if sy is None: sy = sx
        if sz is None: sz = sx
        m = _mat4_identity()
        m[0], m[5], m[10] = sx, sy, sz
        self.transform = _mat4_mul(m, self.transform)
        return self

    def reset_transform(self) -> "Mesh":
        """Reset to identity transform. Returns *self*."""
        self.transform = _mat4_identity()
        return self


# ── built-in mesh factories ───────────────────────────────────────────────────

def make_cube(size: float = 1.0) -> Mesh:
    """Return a unit cube :class:`Mesh` centred at the origin."""
    h = size / 2
    verts: list[Vec3] = [
        (-h,-h,-h),(h,-h,-h),(h,h,-h),(-h,h,-h),
        (-h,-h, h),(h,-h, h),(h,h, h),(-h,h, h),
    ]
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    ]
    return Mesh(vertices=verts, edges=edges, name="cube")


def make_sphere(radius: float = 1.0, lat: int = 8, lon: int = 12) -> Mesh:
    """Return a UV sphere :class:`Mesh`."""
    verts: list[Vec3] = []
    edges: list[tuple[int,int]] = []
    for i in range(lat + 1):
        phi = math.pi * i / lat
        for j in range(lon):
            theta = 2 * math.pi * j / lon
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            verts.append((x, y, z))
    for i in range(lat):
        for j in range(lon):
            a = i * lon + j
            b = i * lon + (j + 1) % lon
            c = (i + 1) * lon + j
            edges.append((a, b))
            edges.append((a, c))
    return Mesh(vertices=verts, edges=edges, name="sphere")


def make_plane(w: float = 2.0, h: float = 2.0, nx: int = 4, ny: int = 4) -> Mesh:
    """Return a flat grid plane Mesh in the XZ plane."""
    verts: list[Vec3] = []
    edges: list[tuple[int,int]] = []
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            x = (ix / nx - 0.5) * w
            z = (iy / ny - 0.5) * h
            verts.append((x, 0.0, z))
    for iy in range(ny + 1):
        for ix in range(nx + 1):
            idx = iy * (nx + 1) + ix
            if ix < nx:
                edges.append((idx, idx + 1))
            if iy < ny:
                edges.append((idx, idx + nx + 1))
    return Mesh(vertices=verts, edges=edges, name="plane")


# ── Scene ─────────────────────────────────────────────────────────────────────

class Scene:
    """
    Container for a :class:`Camera` and a list of :class:`Mesh` objects.

    Use :meth:`render_to` to project and rasterise the scene onto a
    :class:`~flare.core.Canvas`.
    """

    def __init__(self, camera: Camera | None = None) -> None:
        self.camera: Camera = camera or Camera()
        self.meshes: list[Mesh] = []

    def add(self, mesh: Mesh) -> "Scene":
        """Add a mesh to the scene. Returns *self*."""
        self.meshes.append(mesh)
        return self

    def remove(self, mesh: Mesh) -> None:
        """Remove a mesh from the scene."""
        self.meshes.remove(mesh)

    def render_to(
        self,
        canvas: "Canvas",
        *,
        value: float = 1.0,
        draw_points: bool = False,
    ) -> None:
        """
        Project all meshes onto *canvas*.

        Parameters
        ----------
        canvas : Canvas
            Target canvas.
        value : float
            Brightness of drawn pixels.
        draw_points : bool
            Draw vertex dots in addition to edges.
        """
        from .shapes import draw_line

        aspect = canvas.width / max(canvas.height, 1)
        V = self.camera.view_matrix()
        P = self.camera.projection_matrix(aspect)
        VP = _mat4_mul(P, V)

        for mesh in self.meshes:
            MVP = _mat4_mul(VP, mesh.transform)

            projected: list[tuple[float, float, bool]] = []
            for vx, vy, vz in mesh.vertices:
                cx, cy, cz, cw = _mat4_apply(MVP, vx, vy, vz)
                # perspective divide
                if abs(cw) < 1e-6:
                    projected.append((0, 0, False))
                    continue
                nx2, ny2 = cx / cw, cy / cw
                # NDC → canvas pixel
                px = int((nx2 * 0.5 + 0.5) * canvas.width)
                py = int((1.0 - (ny2 * 0.5 + 0.5)) * canvas.height)
                in_front = (cw > 0)
                projected.append((px, py, in_front))

            for i0, i1 in mesh.edges:
                x0, y0, ok0 = projected[i0]
                x1, y1, ok1 = projected[i1]
                if ok0 and ok1:
                    draw_line(canvas, int(x0), int(y0), int(x1), int(y1), value)

            if draw_points:
                for px, py, ok in projected:
                    if ok:
                        canvas.set_pixel(int(px), int(py), value)
