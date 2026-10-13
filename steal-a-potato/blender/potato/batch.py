"""Repeated decoration merged into a few big MeshParts: one per (group, colour, material), split
when a mesh would pass MAX_TRIS. Geometry goes in in world space; the MeshPart sits at its bbox
centre with no rotation, so its own Y is world up (Spin and Sway need their own parts)."""
import numpy as np

import spsgeo as G
from spsgeo import CF

MAX_TRIS = 9000


class Batcher:
    def __init__(self, kit, parent, prefix):
        self.k, self.parent, self.prefix = kit, parent, prefix
        self.groups = {}          # (group, colour, material, transparency) -> [Geo, ...]

    def add(self, group, color, geo, frame=None, material="Plastic", transparency=0.0):
        g = geo if frame is None else geo.xf(_m4(frame))
        key = (group, tuple(int(v) for v in color), material, float(transparency))
        self.groups.setdefault(key, []).append(g)

    def add_parts(self, group, parts, frame):
        """parts = [(suffix, colour, geo) | (suffix, colour, geo, material)] in a prop's own frame."""
        for p in parts:
            mat = p[3] if len(p) > 3 else "Plastic"
            self.add(group, p[1], p[2], frame, material=mat)

    def flush(self):
        out = []
        names = {}
        for (group, color, mat, tr), geos in self.groups.items():
            chunks, cur, tris = [], G.Geo(), 0
            for g in geos:
                t = g.tris()
                if tris and tris + t > MAX_TRIS:
                    chunks.append(cur)
                    cur, tris = G.Geo(), 0
                cur.add(g)
                tris += t
            chunks.append(cur)
            for ch in chunks:
                base = "%s_%s" % (self.prefix, group)
                k = names.get(base, 0) + 1
                names[base] = k
                mesh_name = "%s%d" % (base, k)
                out.append(self.k.mesh(self.parent, group, mesh_name, ch, CF(), color, material=mat,
                                       transparency=tr))
        self.groups = {}
        return out


def _m4(frame):
    """CF or 4x4 -> 4x4."""
    if isinstance(frame, np.ndarray) and frame.shape == (4, 4):
        return frame
    m = np.eye(4)
    m[:3, :3] = frame.R
    m[:3, 3] = frame.p
    return m
