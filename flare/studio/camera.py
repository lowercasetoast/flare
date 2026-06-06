"""
flare.studio.camera — animated camera track for 3-D scenes.
"""
from __future__ import annotations
import math
from typing import Any
from .track import Track
from .easing import Easing


class CameraTrack(Track):
    """
    A specialised Track for animating a 3-D camera.

    Properties interpolated
    -----------------------
    px, py, pz      : camera position (default 0, 0, -5)
    tx, ty, tz      : look-at target  (default 0, 0, 0)
    fov             : field of view in degrees (default 60)
    roll            : roll in degrees (rotates up vector)

    Example::

        cam = studio.add_camera("main_cam")
        cam.keyframe(0,   px=0, py=2, pz=-8, tx=0, ty=0, tz=0, fov=60)
        cam.keyframe(60,  px=4, py=3, pz=-6, fov=50,
                     easing=Easing.EASE_IN_OUT_CUBIC)
        cam.keyframe(120, px=0, py=1, pz=-4, fov=70)
    """

    def __init__(self, name: str = "camera") -> None:
        super().__init__(name, kind="camera")

    def build_camera(self, frame: float) -> Any:
        """Return a :class:`~flare.threed.Camera` configured for *frame*."""
        from ..threed import Camera

        props = self.state_at(frame)
        if not props:
            return Camera()

        pos    = (props.get("px", 0.0), props.get("py", 0.0), props.get("pz", -5.0))
        target = (props.get("tx", 0.0), props.get("ty", 0.0), props.get("tz",  0.0))
        fov    = props.get("fov",  60.0)
        roll   = props.get("roll",  0.0)
        roll_r = math.radians(roll)
        up     = (math.sin(roll_r), math.cos(roll_r), 0.0)

        return Camera(position=pos, target=target, up=up, fov_deg=fov)
