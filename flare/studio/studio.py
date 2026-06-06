"""
flare.studio.studio — the main Studio class: timeline, playback, export.
"""
from __future__ import annotations
import math
import sys
import time
import os
from typing import Callable, Any, TYPE_CHECKING

from .track   import Track
from .camera  import CameraTrack
from .objects import Obj2D, Obj3D
from .easing  import Easing

if TYPE_CHECKING:
    from ..core import Canvas, Color


class Layer:
    """
    A named layer that holds multiple tracks and has its own visibility/opacity.

    Parameters
    ----------
    name : str
    visible : bool
    """
    def __init__(self, name: str, visible: bool = True) -> None:
        self.name    = name
        self.visible = visible
        self.tracks: list[Track] = []

    def add(self, track: Track) -> Track:
        self.tracks.append(track)
        return track

    def __repr__(self) -> str:
        return f"<Layer {self.name!r} tracks={len(self.tracks)}>"


class Studio:
    """
    The top-level animation studio.

    Think Moon Animator: you have a timeline of frames, tracks (objects),
    layers, a camera, and a playback engine.

    Parameters
    ----------
    canvas_width, canvas_height : int
        Pixel dimensions of the canvas.
    fps : float
        Frames per second for playback (default 24).
    charset : str
        Canvas charset (default ``'braille'``).
    color : bool
        Enable ANSI color (default True).
    loop : bool
        Loop playback (default True).

    Example::

        from flare.studio import Studio, Easing
        from flare.core import Color

        s = Studio(120, 60, fps=24)

        ball = s.add_track("ball", "circle2d")
        ball.keyframe(0,  x=10, y=30, radius=6, filled=True, color=Color.RED)
        ball.keyframe(48, x=110,y=30, radius=6, filled=True, color=Color.BLUE,
                      easing=Easing.EASE_IN_OUT_BOUNCE)

        s.play()
    """

    def __init__(
        self,
        canvas_width:  int   = 120,
        canvas_height: int   = 60,
        fps:           float = 24.0,
        charset:       str   = "braille",
        color:         bool  = True,
        loop:          bool  = True,
        bg: "Color | None"   = None,
    ) -> None:
        from ..core import Canvas
        self.fps    = fps
        self.loop   = loop
        self.canvas = Canvas(canvas_width, canvas_height, charset=charset,
                             color=color, bg=bg)
        self._layers: list[Layer]       = []
        self._cameras: list[CameraTrack] = []
        self._active_camera: str | None  = None
        # flat track index for quick lookup
        self._track_index: dict[str, Track] = {}
        # pre/post hooks
        self._pre_frame:  Callable | None = None
        self._post_frame: Callable | None = None

    # ── duration ──────────────────────────────────────────────────────────────

    @property
    def total_frames(self) -> int:
        """The last keyframe across all tracks."""
        mx = 0
        for layer in self._layers:
            for t in layer.tracks:
                mx = max(mx, t.duration)
        for c in self._cameras:
            mx = max(mx, c.duration)
        return max(mx, 1)

    # ── track / layer management ──────────────────────────────────────────────

    def add_layer(self, name: str) -> Layer:
        """Create and return a new layer."""
        layer = Layer(name)
        self._layers.append(layer)
        return layer

    def _ensure_default_layer(self) -> Layer:
        if not self._layers:
            self._layers.append(Layer("default"))
        return self._layers[0]

    def add_track(
        self,
        name: str,
        kind: str = "circle2d",
        layer: str | None = None,
        draw_fn: Callable | None = None,
    ) -> Track:
        """
        Create a Track and add it to a layer.

        Parameters
        ----------
        name : str
            Unique name for the track.
        kind : str
            Shape kind (see :class:`~flare.studio.objects.Obj2D`).
        layer : str, optional
            Layer name. Creates/uses 'default' layer if omitted.
        draw_fn : callable, optional
            Custom draw function for ``kind='custom'``.

        Returns
        -------
        Track
        """
        track = Track(name, kind=kind, draw_fn=draw_fn)
        if layer:
            target = next((l for l in self._layers if l.name == layer), None)
            if target is None:
                target = self.add_layer(layer)
        else:
            target = self._ensure_default_layer()
        target.add(track)
        self._track_index[name] = track
        return track

    def add_camera(self, name: str = "camera") -> CameraTrack:
        """
        Create and return an animated :class:`~flare.studio.camera.CameraTrack`.

        The first camera added is automatically set as active.
        """
        cam = CameraTrack(name)
        self._cameras.append(cam)
        self._track_index[name] = cam
        if self._active_camera is None:
            self._active_camera = name
        return cam

    def set_active_camera(self, name: str) -> None:
        """Set which camera track to use for 3-D rendering."""
        self._active_camera = name

    def get_track(self, name: str) -> Track:
        """Retrieve a track by name."""
        return self._track_index[name]

    def remove_track(self, name: str) -> None:
        """Remove a track by name."""
        track = self._track_index.pop(name, None)
        for layer in self._layers:
            if track in layer.tracks:
                layer.tracks.remove(track)

    # ── hooks ─────────────────────────────────────────────────────────────────

    def on_pre_frame(self, fn: Callable[["Canvas", int, float], None]) -> None:
        """
        Register a callback called before each frame is drawn.

        Signature: ``fn(canvas, frame_index, elapsed_seconds)``
        """
        self._pre_frame = fn

    def on_post_frame(self, fn: Callable[["Canvas", int, float], None]) -> None:
        """
        Register a callback called after all tracks are drawn each frame.

        Signature: ``fn(canvas, frame_index, elapsed_seconds)``
        """
        self._post_frame = fn

    # ── frame rendering ───────────────────────────────────────────────────────

    def render_frame(self, frame: float) -> str:
        """
        Render a single frame and return it as a string.

        Parameters
        ----------
        frame : float
            Timeline position (can be fractional for sub-frame accuracy).
        """
        c = self.canvas
        c.clear()

        elapsed = frame / max(self.fps, 1e-6)

        if self._pre_frame:
            self._pre_frame(c, int(frame), elapsed)

        # get active camera for 3-D tracks
        active_cam = None
        if self._active_camera:
            cam_track = self._track_index.get(self._active_camera)
            if isinstance(cam_track, CameraTrack):
                active_cam = cam_track.build_camera(frame)

        for layer in self._layers:
            if not layer.visible:
                continue
            for track in layer.tracks:
                if not track.visible:
                    continue
                props = track.state_at(frame)

                if track.kind == "custom" and track.draw_fn:
                    track.draw_fn(c, props)
                elif track.kind in ("mesh3d",):
                    if active_cam:
                        props["camera"] = active_cam
                    Obj3D.draw(c, props)
                elif track.kind == "camera":
                    pass  # handled above
                else:
                    Obj2D.draw(c, track.kind, props)

        if self._post_frame:
            self._post_frame(c, int(frame), elapsed)

        return c.render()

    # ── playback ──────────────────────────────────────────────────────────────

    def play(
        self,
        start: int = 0,
        end: int | None = None,
        loop: bool | None = None,
        clear_mode: str = "inline",
    ) -> None:
        """
        Play the animation in the terminal.

        Parameters
        ----------
        start : int
            Start frame (default 0).
        end : int, optional
            End frame (default: last keyframe).
        loop : bool, optional
            Override the studio's loop setting.
        clear_mode : str
            ``'inline'`` (cursor-up, less flicker) or ``'full'`` (cls).
        """
        should_loop = loop if loop is not None else self.loop
        end_frame   = end if end is not None else self.total_frames
        interval    = 1.0 / max(self.fps, 0.1)
        prev_lines  = 0
        frame       = float(start)

        print(f"flare.studio — {int(self.fps)} fps — Ctrl+C to stop\n")

        def _clear(n: int) -> None:
            for _ in range(n):
                sys.stdout.write("\033[1A\033[2K")
            sys.stdout.flush()

        try:
            while True:
                t0      = time.monotonic()
                rendered = self.render_frame(frame)
                lines    = rendered.split("\n")
                MAX      = max(prev_lines, len(lines))

                if prev_lines:
                    _clear(prev_lines)

                # pad to MAX so we always overwrite previous content
                while len(lines) < MAX:
                    lines.append("")

                sys.stdout.write("\n".join(lines) + "\n")
                sys.stdout.flush()
                prev_lines = len(lines)

                frame += 1
                if frame > end_frame:
                    if should_loop:
                        frame = float(start)
                    else:
                        break

                spent = time.monotonic() - t0
                wait  = interval - spent
                if wait > 0:
                    time.sleep(wait)

        except KeyboardInterrupt:
            print("\nStopped.")

    def export_frames(
        self,
        start: int = 0,
        end: int | None = None,
    ) -> list[str]:
        """
        Render all frames to a list of strings without displaying them.

        Parameters
        ----------
        start, end : int
            Frame range (inclusive).

        Returns
        -------
        list of str
        """
        end_frame = end if end is not None else self.total_frames
        return [self.render_frame(f) for f in range(start, end_frame + 1)]

    def export_gif_frames(
        self,
        path_template: str = "frame_{:04d}.txt",
        start: int = 0,
        end: int | None = None,
    ) -> None:
        """
        Write each frame to a separate text file.

        Parameters
        ----------
        path_template : str
            Python format string receiving the frame index.
        """
        for i, frame_str in enumerate(self.export_frames(start, end)):
            with open(path_template.format(i), "w", encoding="utf-8") as f:
                f.write(frame_str)

    # ── timeline info ─────────────────────────────────────────────────────────

    def info(self) -> str:
        """Return a human-readable summary of the studio state."""
        lines = [
            f"Studio  {self.canvas.width}×{self.canvas.height}px  "
            f"{self.fps}fps  {self.total_frames} frames",
            f"Layers  ({len(self._layers)}):",
        ]
        for layer in self._layers:
            lines.append(f"  [{'+' if layer.visible else '-'}] {layer.name}")
            for t in layer.tracks:
                lines.append(
                    f"      {'▶' if t.visible else '○'} {t.name!r:20s} "
                    f"kind={t.kind!r:12s} keys={len(t._keys)}"
                )
        if self._cameras:
            lines.append(f"Cameras ({len(self._cameras)}):")
            for cam in self._cameras:
                active = " ◀ active" if cam.name == self._active_camera else ""
                lines.append(f"  {cam.name!r} keys={len(cam._keys)}{active}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (f"<Studio {self.canvas.width}×{self.canvas.height} "
                f"fps={self.fps} layers={len(self._layers)}>")
