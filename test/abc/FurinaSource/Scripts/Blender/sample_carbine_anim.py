"""blender.exe -b --python sample_carbine_anim.py [-- 시작 끝 간격 출력태그] : arms@carbine.fbx 를 매 2프레임 샘플링. 카라빈(carbine 빈 객체) 기준 로컬 좌표로 부품(clip, bolt, handle, release, boltcatch, lid, trigger)과 양손목/팔꿈치/손가락 뿌리 위치를 cm 로 기록.
 -> Data/carbine_anim_samples.json"""
import bpy, json, math, mathutils
SRC = r'C:\Users\fromj\Downloads\fps-animated-carbine\source\arms@carbine.fbx'
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\carbine_anim_samples.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_anim=True, anim_offset=0, automatic_bone_orientation=False, ignore_leaf_bones=False)
O = bpy.data.objects; arm = O['Null']; car = O['carbine']; base = O['base']
sc = bpy.context.scene
# 총 길이(월드)로 단위 환산: base 메시 월드 바운딩의 최장 변 = 약 74cm(카라빈)로 가정하지 않고, 원시값(월드 단위)과 함께 기록
def world_len(o):
    ws = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    xs = [[w[i] for w in ws] for i in range(3)]; return [max(x) - min(x) for x in xs]
sc.frame_set(1)
R = {'base_world_dims': world_len(base), 'clip_world_dims': world_len(O['clip']), 'armmesh_world_dims': world_len(O['armmesh'])}
longest = max(R['base_world_dims']); K = 74.0 / longest   # 가정: 총 전체 길이 약 74cm 로 스케일(참고용, 정확하지 않음). 원시 월드 값도 저장.
R['assumed_scale_to_cm'] = K
parts = ['clip', 'bullet', 'bolt', 'handle', 'handle2', 'release', 'boltcatch', 'lid', 'trigger', 'scope']
bones = ['R_wrist', 'L_wrist', 'R_elbow', 'L_elbow', 'R_point1', 'L_point1', 'R_thumb1', 'L_thumb1', 'R_palm', 'L_palm']
R['samples'] = []
import sys
FR = range(int(sys.argv[sys.argv.index('--') + 1]), int(sys.argv[sys.argv.index('--') + 2]) + 1, int(sys.argv[sys.argv.index('--') + 3])) if '--' in sys.argv else range(0, 223, 2)
OUTN = sys.argv[sys.argv.index('--') + 4] if '--' in sys.argv else None
for f in FR:
    sc.frame_set(f); cm = car.matrix_world.copy(); loc, rot, scl = cm.decompose(); inv = (mathutils.Matrix.Translation(loc) @ rot.to_matrix().to_4x4()).inverted(); row = {'f': f}
    def rel(m):
        t = (inv @ m).to_translation(); return [round(t.x * K, 2), round(t.y * K, 2), round(t.z * K, 2)]
    row['carbine_world_cm'] = [round(x * K, 1) for x in car.matrix_world.to_translation()]; row['carbine_rot'] = [round(math.degrees(a), 1) for a in car.matrix_world.to_euler()]
    for p in parts: row[p] = rel(O[p].matrix_world)
    for b in bones:
        pb = arm.pose.bones.get(b)
        if pb: row[b] = rel(arm.matrix_world @ pb.matrix)
    R['samples'].append(row)
json.dump(R, open(OUT if not OUTN else OUT.replace('samples', OUTN), 'w'), indent=1)
print('SAMPLE_OK', len(R['samples']))
