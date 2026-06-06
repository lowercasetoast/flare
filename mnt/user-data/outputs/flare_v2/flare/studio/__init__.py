"""
flare.studio — keyframe animation studio sublibrary.

A Moon Animator-style timeline system with:
- Keyframes + easing curves
- 2-D and 3-D object tracks
- Camera animation tracks
- Group/layer management
- Playback engine

Quick start::

    from flare.studio import Studio, Track, Keyframe
    from flare.core import Canvas, Color

    studio = Studio(canvas_width=120, canvas_height=60, fps=24)

    track = studio.add_track("ball", kind="circle2d")
    track.keyframe(0,   x=20, y=30, radius=8,  color=Color.RED)
    track.keyframe(48,  x=100,y=30, radius=12, color=Color.BLUE)
    track.keyframe(96,  x=60, y=10, radius=8,  color=Color.GREEN)

    studio.play()
"""

from .studio   import Studio
from .track    import Track, Keyframe
from .easing   import Easing
from .objects  import Obj2D, Obj3D
from .camera   import CameraTrack

__all__ = ["Studio", "Track", "Keyframe", "Easing", "Obj2D", "Obj3D", "CameraTrack"]
