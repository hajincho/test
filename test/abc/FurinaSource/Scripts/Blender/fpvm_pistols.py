"""Make original, game-only first-person clips from the supplied pistol props."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpvm_lib as rig
import fpvm_lib2 as poses


FPS = 30
PISTOL_POS = (28., -6., -6.5)   # 카메라 공간 cm(앞, 오른쪽=-, 위). fpvm_ads_calc.py 의 권총 정조준 계산과 같은 값


def visual_top(prop, key):
    mesh = bmesh.new()
    mesh.from_mesh(prop.data)
    # Source meshes use split normals, so identify connected surface regions on
    # a welded analysis copy. Keep the visible geometry's original UVs.
    index = {tuple(round(c, 3) for c in vertex.co): [] for vertex in mesh.verts}
    for vertex in mesh.verts:
        index[tuple(round(c, 3) for c in vertex.co)].append(vertex)
    pending = set(mesh.verts)
    regions = []
    while pending:
        seed = pending.pop()
        region = [seed]
        for vertex in region:
            coincident = index[tuple(round(c, 3) for c in vertex.co)]
            adjacent = [edge.other_vert(vertex) for edge in vertex.link_edges]
            for other in (*coincident, *adjacent):
                if other in pending:
                    pending.remove(other)
                    region.append(other)
        regions.append(region)
    if key == 'p08':
        # Small upward accent on the existing exterior model for game feedback.
        faces = {face.index for face in mesh.faces if 1.3 < face.calc_center_median().y < 9.6 and face.calc_center_median().z > 4.7}
    else:
        candidates = [region for region in regions if min(v.co.z for v in region) > 2.1 and len(region) > 350]
        region = set(max(candidates, key=len))
        faces = {face.index for face in mesh.faces if all(v in region for v in face.verts)}
    assert faces, key
    moved = prop.data.copy()
    part_mesh = bmesh.new()
    part_mesh.from_mesh(moved)
    bmesh.ops.delete(part_mesh, geom=[f for f in part_mesh.faces if f.index not in faces], context='FACES')
    part_mesh.to_mesh(moved)
    part_mesh.free()
    bmesh.ops.delete(mesh, geom=[f for f in mesh.faces if f.index in faces], context='FACES')
    mesh.to_mesh(prop.data)
    mesh.free()
    part = bpy.data.objects.new('MovingExterior', moved)
    bpy.context.scene.collection.objects.link(part)
    return part


def unit_interval(time, start, finish):
    x = min(1., max(0., (time - start) / (finish - start)))
    return x * x * (3 - 2 * x)


def main():
    key = sys.argv[sys.argv.index('--') + 1]
    assert key in ('p38', 'p08', 'pp')
    arm, hands, _ = rig.load_arms('a1')
    arm.name = 'Armature'
    if hands.data.shape_keys:
        hands.shape_key_clear()
    for uv in list(hands.data.uv_layers)[1:]:
        hands.data.uv_layers.remove(uv)
    print('SLEEVES', poses.fold_sleeves(arm))   # 소매 날개를 팔꿈치 쪽으로 접어 손이 보이게
    gun = rig.load_weapon(key)
    top = visual_top(gun, key)
    position = PISTOL_POS   # 2026-11-21: 예전 (24,-4,-15) 은 총이 눈 아래 15cm 라 쥔 손이 화면(세로 ±27°) 밖 -> 손이 안 보였음
    transform = rig.gun_native_to_cam(position, 2.5, 4., -3.)
    for prop in (gun, top):
        prop.matrix_world = transform
    bpy.context.view_layer.update()
    ik = poses.setup_ik(arm)
    mesh = poses.bvh_of([gun, top])
    grip_y = {'p38': 5.5, 'p08': 6., 'pp': 4.6}[key]
    controls = {}
    for side, sign in (('R', 1), ('L', -1)):
        point = transform @ Vector((-sign * 9., grip_y - (0. if side == 'R' else 1.5), -2.2))
        direction = (transform.to_3x3() @ Vector((sign, 0, 0))).normalized()
        contact = mesh.ray_cast(point, direction, .3)[0]
        if contact is None:
            contact = transform @ Vector((-sign * 1.05, grip_y, -2.2))
        wrist_axes = rig.hand_axes(arm, side)
        fingers = rig.finger_axes(arm, side, wrist_axes)
        finger_dir = (transform.to_3x3() @ Vector((0, -.48, -.88))).normalized()
        pole = Vector((-.04, -.20 * sign, -.28))   # 팔꿈치를 아래·바깥으로(아래팔이 가파르게 내려가 소매가 손을 덜 가림)
        poses.place_hand(arm, ik, side, wrist_axes, contact, finger_dir, direction,
                         palm_off_cm=1.35, along=.42, elbow_hint_m=contact + pole)
        poses.calib_pole(arm, ik, side, ik['T_' + side].location, contact + pole)
        seat = poses.seat_hand(arm, hands, ik, side, wrist_axes, mesh)   # 손바닥을 손잡이에 붙임
        grip = poses.grip_fingers(arm, side, fingers, mesh, r_cm=0.55, limits={'Thumb': (20, 25, 25), 'default': (76, 90, 64)})
        print('SEAT', key, side, seat)
        controller = ik['T_' + side]
        controls[side] = (controller.location.copy(), controller.rotation_quaternion.copy(), pole, fingers, grip)

    if 'preview' in sys.argv:   # 대기 자세 미리보기(1인칭 화면 + 옆)만 그리고 끝
        for side, (location, rotation, pole, fingers, grip) in controls.items(): poses.apply_fingers(arm, fingers, grip)
        for m in bpy.data.materials: m.diffuse_color = (0.85, 0.7, 0.62, 1) if 'Skin' in m.name else (0.25, 0.3, 0.55, 1) if 'Outfit' in m.name else (0.3, 0.3, 0.32, 1)
        poses.render_views(str(Path(rig.D) / 'Data' / f'fpvm_{key}_prev'), views=('fp', 'side', 'front'), look=tuple(transform @ Vector((0, 0, 0))), scale=0.45)
        return
    root = transform @ Vector((0, 0, 0))
    top_pivot = transform @ Vector((0, 5., 4.))
    forward = Vector((.05, 0, 0))
    rig.add_bone(arm, 'VM_Gun', 'Hips', root, root + forward)
    rig.add_bone(arm, 'VM_Exterior', 'VM_Gun', top_pivot, top_pivot + forward)
    rig.bind_rigid(arm, gun, 'VM_Gun')
    rig.bind_rigid(arm, top, 'VM_Exterior')
    for bone in arm.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    rest = {name: arm.data.bones[name].matrix_local.copy() for name in ('VM_Gun', 'VM_Exterior')}
    constraints = [constraint for bone in arm.pose.bones for constraint in bone.constraints]
    actions = {}
    for motion, duration in (('Idle', 4.), ('Fire', .30), ('Reload', 1.8)):
        arm.animation_data_create()
        arm.animation_data.action = None
        for constraint in constraints:
            constraint.mute = False
        frames = []
        for frame in range(round(duration * FPS) + 1):
            time = frame / FPS
            fire = unit_interval(time, 0, .045) * (1 - unit_interval(time, .05, .24)) if motion == 'Fire' else 0.
            reload = unit_interval(time, 0, .28) * (1 - unit_interval(time, 1.35, 1.8)) if motion == 'Reload' else 0.
            breath = math.sin(time / 4 * math.tau) if motion == 'Idle' else 0.
            delta = Matrix.Translation((-.017 * fire, .015 * reload, .0016 * breath - .065 * reload))
            delta @= Matrix.Translation(root) @ Matrix.Rotation(math.radians(-3.2 * fire + 12. * reload), 4, 'Y') @ Matrix.Translation(-root)
            for side, (location, rotation, pole, fingers, grip) in controls.items():
                target = ik['T_' + side]
                target.location = delta @ location
                if side == 'L':
                    target.location += Vector((-.025, .025, -.13)) * reload
                target.rotation_quaternion = delta.to_quaternion() @ rotation
                ik['P_' + side].location = target.location + pole
                poses.apply_fingers(arm, fingers, grip)
            arm.pose.bones['VM_Gun'].matrix = delta @ rest['VM_Gun']
            bpy.context.view_layer.update()
            accent = Matrix.Translation((-.008 * fire, 0, .003 * fire))
            if key == 'p08':
                accent = Matrix.Translation(top_pivot) @ Matrix.Rotation(math.radians(-18 * fire), 4, 'Y') @ Matrix.Translation(-top_pivot)
            arm.pose.bones['VM_Exterior'].matrix = delta @ accent @ rest['VM_Exterior']
            bpy.context.view_layer.update()
            frames.append({bone.name: arm.convert_space(pose_bone=bone, matrix=bone.matrix, from_space='POSE', to_space='LOCAL').copy() for bone in arm.pose.bones})
        for constraint in constraints:
            constraint.mute = True
        action = bpy.data.actions.new(f'FPVM_{key.upper()}_{motion}')
        action.use_fake_user = True
        arm.animation_data.action = action
        for frame, matrices in enumerate(frames, 1):
            for bone in arm.pose.bones:
                bone.matrix_basis = matrices[bone.name]
                for path in ('location', 'rotation_quaternion', 'scale'):
                    bone.keyframe_insert(data_path=path, frame=frame, group=bone.name)
        actions[motion] = action
    for bone in arm.pose.bones:
        for constraint in list(bone.constraints):
            bone.constraints.remove(constraint)
    for helper in ik.values():
        bpy.data.objects.remove(helper)
    arm.animation_data.action = actions['Idle']
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.render.fps_base = 1.0
    bpy.ops.object.select_all(action='DESELECT')
    for obj in (arm, hands, gun, top):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = Path(rig.D) / 'FBX' / 'FPVM' / f'SK_FPVM_{key.upper()}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'ARMATURE', 'MESH'},
                             axis_forward='-Y', axis_up='Z', add_leaf_bones=False, armature_nodetype='NULL',
                             bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP')
    for motion, action in actions.items():
        arm.animation_data.action = action
        start, end = action.frame_range
        bpy.context.scene.frame_start = round(start)
        bpy.context.scene.frame_end = round(end)
        target = path.with_name(f'AS_FPVM_{key.upper()}_{motion}.fbx')
        bpy.ops.export_scene.fbx(filepath=str(target), use_selection=True, object_types={'ARMATURE'},
                                 axis_forward='-Y', axis_up='Z', add_leaf_bones=False, armature_nodetype='NULL',
                                 bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                                 bake_anim_simplify_factor=0.)
    print(json.dumps({'key': key, 'scene_prop': str(path), 'body_faces': len(gun.data.polygons), 'top_faces': len(top.data.polygons)}))


if __name__ == '__main__':
    main()
