"""FBX export for Roblox's 3D importer.

Every part becomes one mesh object named "<Id>__<Part>" with a plain white
material (the colour is set on the MeshPart in Studio). Geometry is written in
Roblox axes (Y up, -Z forward). Four small marker cubes (FV_AxisO/X/Y/Z, 4 studs
apart along Roblox X, Y, Z) let the rig script detect the importer's scale and
orientation, so it works whatever import settings are used.
"""
import bpy
from mathutils import Matrix, Vector

import rbxscene as rs

MARK_O = Vector((-6.0, 0.0, 0.0))     # Roblox space
MARK_STEP = 4.0
LAYOUT_STEP = 3.0                      # weapons are laid out along Roblox X in the file


def _white():
    m = bpy.data.materials.get("White") or bpy.data.materials.new("White")
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
        bsdf.inputs["Roughness"].default_value = 0.5
        bsdf.inputs["Metallic"].default_value = 0.0
    return m


def _marker(name, pos_rb, coll):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=0.25)
    bm.to_mesh(me)
    bm.free()
    me.transform(rs.RB2BL @ Matrix.Translation(pos_rb))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def export(scene, built, path):
    white = _white()
    coll = bpy.data.collections.new("FBXExport")
    scene.collection.children.link(coll)
    objs = []
    renamed = []
    for i, (wcoll, wobjs, info) in enumerate(built):
        off = rs.RB2BL @ Vector((i * LAYOUT_STEP, 0, 0))
        for ob in wobjs:
            name = ob.name                                   # "<Id>__<Part>"
            # move the preview object out of the way so the export copy gets the exact name
            ob.name = name + "~src"
            ob.data.name = name + "~src"
            renamed.append((ob, name))
            dup = ob.copy()
            dup.data = ob.data.copy()
            dup.name = name
            dup.data.name = name
            assert dup.name == name, dup.name
            dup.data.materials.clear()
            dup.data.materials.append(white)
            dup.data.transform(Matrix.Translation(off))
            coll.objects.link(dup)
            objs.append(dup)
    for name, d in (("FV_AxisO", Vector((0, 0, 0))), ("FV_AxisX", Vector((MARK_STEP, 0, 0))),
                    ("FV_AxisY", Vector((0, MARK_STEP, 0))), ("FV_AxisZ", Vector((0, 0, MARK_STEP)))):
        objs.append(_marker(name, MARK_O + d, coll))
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
                             bake_space_transform=True, mesh_smooth_type="OFF",
                             use_mesh_modifiers=True, add_leaf_bones=False, path_mode="STRIP",
                             use_custom_props=False)
    print("exported", path, len(objs), "objects")
    for ob in objs:
        me = ob.data
        bpy.data.objects.remove(ob)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    bpy.data.collections.remove(coll)
    for ob, name in renamed:
        ob.name = name
        ob.data.name = name
