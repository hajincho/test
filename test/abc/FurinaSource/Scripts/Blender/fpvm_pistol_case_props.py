"""Prepare supplied cartridge artwork as Unreal visual props."""
from math import atan2, pi
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(sys.argv[sys.argv.index('--') + 1])
OUTPUT = ROOT / 'FBX' / 'FX'


def export(name, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(filepath=str(OUTPUT / (name+'.fbx')), use_selection=True,
                             object_types={'MESH'}, bake_anim=False, axis_forward='-Y',
                             axis_up='Z', mesh_smooth_type='FACE', path_mode='STRIP')


def stl(name, slot, projectile=False):
    bpy.ops.wm.stl_import(filepath=str(SOURCE / name), use_scene_unit=False)
    part = bpy.context.object
    if projectile:
        part.data.transform(Matrix.Translation((-8.732, 0., 0.)))
    part.data.transform(Matrix.Rotation((-1 if projectile else 1) * pi/2, 4, 'X') @ Matrix.Scale(.001, 4))
    if len(part.data.polygons) > 6000:
        mod = part.modifiers.new('Game mesh budget', 'DECIMATE')
        mod.ratio = 6000 / len(part.data.polygons)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    lowest = min(v.co.z for v in part.data.vertices)
    high = max(v.co.z for v in part.data.vertices)
    # The loose component files are laid out side-by-side. Seat them for the
    # display prop, while the spawned visual effect exports the empty case.
    part.data.transform(Matrix.Translation((0, 0, (.014 if projectile else 0) - lowest)))
    mat = bpy.data.materials.new(slot)
    part.data.materials.append(mat)
    uv = part.data.uv_layers.new(name='UVMap')
    for poly in part.data.polygons:
        poly.use_smooth = abs(poly.normal.z) < .8
        for idx in poly.loop_indices:
            p = part.data.vertices[part.data.loops[idx].vertex_index].co
            if abs(poly.normal.z) > .8:
                uv.data[idx].uv = (p.x / .009 + .5, p.y / .009 + .5)
            else:
                uv.data[idx].uv = (atan2(p.y, p.x)/(2*pi)+.5, (p.z-(.014 if projectile else 0))/(high-lowest))
    return part


def main():
    OUTPUT.mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SOURCE/'Nine_MM_Bullet.fbx'))
    case = bpy.data.objects['case_GEO']
    export('SM_FPVM_9mmCase', [case])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    case = stl('32-acp-casing.stl', 'Case_Metal048B')
    bullet = stl('32-acp-bullet.stl', 'Bullet_Metal058A', projectile=True)
    export('SM_FPVM_32Case', [case])
    export('SM_FPVM_32Cartridge', [case, bullet])


if __name__ == '__main__':
    main()
