"""blender.exe -b --python extract_pistol_reload_hand.py : Armpist.fbx Reload_easy / Reload_full 의 왼손(Hand_L) 위치를 프레임 무게중심 기준으로 매 프레임 뽑아
 소총(권총) 컴포넌트 기준 좌표(X왼쪽·Y앞·Z위 = FBX (x, -y, z))의 '0프레임 대비 변화량'으로 저장한다.  단위 cm, 60fps.   -> Data/pistol_reload_hand.json"""
import bpy, json
import numpy as np
SRC = r'C:\Users\fromj\Downloads\fps-pistol-animations\source\Armpist.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\pistol_reload_hand.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
arm = bpy.data.objects['Armature']; sc = bpy.context.scene; FPS = sc.render.fps
if arm.animation_data is None: arm.animation_data_create()
def cent(name):
    o = bpy.data.objects[name]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); M = np.array(oe.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]; oe.to_mesh_clear(); return w.mean(0) * 100
R = {'fps': FPS, 'actions': {}}
for act in [a for a in bpy.data.actions if not a.name.endswith(('.001', '.002'))]:
    nm = act.name.split('|')[-1]
    if nm not in ('FPS_Pistol_Reload_easy', 'FPS_Pistol_Reload_full', 'FPS_Pistol_Idle'): continue
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        fr = cent('xd_frame'); h = np.array(arm.matrix_world @ arm.pose.bones['Hand_L'].head) * 100; hr = np.array(arm.matrix_world @ arm.pose.bones['Hand_R'].head) * 100
        sl = cent('xd_frame.001'); mg = cent('xd_frame.002')
        rel = h - fr; relr = hr - fr; rs = sl - fr; rm = mg - fr
        rows.append({'t': round((f - f0) / FPS, 4), 'hl': [float(rel[0]), float(-rel[1]), float(rel[2])], 'hr': [float(relr[0]), float(-relr[1]), float(relr[2])], 'slide': [float(rs[0]), float(-rs[1]), float(rs[2])], 'mag': [float(rm[0]), float(-rm[1]), float(rm[2])]})
    R['actions'][nm] = {'seconds': round((f1 - f0) / FPS, 4), 'rows': rows}
json.dump(R, open(OUT, 'w'), indent=1); print('RELOAD_HAND_OK', {k: len(v['rows']) for k, v in R['actions'].items()})
