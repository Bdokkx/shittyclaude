"""What every area module shares: local coordinates along the area (u = studs north of its
south border), a record of what's taken (props and mounds keep out of each other), side
scattering that never enters the running lane, and the area's batcher."""
import math

import numpy as np

from spsgeo import CF
import spsgeo as G

from .. import layout as L
from ..batch import Batcher

SIDE = (26.0, 56.0)          # props live at |x| in here (the lane is |x| < 22)


class Area:
    def __init__(self, k, n, folder, markers, rng):
        self.k, self.n, self.f, self.mk, self.rng = k, n, folder, markers, rng
        self.zs, self.zn = L.area_z(n)
        self.b = Batcher(k, k.sc.folder(folder, "Scenery"), "A%d" % n)
        self.taken = []           # (x, z, r)
        self.tucked = []          # (x, z): mound spots beside props

    def z(self, u):
        return self.zs - u

    def cf(self, x, u, ang=0.0, y=0.0):
        return CF((x, y, self.z(u)), G.ry(ang))

    def take(self, x, u, r):
        self.taken.append((x, self.z(u), r))

    def free(self, x, u, r):
        z = self.z(u)
        return all(math.hypot(x - a, z - b) >= r + c for (a, b, c) in self.taken)

    def tuck(self, x, u):
        self.tucked.append((x, self.z(u)))

    def put(self, group, parts, x, u, ang=0.0, r=2.0, y=0.0):
        self.b.add_parts(group, parts, self.cf(x, u, ang, y))
        self.take(x, u, r)

    def scatter(self, n, r, xs=SIDE, us=(6.0, 214.0), lane_too=0, tries=400):
        """n spots (x, u) on the sides (|x| in xs), plus lane_too in the open middle, each r clear
        of everything taken so far."""
        out = []
        rng = self.rng
        for i in range(n + lane_too):
            for _ in range(tries):
                if i < n:
                    x = rng.uniform(*xs) * (1 if rng.random() < 0.5 else -1)
                else:
                    x = rng.uniform(-18.0, 18.0)
                u = rng.uniform(*us)
                if self.free(x, u, r):
                    out.append((x, u))
                    self.take(x, u, r)
                    break
        return out

    def flush(self):
        return self.b.flush()
