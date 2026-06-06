"""
flare.studio.easing — easing functions for keyframe interpolation.

All functions take t in [0,1] and return a value in [0,1].
"""
from __future__ import annotations
import math


class Easing:
    """
    Collection of easing functions, usable as callables or by name string.

    Usage::

        Easing.EASE_IN_QUAD       # the function itself
        Easing.get("ease_out_cubic")
    """

    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2*t*t if t < 0.5 else -1+(4-2*t)*t

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 + (t-1)**3

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4*t*t*t if t < 0.5 else 1+(t-1)*(2*t-2)**2

    @staticmethod
    def ease_in_quart(t: float) -> float:
        return t * t * t * t

    @staticmethod
    def ease_out_quart(t: float) -> float:
        return 1-(t-1)**4

    @staticmethod
    def ease_in_out_quart(t: float) -> float:
        return 8*t**4 if t < 0.5 else 1-8*(t-1)**4

    @staticmethod
    def ease_in_sine(t: float) -> float:
        return 1 - math.cos(t * math.pi / 2)

    @staticmethod
    def ease_out_sine(t: float) -> float:
        return math.sin(t * math.pi / 2)

    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def ease_in_expo(t: float) -> float:
        return 0.0 if t == 0 else 2 ** (10*t - 10)

    @staticmethod
    def ease_out_expo(t: float) -> float:
        return 1.0 if t == 1 else 1 - 2**(-10*t)

    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        if t == 0: return 0.0
        if t == 1: return 1.0
        return 2**(20*t-10)/2 if t < 0.5 else (2-2**(-20*t+10))/2

    @staticmethod
    def ease_in_back(t: float) -> float:
        c = 1.70158
        return (c+1)*t*t*t - c*t*t

    @staticmethod
    def ease_out_back(t: float) -> float:
        c = 1.70158
        return 1+(c+1)*(t-1)**3+c*(t-1)**2

    @staticmethod
    def ease_in_out_back(t: float) -> float:
        c = 1.70158*1.525
        return ((1+c)*4*t**3-c*2*t**2)/2 if t<0.5 else ((1+c)*(2*t-2)**3+c*(2*t-2)**2+2)/2

    @staticmethod
    def ease_in_elastic(t: float) -> float:
        if t in (0,1): return t
        return -(2**(10*t-10))*math.sin((t*10-10.75)*(2*math.pi)/3)

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        if t in (0,1): return t
        return 2**(-10*t)*math.sin((t*10-0.75)*(2*math.pi)/3)+1

    @staticmethod
    def ease_in_out_elastic(t: float) -> float:
        if t in (0,1): return t
        if t<0.5:
            return -(2**(20*t-10)*math.sin((20*t-11.125)*(2*math.pi)/4.5))/2
        return (2**(-20*t+10)*math.sin((20*t-11.125)*(2*math.pi)/4.5))/2+1

    @staticmethod
    def ease_in_bounce(t: float) -> float:
        return 1 - Easing.ease_out_bounce(1-t)

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n,d=7.5625,2.75
        if t<1/d:   return n*t*t
        elif t<2/d: t-=1.5/d;  return n*t*t+0.75
        elif t<2.5/d: t-=2.25/d; return n*t*t+0.9375
        else:         t-=2.625/d; return n*t*t+0.984375

    @staticmethod
    def ease_in_out_bounce(t: float) -> float:
        return (1-Easing.ease_out_bounce(1-2*t))/2 if t<0.5 else (1+Easing.ease_out_bounce(2*t-1))/2

    @staticmethod
    def step(t: float) -> float:
        """Jump immediately to the end value (no interpolation)."""
        return 0.0 if t < 1.0 else 1.0

    # ── registry ──────────────────────────────────────────────────────────────

    _REGISTRY: dict[str, object] = {}

    @classmethod
    def get(cls, name: str):
        """Look up an easing function by name string (case-insensitive)."""
        if not cls._REGISTRY:
            cls._REGISTRY = {
                k.lower(): getattr(cls, k)
                for k in dir(cls)
                if not k.startswith("_") and callable(getattr(cls, k))
                and k not in ("get", "apply")
            }
        fn = cls._REGISTRY.get(name.lower())
        if fn is None:
            raise KeyError(f"Unknown easing: {name!r}. "
                           f"Available: {list(cls._REGISTRY.keys())}")
        return fn

    @classmethod
    def apply(cls, name_or_fn, t: float) -> float:
        """Apply an easing by name string or callable."""
        if callable(name_or_fn):
            return name_or_fn(t)
        return cls.get(name_or_fn)(t)


# Attach constants for IDE autocomplete
Easing.LINEAR             = Easing.linear
Easing.EASE_IN_QUAD       = Easing.ease_in_quad
Easing.EASE_OUT_QUAD      = Easing.ease_out_quad
Easing.EASE_IN_OUT_QUAD   = Easing.ease_in_out_quad
Easing.EASE_IN_CUBIC      = Easing.ease_in_cubic
Easing.EASE_OUT_CUBIC     = Easing.ease_out_cubic
Easing.EASE_IN_OUT_CUBIC  = Easing.ease_in_out_cubic
Easing.EASE_IN_SINE       = Easing.ease_in_sine
Easing.EASE_OUT_SINE      = Easing.ease_out_sine
Easing.EASE_IN_OUT_SINE   = Easing.ease_in_out_sine
Easing.EASE_IN_BACK       = Easing.ease_in_back
Easing.EASE_OUT_BACK      = Easing.ease_out_back
Easing.EASE_IN_ELASTIC    = Easing.ease_in_elastic
Easing.EASE_OUT_ELASTIC   = Easing.ease_out_elastic
Easing.EASE_IN_BOUNCE     = Easing.ease_in_bounce
Easing.EASE_OUT_BOUNCE    = Easing.ease_out_bounce
Easing.STEP               = Easing.step
