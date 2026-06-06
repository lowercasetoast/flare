"""
flare.animation — simple frame-based terminal animation utilities.
"""

from __future__ import annotations
import time
import sys
import os
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Canvas


def _clear_terminal() -> None:
    """Clear the terminal (cross-platform)."""
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[H\033[2J", end="", flush=True)


def _move_cursor_up(n: int) -> None:
    """Move the cursor up n lines without clearing."""
    sys.stdout.write(f"\033[{n}A")
    sys.stdout.flush()


class Animation:
    """
    Run a render callback repeatedly to produce a terminal animation.

    Parameters
    ----------
    canvas : Canvas
        The canvas to render each frame.
    fps : float
        Target frames per second.
    clear_mode : str
        ``'full'`` – clear entire terminal between frames (default).
        ``'inline'`` – move cursor up instead (flicker-free for fixed-size output).
    """

    def __init__(
        self,
        canvas: "Canvas",
        fps: float = 15.0,
        clear_mode: str = "full",
    ) -> None:
        self.canvas = canvas
        self.fps = fps
        self.clear_mode = clear_mode
        self._running = False
        self._frame = 0
        self._last_lines = 0

    def play(
        self,
        update_fn: Callable[["Canvas", int, float], None],
        duration: float | None = None,
        loop: bool = False,
    ) -> None:
        """
        Start the animation loop.

        Parameters
        ----------
        update_fn : callable(canvas, frame, elapsed)
            Called each frame with the canvas, frame index, and elapsed
            seconds. Should update the canvas (clear + redraw).
        duration : float, optional
            Stop after this many seconds (None = run until Ctrl-C).
        loop : bool
            If *duration* is set, restart after it elapses.
        """
        interval = 1.0 / max(self.fps, 0.1)
        self._running = True
        self._frame = 0
        start = time.monotonic()

        try:
            while self._running:
                t0 = time.monotonic()
                elapsed = t0 - start

                if duration is not None and elapsed >= duration:
                    if loop:
                        start = t0
                        self._frame = 0
                        elapsed = 0.0
                    else:
                        break

                self.canvas.clear()
                update_fn(self.canvas, self._frame, elapsed)
                rendered = self.canvas.render()
                lines = rendered.count("\n") + 1

                if self.clear_mode == "inline" and self._last_lines:
                    _move_cursor_up(self._last_lines)
                else:
                    _clear_terminal()

                sys.stdout.write(rendered + "\n")
                sys.stdout.flush()
                self._last_lines = lines
                self._frame += 1

                sleep = interval - (time.monotonic() - t0)
                if sleep > 0:
                    time.sleep(sleep)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False

    def stop(self) -> None:
        """Signal the animation loop to stop."""
        self._running = False


def frames(
    canvas: "Canvas",
    update_fn: Callable[["Canvas", int], None],
    count: int,
) -> list[str]:
    """
    Render *count* frames and return them as a list of strings.

    Parameters
    ----------
    canvas : Canvas
        Canvas used for each frame.
    update_fn : callable(canvas, frame_index)
        Updates the canvas for each frame.
    count : int
        Number of frames to render.

    Returns
    -------
    list of str
    """
    result = []
    for i in range(count):
        canvas.clear()
        update_fn(canvas, i)
        result.append(canvas.render())
    return result
