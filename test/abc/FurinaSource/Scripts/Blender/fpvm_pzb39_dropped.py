"""Export the game pickup prop with its origin at the hand grip."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpvm_lib as rig
from fpvm_pzb39 import open_rear_notch

bpy.ops.wm.read_factory_settings(use_empty=True)
weapon = rig.load_weapon('pzb39')
transform = (Matrix.Rotation(math.pi / 2, 4, 'Z')
             @ Matrix.Scale(.01, 4)
             @ Matrix.Translation((0, -44., 1.5)))
weapon.matrix_world = transform
notch, _ = open_rear_notch(weapon, transform)
bpy.ops.object.select_all(action='DESELECT')
for obj in (weapon, notch):
    obj.select_set(True)
bpy.context.view_layer.objects.active = weapon
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
bpy.ops.export_scene.fbx(filepath=str(Path(rig.D) / 'FBX/FPVM/SM_PZB39_Dropped.fbx'),
                        use_selection=True, object_types={'MESH'}, axis_up='Z', axis_forward='-Y',
                        apply_unit_scale=True, bake_anim=False, path_mode='STRIP')
