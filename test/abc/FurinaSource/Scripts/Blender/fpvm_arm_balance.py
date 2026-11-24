"""기존 1인칭 동작에서 손 위치를 유지하며 위팔과 전완의 자세를 다시 균형 잡는다."""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fpvm_lib2 import key_baked_pose


def swing_about(pivot, rotation):
    return Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot)


def arm_turn(upper, lower, wrist, knuckle):
    shoulder = upper.translation
    elbow = lower.translation
    hand = knuckle.translation - wrist.translation
    forearm = wrist.translation - elbow
    axis = (wrist.translation - shoulder).normalized()
    radial = elbow - shoulder
    radial -= axis * radial.dot(axis)
    preferred = -(hand - axis * hand.dot(axis))
    if min(radial.length, preferred.length) < 0.002:
        return 0.0
    deviation = math.degrees(forearm.angle(hand, 0.0))
    weight = min(1.0, max(0.0, (deviation - 35.0) / 37.0))
    weight = weight * weight * (3.0 - 2.0 * weight)
    return math.radians(42.0) * weight * axis.dot(radial.normalized().cross(preferred.normalized()))


def roll_share(lower, wrist, bind_relative):
    lower_rotation = lower.to_quaternion()
    axis = (wrist.translation - lower.translation).normalized()
    local_axis = lower_rotation.inverted() @ axis
    delta = lower_rotation.inverted() @ wrist.to_quaternion() @ bind_relative.inverted()
    projected = Vector((delta.x, delta.y, delta.z)).dot(local_axis)
    # q와 -q가 같은 보정을 만들고 손목이 반바퀴 경계를 지나도 부호가 튀지 않는다.
    return axis, 0.48 * delta.w * projected


def free_wrist_positions(samples, wrist, props, unit):
    positions = [frame[wrist].translation for frame in samples]
    locked = set()
    for prop in props:
        local = [frame[prop].inverted_safe() @ position for frame, position in zip(samples, positions)]
        still = [(frame[prop].to_3x3() @ (local[index] - local[index - 1])).length * unit < 0.00065
                 for index, frame in enumerate(samples) if index]
        for index in range(1, len(samples) - 1):
            if still[index - 1] and still[index]:
                locked.add(index)

    revised = {}
    weights = (1, 4, 6, 4, 1)
    for index in range(2, len(samples) - 2):
        window = range(index - 2, index + 3)
        if any(frame in locked for frame in window):
            continue
        smoothed = sum((positions[frame] * weight for frame, weight in zip(window, weights)), Vector()) / 16.0
        correction = smoothed - positions[index]
        scale = min(1.0, 0.035 / max(1e-7, unit * correction.length))
        revised[index] = positions[index] + correction * scale
    return revised


def reach_free_position(upper, lower, wrist, goal):
    shoulder, old_elbow, old_wrist = (matrix.translation for matrix in (upper, lower, wrist))
    a_vec, b_vec = old_elbow - shoulder, old_wrist - old_elbow
    a, b = a_vec.length, b_vec.length
    reach = goal - shoulder
    distance = reach.length
    if not abs(a - b) + 1e-5 < distance < a + b - 1e-5:
        return upper, lower, wrist
    axis = reach / distance
    radial = a_vec - axis * a_vec.dot(axis)
    if radial.length < 1e-6:
        return upper, lower, wrist
    along = (distance * distance + a * a - b * b) / (2.0 * distance)
    new_elbow = shoulder + axis * along + radial.normalized() * math.sqrt(max(0.0, a * a - along * along))
    upper = swing_about(shoulder, a_vec.rotation_difference(new_elbow - shoulder)) @ upper
    lower = Matrix.Translation(new_elbow - old_elbow) @ swing_about(old_elbow, b_vec.rotation_difference(goal - new_elbow)) @ lower
    wrist = Matrix.Translation(goal - old_wrist) @ wrist
    return upper, lower, wrist


def relax_free_rotation(forearm, hand_direction):
    bend = forearm.angle(hand_direction, 0.0)
    weight = min(1.0, max(0.0, (math.degrees(bend) - 55.0) / 52.0))
    axis = hand_direction.cross(forearm)
    if axis.length < 1e-6:
        return Quaternion()
    return Quaternion(axis, math.radians(36.0) * weight * weight * (3.0 - 2.0 * weight))


