"""
flare.studio.track — Track and Keyframe: the core timeline data model.
"""
from __future__ import annotations
import math
from typing import Any, Callable
from .easing import Easing


class Keyframe:
    """
    A single keyframe at a given *frame* number.

    Parameters
    ----------
    frame : int
        Timeline position (0-based).
    props : dict
        Property values at this keyframe (x, y, radius, color, …).
    easing : callable or str
        Easing applied when interpolating FROM this keyframe to the next.
        Defaults to ``Easing.LINEAR``.
    """

    def __init__(
        self,
        frame: int,
        props: dict[str, Any],
        easing = None,
    ) -> None:
        self.frame  = int(frame)
        self.props  = props
        self.easing = easing or Easing.linear

    def __repr__(self) -> str:
        return f"<Keyframe f={self.frame} props={list(self.props.keys())}>"


def _lerp_value(a, b, t: float):
    """Interpolate between two values. Handles numbers and Colors."""
    try:
        from ..core import Color
        if isinstance(a, Color) and isinstance(b, Color):
            return a.lerp(b, t)
    except ImportError:
        pass
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * t
    # non-numeric: snap at t>=0.5
    return a if t < 0.5 else b


class Track:
    """
    A named animation track holding a sorted list of :class:`Keyframe` objects.

    Supports arbitrary property names. At playback time the Studio asks each
    track for its interpolated state at a given frame, then draws the result.

    Parameters
    ----------
    name : str
        Human-readable label.
    kind : str
        Shape kind — ``'circle2d'``, ``'rect2d'``, ``'line2d'``,
        ``'triangle2d'``, ``'polygon2d'``, ``'text2d'``,
        ``'mesh3d'``, ``'camera'``, ``'custom'``.
    draw_fn : callable(canvas, props), optional
        For ``kind='custom'``, a function that draws the object given the
        interpolated props dict.
    visible : bool
        Whether this track is drawn during playback.
    """

    def __init__(
        self,
        name: str,
        kind: str = "circle2d",
        draw_fn: Callable | None = None,
        visible: bool = True,
    ) -> None:
        self.name    = name
        self.kind    = kind
        self.draw_fn = draw_fn
        self.visible = visible
        self._keys: list[Keyframe] = []

    # ── keyframe management ───────────────────────────────────────────────────

    def keyframe(self, frame: int, easing=None, **props) -> "Track":
        """
        Add or update a keyframe at *frame*.

        All keyword arguments become properties of the keyframe.
        Returns *self* for chaining.

        Example::

            track.keyframe(0,  x=10, y=20, color=Color.RED)
            track.keyframe(30, x=80, y=20, color=Color.BLUE, easing=Easing.EASE_OUT_CUBIC)
        """
        # merge with existing keyframe at same frame if present
        existing = next((k for k in self._keys if k.frame == frame), None)
        if existing:
            existing.props.update(props)
            if easing: existing.easing = easing
        else:
            self._keys.append(Keyframe(frame, dict(props), easing))
            self._keys.sort(key=lambda k: k.frame)
        return self

    def remove_keyframe(self, frame: int) -> None:
        """Remove the keyframe at *frame* (if it exists)."""
        self._keys = [k for k in self._keys if k.frame != frame]

    def clear_keyframes(self) -> None:
        """Remove all keyframes."""
        self._keys.clear()

    @property
    def duration(self) -> int:
        """Frame number of the last keyframe (0 if no keyframes)."""
        return self._keys[-1].frame if self._keys else 0

    # ── interpolation ─────────────────────────────────────────────────────────

    def state_at(self, frame: float) -> dict[str, Any]:
        """
        Return the interpolated property dict at *frame*.

        If frame is before the first keyframe, returns first keyframe props.
        If frame is after the last keyframe, returns last keyframe props.
        Otherwise interpolates between the surrounding keyframes using the
        easing of the left keyframe.
        """
        if not self._keys:
            return {}
        if frame <= self._keys[0].frame:
            return dict(self._keys[0].props)
        if frame >= self._keys[-1].frame:
            return dict(self._keys[-1].props)

        # find surrounding pair
        left = right = None
        for i, k in enumerate(self._keys[:-1]):
            if k.frame <= frame <= self._keys[i+1].frame:
                left, right = k, self._keys[i+1]
                break

        if left is None or right is None:
            return dict(self._keys[-1].props)

        span = right.frame - left.frame
        raw_t = (frame - left.frame) / span if span else 1.0
        t = Easing.apply(left.easing, raw_t)

        # interpolate all shared props
        result: dict[str, Any] = {}
        all_keys = set(left.props) | set(right.props)
        for prop in all_keys:
            a = left.props.get(prop)
            b = right.props.get(prop)
            if a is None:
                result[prop] = b
            elif b is None:
                result[prop] = a
            else:
                result[prop] = _lerp_value(a, b, t)

        return result

    def __repr__(self) -> str:
        return f"<Track {self.name!r} kind={self.kind!r} keys={len(self._keys)}>"
