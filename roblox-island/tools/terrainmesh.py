"""Turns the island's column height field into one deformed, stud-textured terrain mesh
in the same style as the reef rocks (and the reference shots):

    columns -> voxel remesh (fuse) -> push cliff faces in/out with noise (tops stay flat,
    so paths and props still line up) -> decimate into facets -> colour each face
    (grass top, yellow sand band + grass lip under every edge, blue rock cliffs,
    sand beaches, dirt under the cobbles) -> split into 64-stud chunks per colour.

Import inside Blender only.
"""
import math

import bmesh
import bpy
from mathutils import Vector, noise

from noise import fbm as _fbm

import rockmesh
from island import greedy

CHUNK = 64          # studs per chunk side
BOTTOM = -3         # mesh goes a little below the water line; shallows stay as parts
MATS = {"Lava": "lava", "Ice": "ice", "Rock": "rock", "Band": "sand", "Grass": "grass", "GrassDark": "grass_dark", "Beach": "sand_light",
        "Dirt": "path_dirt", "Stone": "moss"}


def _cell_lookup(m):
    N, C = m["N"], m["cell"]
    cells = {(i, j): (top, kind, surf) for i, j, top, kind, surf in m["mesh_cells"]}

    def at(x, z):
        """Column under Roblox position (x, z)."""
        return cells.get((int(math.floor(x / C + N / 2)), int(math.floor(z / C + N / 2))))
    return cells, at


def build_island_terrain(m, coll, tex_dir, voxel=1.25, amp=1.15, bulge=1.3, ratio=0.28, name=None):
    name = name or m.get("map", "IslandTerrain")
    mats = dict(MATS, **m.get("mats", {}))
    N, C = m["N"], m["cell"]
    cells, at = _cell_lookup(m)

    # 1. solid from merged columns
    grid = {(i, j): top for (i, j), (top, kind, surf) in cells.items()}
    bm = bmesh.new()
    for i0, j0, i1, j1, top in greedy(grid, N, N):
        x0, x1 = (i0 - N / 2) * C, (i1 + 1 - N / 2) * C
        z0, z1 = (j0 - N / 2) * C, (j1 + 1 - N / 2) * C
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res["verts"]:
            lx, ly, lz = v.co
            rx = (x0 + x1) / 2 + lx * (x1 - x0)
            ry = (BOTTOM + top) / 2 + lz * (top - BOTTOM)
            rz = (z0 + z1) / 2 - ly * (z1 - z0)
            v.co = (rx, -rz, ry)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    rem = ob.modifiers.new("fuse", "REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = voxel
    rockmesh._apply_all(ob)

    # 2. deform: wobble everything sideways (cliff edges become ragged, tops stay at their
    #    height) and bulge the cliff faces out/in along their normals
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    f = 1 / 7.0
    def snap(x, y, z):
        """Voxel remesh rounds flat tops by up to ~0.7 studs; put them back at the exact column
        height so the visible ground matches the invisible collision (and props sit right)."""
        best = None
        for ddx, ddy in ((0, 0), (C * 0.5, 0), (-C * 0.5, 0), (0, C * 0.5), (0, -C * 0.5)):
            col = at(x + ddx, -(y + ddy))
            if col and abs(col[0] - z) < 0.95 and (best is None or abs(col[0] - z) < abs(best - z)):
                best = col[0]
        return best if best is not None else z

    for v in bm.verts:
        x, y, z = v.co
        z = snap(x, y, z)
        p = Vector((x * f, y * f, z * f * 0.7))
        dx = noise.noise(p) * amp
        dy = noise.noise(p + Vector((31.7, 17.3, 5.1))) * amp
        nz = v.normal.z
        side = max(0.0, 1 - abs(nz) * 1.6)
        b = noise.noise(p * 1.9 + Vector((7.3, 3.1, 11.9))) * bulge * side
        v.co = (x + dx + v.normal.x * b, y + dy + v.normal.y * b, z)
    bm.to_mesh(ob.data)
    bm.free()

    # 3. facets
    dec = ob.modifiers.new("facets", "DECIMATE")
    dec.decimate_type = "COLLAPSE"
    dec.ratio = ratio
    dec.use_collapse_triangulate = True
    rockmesh._apply_all(ob)

    def grass(x, z):
        return "GrassDark" if _fbm(x / 26, z / 26, 77) > 0.56 else "Grass"

    # 4. colour each face, then 5. split by chunk + colour
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    groups = {}
    for face in bm.faces:
        c = face.calc_center_median()
        n = face.normal
        rx, ry, rz = c.x, c.z, -c.y               # Roblox coords
        if n.z > 0.65 or (n.z > 0.3 and at(rx, rz) and ry > at(rx, rz)[0] - 1.3):
            col = at(rx, rz)
            if col is None:
                mat = "Rock"
            else:
                top, kind, surf = col
                mat = {"beach": "Beach", "path": "Dirt", "lava": "Lava", "ice": "Ice"}.get(
                    kind, "Stone" if surf == "rocktop" else grass(rx, rz))
        elif n.z < -0.5:
            mat = "Rock"
        else:
            # which column does this face belong to? step into the solid
            h = Vector((n.x, n.y, 0))
            h = h.normalized() if h.length > 1e-6 else Vector((0, 0, 0))
            inner = c - h * 1.2
            col = at(inner.x, -inner.y)
            if col is None:
                mat = "Rock"
            else:
                top, kind, surf = col
                if kind in ("beach", "ice"):
                    mat = "Beach"
                elif kind == "lava":
                    mat = "Lava" if ry > top - 1.0 else ("Band" if ry > top - 2.5 else "Rock")
                elif kind == "path":
                    mat = "Dirt" if ry > top - 2 else "Rock"
                elif ry > top - 1.3:
                    mat = "Stone" if surf == "rocktop" else grass(rx, rz)   # grass lip over the edge
                elif ry > top - 3.2:
                    mat = "Band"                                     # yellow sand band
                else:
                    mat = "Rock"
        key = (int(math.floor(rx / CHUNK)), int(math.floor(rz / CHUNK)), mat)
        groups.setdefault(key, []).append(face)

    objs = []
    for (cx, cz, mat), faces in sorted(groups.items()):
        nb = bmesh.new()
        vmap = {}
        for face in faces:
            vs = []
            for v in face.verts:
                if v.index not in vmap:
                    vmap[v.index] = nb.verts.new(v.co)
                vs.append(vmap[v.index])
            try:
                nb.faces.new(vs)
            except ValueError:
                pass
        oname = "%s_%d_%d_%s" % (name, cx + 8, cz + 8, mat)
        pme = bpy.data.meshes.new(oname)
        nb.to_mesh(pme)
        nb.free()
        po = bpy.data.objects.new(oname, pme)
        coll.objects.link(po)
        for p in pme.polygons:
            p.use_smooth = False
        rockmesh.box_uv(pme)
        pme.materials.append(rockmesh.stud_material(mats[mat], tex_dir))
        po["voxel_color"] = mats[mat]
        objs.append(po)
    bm.free()
    bpy.data.objects.remove(ob)
    return objs