def balance_clip(source, destination, support=None, support_only=False, pin_grip=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source))
    arm = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
    original = arm.animation_data.action
    first, last = (round(value) for value in original.frame_range)
    scene = bpy.context.scene
    bones = arm.pose.bones
    sides = {}
    for side, name in (('L', 'Left'), ('R', 'Right')):
        upper, lower, wrist, knuckle = (bones[part] for part in (f'{name} arm', f'{name} elbow', f'{name} wrist', f'MiddleFinger1_{side}'))
        bind = lower.bone.matrix_local.to_quaternion().inverted() @ wrist.bone.matrix_local.to_quaternion()
        sides[side] = ((upper.name, lower.name, wrist.name, knuckle.name), bind)

    samples = []
    angles = {side: [] for side in sides}
    for frame in range(first, last + 1):
        scene.frame_set(frame)
        matrices = {bone.name: bone.matrix.copy() for bone in bones}
        samples.append(matrices)
        for side, (names, _) in sides.items():
            angles[side].append(0.0 if support_only else arm_turn(*(matrices[name] for name in names)))

    unit = arm.matrix_world.to_scale().x
    props = [bone.name for bone in bones if bone.name.startswith('VM_')]
    free = {side: {} if support_only else free_wrist_positions(samples, names[2], props, unit)
            for side, (names, _) in sides.items()}
    offsets, spreads = {}, {}
    if support:
        grip_upper, grip_lower, grip_wrist, _ = sides[support.get('side', 'L')][0]
        reference = Vector(support['grip_location'])
        reference_rotation = Quaternion(support['grip_rotation'])
        for finger in support['fingers'].values():
            for name, degrees in finger['degrees'].items():
                if degrees:
                    offsets[name] = Vector(support['axes'][name]), math.radians(degrees)
            if spread := finger.get('spread'):
                spreads[spread['bone']] = Vector(spread['axis']), math.radians(spread['degrees'])
    revised = bpy.data.actions.new(original.name + '_arms')
    arm.animation_data.action = revised
    for bone in bones:
        bone.rotation_mode = 'QUATERNION'
    previous = {}
    for index, matrices in enumerate(samples):
        if pin_grip:
            old_wrist = matrices[grip_wrist]
            goal = matrices['VM_Gun'] @ Matrix.LocRotScale(reference, reference_rotation, None)
            upper, lower, wrist = reach_free_position(matrices[grip_upper], matrices[grip_lower], old_wrist, goal.translation)
            wrist = Matrix.LocRotScale(wrist.translation, goal.to_quaternion(), old_wrist.to_scale())
            change = wrist @ old_wrist.inverted()
            matrices[grip_upper], matrices[grip_lower], matrices[grip_wrist] = upper, lower, wrist
            for child in bones[grip_wrist].children_recursive:
                matrices[child.name] = change @ matrices[child.name]
        weight = 0.0
        if offsets or spreads:
            gun = matrices['VM_Gun']
            grip = gun.inverted_safe() @ matrices[grip_wrist]
            distance = (gun.to_3x3() @ (grip.translation - reference)).length * unit
            rotation = abs(grip.to_quaternion().dot(reference_rotation))
            position_weight = min(1.0, max(0.0, (0.022 - distance) / 0.017))
            orientation_weight = min(1.0, max(0.0, (rotation - 0.98) / 0.015))
            weight = position_weight * position_weight * (3.0 - 2.0 * position_weight) * orientation_weight

        for side, (names, bind) in sides.items():
            if support_only:
                break
            upper_name, lower_name, wrist_name, knuckle_name = names
            upper, lower, wrist = (matrices[name] for name in names[:3])
            if index in free[side]:
                previous_position = wrist.translation
                direction = matrices[knuckle_name].translation - previous_position
                upper, lower, wrist = reach_free_position(upper, lower, wrist, free[side][index])
                follow = Matrix.Translation(wrist.translation - previous_position)
                available = sum(frame_index in free[side] for frame_index in range(index - 2, index + 3)) / 5.0
                neutral = relax_free_rotation(wrist.translation - lower.translation, direction)
                neutral = Quaternion().slerp(neutral, available)
                turn_hand = swing_about(wrist.translation, neutral)
                wrist = turn_hand @ wrist
                for child in bones[wrist_name].children_recursive:
                    matrices[child.name] = turn_hand @ follow @ matrices[child.name]
            values = angles[side]
            left = values[max(0, index - 1)]
            right = values[min(len(values) - 1, index + 1)]
            turn = (left + 2.0 * values[index] + right) * 0.25
            axis = (wrist.translation - upper.translation).normalized()
            swing = swing_about(upper.translation, Quaternion(axis, turn))
            revised_lower = swing @ lower
            roll_axis, shared = roll_share(revised_lower, wrist, bind)
            matrices[upper_name] = swing @ upper
            matrices[lower_name] = swing_about(revised_lower.translation, Quaternion(roll_axis, shared)) @ revised_lower
            # 손목의 장면 공간 행렬을 유지해 기존 손가락과 접촉점이 함께 따라오게 한다.
            matrices[wrist_name] = wrist

        for bone in bones:
            parent = bone.parent
            matrix = matrices[bone.name]
            if parent is None:
                local = bone.bone.convert_local_to_pose(matrix, bone.bone.matrix_local, invert=True)
            else:
                local = bone.bone.convert_local_to_pose(matrix, bone.bone.matrix_local,
                                                        parent_matrix=matrices[parent.name], parent_matrix_local=parent.bone.matrix_local,
                                                        invert=True)
            if weight and (bone.name in offsets or bone.name in spreads):
                location, rotation, scale = local.decompose()
                if bone.name in spreads:
                    axis, angle = spreads[bone.name]
                    rotation = rotation @ Quaternion(axis, angle * weight)
                if bone.name in offsets:
                    axis, angle = offsets[bone.name]
                    rotation = rotation @ Quaternion(axis, angle * weight)
                local = Matrix.LocRotScale(location, rotation, scale)
            key_baked_pose(bone, local, first + index, previous)

    scene.frame_start, scene.frame_end = first, last
    scene.frame_set(first)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(destination), use_selection=True, object_types={'ARMATURE'},
                             axis_forward='-Y', axis_up='Z', apply_unit_scale=True, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_simplify_factor=0.0, armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
    print('ARM_BALANCE', source.name, last - first + 1, 'FREE', {side: len(values) for side, values in free.items()})


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    source_dir, output_dir = (Path(value) for value in arguments[:2])
    support = next((Path(arg.split('=', 1)[1]) for arg in arguments[2:] if arg.startswith('support=')), None)
    profile = json.loads(support.read_text(encoding='utf-8')) if support else None
    pin_grip = 'pin_grip' in arguments
    if pin_grip and profile is None:
        raise ValueError('pin_grip requires a fitted grip profile')
    for clip in (arg for arg in arguments[2:] if arg.endswith('.fbx')):
        balance_clip(source_dir / clip, output_dir / clip, profile, 'support_only' in arguments, pin_grip)
