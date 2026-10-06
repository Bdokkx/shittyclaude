"""Build the spearfishing islands:  python3 spear/build.py [VoxelIsland ...]
Writes roblox/builders/<Map>Builder.server.lua and build/<Map>.json, prints part counts."""
import collections
import sys
import time

from emit import emit

ISLANDS = {"VoxelIsland": ("voxel_island", (0, 0, 0))}

if __name__ == "__main__":
    names = sys.argv[1:] or list(ISLANDS)
    for name in names:
        mod, origin = ISLANDS[name]
        t = time.time()
        m, preset, water, spawn, cams = __import__(mod).build()
        lua, js, n = emit(m, origin, preset, water, spawn, cams)
        by_stage = collections.Counter(p["stage"] for p in m.parts)
        by_tier = collections.Counter(p["tier"] for p in m.parts)
        print("%s: %d parts (%s) tiers %s  [%.1fs]" % (name, n, dict(by_stage), dict(sorted(by_tier.items())),
                                                      time.time() - t))
        print("   ", lua)
