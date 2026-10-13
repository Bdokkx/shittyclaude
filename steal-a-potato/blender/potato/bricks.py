"""Brick building in the Folk Valley idiom: every piece is one Roblox Part.

  * Plastic parts get Inlet on all six faces; Neon and SmoothPlastic parts are Smooth.
  * ori(rx, ry, rz) is CFrame.fromOrientation in degrees: turn about Y, then X, then Z
    (the order the props file uses), so "heading 30, tilt 8, roll 5" reads naturally.
  * Colours are hex strings ("55b848") or RGB tuples.
"""
import math

import numpy as np

import spsgeo as G
from spsgeo import CF

SMALL = 2.5          # parts whose biggest side is under this cast no shadow


def hexc(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(v) for v in c)


def mix(a, b, t):
    a, b = np.array(hexc(a), float), np.array(hexc(b), float)
    return tuple(int(round(v)) for v in a + (b - a) * t)


def shade(c, k):
    """k < 0 darker, k > 0 lighter (towards white)."""
    c = np.array(hexc(c), float)
    if k < 0:
        return tuple(int(round(v)) for v in c * (1 + k))
    return tuple(int(round(v + (255 - v) * k)) for v in c)


def ori(rx=0.0, ry=0.0, rz=0.0):
    return G.ry(ry) @ G.rx(rx) @ G.rz(rz)


def surfaces_for(material):
    return "inlet" if material == "Plastic" else "smooth"


class Bricks:
    """Adds parts to a spslib Scene in a local frame (`base`, a CF): positions and turns given to
    part() are in that frame."""

    def __init__(self, sc, base=None, anchored=True, collide=False, touch=False, query=False, massless=False):
        self.sc = sc
        self.base = base if base is not None else CF()
        self.flags = dict(anchored=anchored, collide=collide, touch=touch, query=query, massless=massless)
        self.count = 0

    def cf(self, pos, R=None):
        return self.base * CF(np.asarray(pos, float), np.eye(3) if R is None else R)

    def part(self, parent, name, size, pos, R=None, color="ffffff", material="Plastic", transparency=0.0,
             shadow=None, shape="Block", **kw):
        size = tuple(float(v) for v in size)
        if shadow is None:
            shadow = max(size) >= SMALL and transparency < 1.0
        fl = dict(self.flags)
        fl.update(kw)
        self.count += 1
        return self.sc.part(parent, name, size, self.cf(pos, R), hexc(color), shape=shape, material=material,
                            transparency=transparency, shadow=bool(shadow), grid=False,
                            surfaces=surfaces_for(material), **fl)

    def plate(self, parent, name, size, pos, R=None, color="1e1a22", material="SmoothPlastic", **kw):
        """A thin face / text plate: SmoothPlastic, Smooth faces, no shadow."""
        return self.part(parent, name, size, pos, R, color, material=material, shadow=False, **kw)

    def round3(self, parent, name, w, h, d, pos, R=None, cols=("ff8a1f", "f07412", "ffa23f"), names=None,
               cross=0.68, turned=0.88, lid=None):
        """Folk Valley's round: a core block, two crossing slabs (one long in X, one long in Z) and a
        block turned 45 degrees about Y; an optional lid plate (w, h, d of the lid) on top.
        Returns the parts; the first is the core."""
        R = np.eye(3) if R is None else R
        names = names or (name,) * 5
        p = np.asarray(pos, float)
        out = [self.part(parent, names[0], (w * 0.82, h, d * 0.82), p, R, cols[0])]
        out.append(self.part(parent, names[1], (w, h * 0.8, d * cross), p + R @ (0, -h * 0.04, 0), R, cols[1]))
        out.append(self.part(parent, names[2], (w * cross, h * 0.8, d), p + R @ (0, -h * 0.04, 0), R, cols[1]))
        out.append(self.part(parent, names[3], (w * turned * 0.75, h * 0.7, d * turned * 0.75), p, R @ G.ry(45),
                             cols[2]))
        if lid:
            lw, lh, ld = lid
            out.append(self.part(parent, names[4], (lw, lh, ld), p + R @ (0, h / 2 + lh / 2 - 0.02, 0), R, cols[1]))
        return out


def star_geo_points(n, r_out, r_in, phase=90.0):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(phase + i * 180.0 / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts
