"""blender.exe -b --python furina_hand_radius.py : FBX/Furina_cm.fbx 의 손 스킨 메시에서 뼈별(손가락 마디/손바닥) 스킨 반경(가중치 0.5 이상 정점의 뼈 선분까지 거리: 평균/90%/최대)을 구한다.  -> Data/furina_hand_radius.json"""
import bpy, json, math
import numpy as np
from mathutils import Vector
SRC = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\FBX\Furina_cm.fbx'; OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\furina_hand_radius.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']; meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('arms', [a.name for a in arms], 'meshes', [(m.name, len(m.data.vertices)) for m in meshes][:8])
arm = arms[0]; bones = arm.pose.bones
R = {}
names = ['IndexFinger1_R', 'IndexFinger2_R', 'IndexFinger3_R', 'MiddleFinger1_R', 'MiddleFinger2_R', 'RingFinger1_R', 'RingFinger2_R', 'LittleFinger1_R', 'LittleFinger2_R', 'Thumb1_R', 'Thumb2_R', 'Right-wrist', 'IndexFinger2_L', 'MiddleFinger2_L', 'Right-hand', 'Hand_R']
M = np.array(arm.matrix_world)
for nm in names:
    if nm not in bones: continue
    b = bones[nm]; h = np.array(arm.matrix_world @ b.head); t = np.array(arm.matrix_world @ b.tail)
    ds = []
    for me in meshes:
        vg = me.vertex_groups.get(nm)
        if vg is None: continue
        MW = np.array(me.matrix_world)
        for v in me.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0.5:
                    p = MW[:3, :3] @ np.array(v.co) + MW[:3, 3]
                    d = t - h; L = max(1e-9, d @ d); s = min(1, max(0, ((p - h) @ d) / L)); ds.append(float(np.linalg.norm(p - (h + s * d))))
    if ds: R[nm] = {'n': len(ds), 'len_cm': round(float(np.linalg.norm(t - h)) * 100, 3), 'mean_cm': round(float(np.mean(ds)) * 100, 3), 'p90_cm': round(float(np.percentile(ds, 90)) * 100, 3), 'max_cm': round(float(np.max(ds)) * 100, 3)}
print(json.dumps(R, indent=1)); json.dump(R, open(OUT, 'w'), indent=1)
