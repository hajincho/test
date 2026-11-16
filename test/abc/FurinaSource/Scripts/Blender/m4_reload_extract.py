"""Blender: M4 팩의 Reload(프레임 1~110, 30fps)에서 왼손/오른손/탄창1/탄창2/볼트를 총(Main_j) 기준 좌표로 프레임별 추출.
총 기준 축은 Furina 규칙(X=왼쪽, Y=앞(총구), Z=위)으로 맞춘다: 앞 = 오른손→왼손 방향(프레임1), 왼쪽 = 안전장치 쪽, 위 = 앞×왼쪽 조합.
길이는 Main 메시 길이를 80cm(푸리나 총)로 정규화하는 배율을 적용한 cm.  -> FurinaSource/Data/m4_reload_extract.json
사용: blender.exe -b --python m4_reload_extract.py"""
import bpy, json, math
from mathutils import Vector, Matrix
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\m4_reload_extract.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\fromj\Downloads\m4-fps-weapon-animations-pack-v1\source\M4.fbx', use_anim=True, anim_offset=0.0)
arm = bpy.data.objects['Armature']; main = bpy.data.objects['Main']
act = bpy.data.actions['Armature|Reload|BaseLayer']; arm.animation_data.action = act
for ob in bpy.data.objects:
    if ob.animation_data and ob.type != 'ARMATURE': pass
sc = bpy.context.scene
def pb(name): return arm.pose.bones[name]
def wpos(name): return arm.matrix_world @ pb(name).head
# 총 길이 -> 80cm 배율 (Main 메시 월드 바운딩 박스 최장 변)
sc.frame_set(1); dg = bpy.context.evaluated_depsgraph_get()
me = main.evaluated_get(dg); ws = [main.matrix_world @ v.co for v in me.to_mesh().vertices] if False else None
verts = [arm.matrix_world.inverted() @ (main.matrix_world @ v.co) for v in main.data.vertices]
# 본 변형이 없는 레스트 기준 길이 (총 메시는 본 가중치로 따라가므로 월드 변환 후의 최장 변)
xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
ext = sorted([max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)], reverse=True)
longest = ext[0]; K = 80.0 / longest   # 블렌더 단위 -> cm (푸리나 총 80cm 기준)
R = {'fps': 30, 'unit_to_cm': K, 'mesh_extent_blender_units': ext, 'frames': {}}
# 총 기준 프레임 (프레임 1 기준 고정): 앞 = 오른손 -> 왼손, 왼쪽 = 안전장치 쪽
sc.frame_set(1)
mj = pb('Main_j'); Mw = arm.matrix_world @ mj.matrix
rh = wpos('RightHand'); lh = wpos('LeftHand')
fwd = (lh - rh); fwd = (Mw.to_3x3().inverted() @ fwd).normalized()    # Main_j 로컬에서의 앞 벡터
safety = bpy.data.objects['Safety']; sv = [safety.matrix_world @ v.co for v in safety.data.vertices]; sc_c = sum(sv, Vector()) / len(sv)
main_c = sum([main.matrix_world @ v.co for v in main.data.vertices], Vector()) / len(main.data.vertices)
side = (Mw.to_3x3().inverted() @ (sc_c - main_c))
side = (side - fwd * side.dot(fwd)).normalized()                      # 왼쪽 후보(안전장치 방향) - 앞과 직교화
up_r = side.cross(fwd).normalized()                                  # 우수계: 왼쪽 x 앞 = 위?  (확인은 탄창 방향으로)
mag1 = pb('Mag1_j'); m1_local = (Mw.inverted() @ (arm.matrix_world @ mag1.head))
R['axes_check'] = {'fwd_local': list(fwd), 'side_local': list(side), 'up_candidate_local': list(up_r), 'mag1_in_main_local': list(m1_local),
                   'mag_dot_up_candidate': m1_local.dot(up_r), 'mag_dot_fwd': m1_local.dot(fwd)}
# 탄창은 총 아래에 있어야 한다 -> 위 = 탄창 반대
up = up_r if m1_local.dot(up_r) < 0 else -up_r
left = side
R['axes_check']['chosen_up_local'] = list(up)
# 우수계 확인: 푸리나(언리얼) 규칙 X=왼쪽, Y=앞, Z=위 는 좌수계이므로 (왼쪽, 앞, 위)의 행렬식이 우수계에서 음수여야 한다
R['axes_check']['det_left_fwd_up'] = left.dot(fwd.cross(up))
names = ['RightHand', 'LeftHand', 'Mag1_j', 'Mag2_j', 'Bolt_j', 'BoltCatch_j', 'Trigger_j']
def to_gun(Mmain_inv_rot, Mm, p):
    d = Mmain_inv_rot @ (p - Mm.translation) if False else (Mm.inverted() @ p)
    return [round(d.dot(left) * K, 3), round(d.dot(fwd) * K, 3), round(d.dot(up) * K, 3)]
for f in range(1, 111):
    sc.frame_set(f); Mw = arm.matrix_world @ pb('Main_j').matrix
    row = {}
    for n in names:
        row[n] = to_gun(None, Mw, wpos(n))
    # 탄창 축 기울기 (총 기준): 탄창 본의 'Y' 로컬축 방향을 총 로컬에서
    for n in ('Mag1_j', 'Mag2_j'):
        mm = arm.matrix_world @ pb(n).matrix; d = (Mw.inverted().to_3x3() @ mm.to_3x3()) @ Vector((0, 1, 0))
        row[n + '_axisY'] = [round(d.dot(left), 3), round(d.dot(fwd), 3), round(d.dot(up), 3)]
    # 총 자체의 카메라 대비 움직임 (총이 기울어지는지): Main_j 의 월드 위쪽 벡터
    wu = (Mw.to_3x3() @ up).normalized(); wf = (Mw.to_3x3() @ fwd).normalized()
    row['gun_fwd_world'] = [round(v, 3) for v in wf]; row['gun_up_world'] = [round(v, 3) for v in wu]
    row['gun_pos_world_cm'] = [round(v * K, 2) for v in Mw.translation]
    R['frames'][f] = row
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('M4_RELOAD_EXTRACT K=%.3f' % K, R['axes_check'])
