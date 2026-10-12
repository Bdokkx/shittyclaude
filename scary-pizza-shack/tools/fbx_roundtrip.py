"""Re-import an exported FBX in Blender and compare every mesh with the JSON the build
script uses (name, size in Roblox axes, triangle count), plus the axis marker cubes.

    python tools/fbx_roundtrip.py out/ScaryPizzaShack_Batch1.fbx out/map.json FV_Axis
    python tools/fbx_roundtrip.py out/ScaryPizzaShack_Batch2.fbx out/assets.json PSA_Axis
"""
import json
import sys

import bpy
import numpy as np

fbx, src, axis = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "FV_Axis"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
meta = json.load(open(src))["meshes"]
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
missing = [k for k in meta if k not in objs]
extra = [k for k in objs if k not in meta and not k.startswith(axis)]
bad = []
for k, info in meta.items():
    o = objs.get(k)
    if o is None:
        continue
    V = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
    R = np.stack((V[:, 0], V[:, 2], -V[:, 1]), 1)          # Blender (x, y, z) -> Roblox (x, z, -y)
    size = R.max(0) - R.min(0)
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if not np.allclose(size, info["size"], atol=2e-3) or tris != info["tris"]:
        bad.append((k, size.round(3).tolist(), info["size"], tris, info["tris"]))
names = [axis + c for c in "OXYZ"]
mk = {n: np.array((objs[n].matrix_world @ objs[n].data.vertices[0].co)[:]) for n in names}
print("objects", len(objs), "missing", missing, "extra", extra, "bad", len(bad))
for b in bad[:10]:
    print("  ", b)
spacing = [round(float(np.linalg.norm(mk[n] - mk[names[0]])), 3) for n in names[1:]]
print("marker spacing", spacing)
sys.exit(1 if (missing or extra or bad or spacing != [4.0, 4.0, 4.0]) else 0)
