"""blender -b --python de_stg44_fix.py : StG44 정리본에서 어깨끈(Belt) 제거 + 총구 방향을 다른 무기와 같게(-Y)로 Z 180° (원본 백업 _export/SM_DE_stg44_orig.fbx)"""
import bpy, bmesh, math, shutil, os
from mathutils import Matrix
P = r'C:\Users\fromj\Downloads\FurinaWeaponSrc\Germany\_export\SM_DE_stg44.fbx'; B = P.replace('.fbx', '_orig.fbx')
if not os.path.exists(B): shutil.copy(P, B)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=B)
o = [x for x in bpy.data.objects if x.type == 'MESH'][0]; mats = [m.name for m in o.data.materials]
bm = bmesh.new(); bm.from_mesh(o.data); n0 = len(bm.faces)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if mats[f.material_index] == 'Belt'], context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(o.data); bm.free()
bi = mats.index('Belt'); o.active_material_index = bi; bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.material_slot_remove()
o.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
ys = [v.co.y for v in o.data.vertices]
bpy.ops.export_scene.fbx(filepath=P, use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True, mesh_smooth_type='FACE', path_mode='STRIP', add_leaf_bones=False, bake_anim=False)
print('STG44_FIX faces', n0, '->', len(o.data.polygons), 'mats', [m.name for m in o.data.materials], 'y', round(min(ys), 3), round(max(ys), 3))
