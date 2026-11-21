"""blender.exe -b --python pistol_fbx_bounds.py : Armpist.fbx FPS_Pistol_Idle 0프레임에서 프레임/슬라이드/탄창 메시 경계 상자와 손 뼈 위치를 총 컴포넌트 축(X왼쪽·Y앞·Z위 = FBX (x,-y,z)) cm 로 뽑는다 -> Data/pistol_fbx_bounds.json"""
import bpy, json
import numpy as np
SRC = r'C:\Users\fromj\Downloads\fps-pistol-animations\source\Armpist.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\pistol_fbx_bounds.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = bpy.data.objects['Armature']; sc = bpy.context.scene
if arm.animation_data is None: arm.animation_data_create()
act = [a for a in bpy.data.actions if a.name.split('|')[-1] == 'FPS_Pistol_Idle'][0]
arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
sc.frame_set(int(act.frame_range[0])); bpy.context.view_layer.update()
def verts(name):
    o = bpy.data.objects[name]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); M = np.array(oe.matrix_world)
    w = (co @ M[:3, :3].T + M[:3, 3]) * 100; oe.to_mesh_clear(); return w
def conv(a): a = np.asarray(a); return np.stack([a[..., 0], -a[..., 1], a[..., 2]], -1)
R = {}
for k, nm in (('frame', 'xd_frame'), ('slide', 'xd_frame.001'), ('mag', 'xd_frame.002')):
    w = conv(verts(nm)); R[k] = {'min': [round(float(x), 2) for x in w.min(0)], 'max': [round(float(x), 2) for x in w.max(0)], 'centroid': [round(float(x), 2) for x in w.mean(0)]}
bones = {}
for b in arm.pose.bones:
    if b.name in ('Hand_R', 'Hand_L', 'IK_Hand_Cntrl_R', 'IK_Hand_Cntrl_L') or b.name.startswith(('Bone_R', 'Bone_L')) or b.name.endswith(('_R', '_L')) and 'Fore' not in b.name and 'Up' not in b.name:
        h = conv(np.array(arm.matrix_world @ b.head) * 100); t = conv(np.array(arm.matrix_world @ b.tail) * 100); bones[b.name] = [[round(float(x), 2) for x in h], [round(float(x), 2) for x in t]]
R['bones'] = bones
json.dump(R, open(OUT, 'w'), indent=1); print('BOUNDS_OK', len(bones))
