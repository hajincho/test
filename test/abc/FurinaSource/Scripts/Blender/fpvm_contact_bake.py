"""Bake fitted hand poses while keeping arm length and the object's contact frame."""

import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Quaternion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fpvm_arm_balance import reach_free_position, roll_share, swing_about
from fpvm_lib2 import key_baked_pose


def smooth(value):
    value = min(1.0, max(0.0, value))
    return value**3 * (10.0 + value * (-15.0 + 6.0 * value))


def solve_arm(collar, upper, lower, wrist, goal, scale):
    shoulder, elbow, old_end = (matrix.translation for matrix in (upper, lower, wrist))
    a, b = (elbow - shoulder).length, (old_end - elbow).length
    direction = goal.translation - shoulder
    long, short = a + b - 0.008 / scale, abs(a - b) + 0.032 / scale
    if direction.length > long and (shoulder - collar.translation).length > 0.001 / scale:
        clavicle = shoulder - collar.translation
        adjustment = direction.normalized() * min(0.022 / scale, direction.length - long)
        rotation = clavicle.rotation_difference(clavicle + adjustment)
        rotation = Quaternion().slerp(rotation, min(1.0, math.radians(12.0) / max(rotation.angle, 1e-6)))
        move = swing_about(collar.translation, rotation)
        collar, upper, lower, wrist = (move @ matrix for matrix in (collar, upper, lower, wrist))
        shoulder = upper.translation
        direction = goal.translation - shoulder
        # The shoulder girdle can slide forward without increasing either limb length.
        protraction = direction.normalized() * min(0.024 / scale, max(0.0, direction.length - long))
        move = Matrix.Translation(protraction)
        collar, upper, lower, wrist = (move @ matrix for matrix in (collar, upper, lower, wrist))
        shoulder = upper.translation
        direction = goal.translation - shoulder
    end = shoulder + direction.normalized() * min(long, max(short, direction.length))
    upper, lower, wrist = reach_free_position(upper, lower, wrist, end)
    wrist = Matrix.LocRotScale(wrist.translation, goal.to_quaternion(), wrist.to_scale())
    return collar, upper, lower, wrist


def weight_for(time, attachment, relative, reference, prop, scale, clip, wrist):
    if attachment:
        approach, held, release, free = attachment
        return smooth((time - approach) / (held - approach)) * (1.0 - smooth((time - release) / (free - release)))
    if not clip.endswith('_Reload') or wrist == 'Right wrist':
        return 1.0
    distance = (prop.to_3x3() @ (relative.translation - reference.translation)).length * scale
    alignment = abs(relative.to_quaternion().dot(reference.to_quaternion()))
    return smooth((0.044 - distance) / 0.030) * smooth((alignment - 0.93) / 0.066)


def fitted_fingers(source, fits):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source))
    arm = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
    bpy.context.scene.frame_set(round(arm.animation_data.action.frame_range[0]))
    return {name: arm.pose.bones[name].matrix_basis.to_quaternion() @ Quaternion(value)
            for fit in fits for name, value in fit['offsets'].items()}


def bake(source, output, fits, attachment=None, ending_fits=None, stable_fingers=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source))
    arm = next(obj for obj in bpy.data.objects if obj.type == 'ARMATURE')
    bones = arm.pose.bones
    action = arm.animation_data.action
    first, last = map(round, action.frame_range)
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    scale = arm.matrix_world.to_scale().x
    samples = []
    for frame in range(first, last + 1):
        scene.frame_set(frame)
        samples.append({bone.name: bone.matrix.copy() for bone in bones})
    contacts = []
    for index, fit in enumerate(fits):
        side = {'L': 'Left', 'R': 'Right'}[fit['side']]
        limb = tuple(f'{side} {joint}' for joint in ('shoulder', 'arm', 'elbow', 'wrist'))
        _, _, lower, wrist = limb
        bind = bones[lower].bone.matrix_local.to_quaternion().inverted() @ bones[wrist].bone.matrix_local.to_quaternion()
        ending = ending_fits[index] if ending_fits else fit
        contacts.append((limb, fit['prop'], Matrix(fit['reference']),
                         (Matrix(fit['target']), Matrix(ending['target'])),
                         {name: (Quaternion(value), Quaternion(ending['offsets'][name]))
                          for name, value in fit['offsets'].items()}, bind))
    revised = bpy.data.actions.new(action.name + '_Contact')
    arm.animation_data.action = revised
    previous = {}
    maximum_miss = 0.0
    for index, matrices in enumerate(samples):
        time = index / fps
        progress = smooth(index / max(1, len(samples) - 1)) if ending_fits else 0.0
        if ending_fits and source.stem.endswith('_Reload'):
            remaining = (len(samples) - 1 - index) / fps
            progress = smooth(time / 0.25) * smooth(remaining / 0.25)
        rotations = {}
        for limb, prop_name, reference, targets, offsets, bind in contacts:
            collar, upper, lower, wrist = limb
            prop = matrices[prop_name]
            old_wrist = matrices[wrist]
            relative = prop.inverted() @ old_wrist
            weight = weight_for(time, attachment, relative, reference, prop, scale, source.stem, wrist)
            if not weight:
                continue
            target = Matrix.LocRotScale(targets[0].translation.lerp(targets[1].translation, progress),
                                        targets[0].to_quaternion().slerp(targets[1].to_quaternion(), progress),
                                        targets[0].to_scale())
            goal = prop @ target
            if not attachment and source.stem.endswith('_Reload') and wrist == 'Left wrist':
                goal = old_wrist @ reference.inverted() @ target
            position = old_wrist.translation.lerp(goal.translation, weight)
            if attachment and weight < 1.0:
                outward = (goal.translation - prop.translation).normalized()
                position += outward * (0.045 / scale) * math.sin(math.pi * weight)
            rotation = old_wrist.to_quaternion().slerp(goal.to_quaternion(), weight)
            goal = Matrix.LocRotScale(position, rotation, old_wrist.to_scale())
            solved = list(solve_arm(*(matrices[name] for name in limb), goal, scale))
            new_wrist = solved[-1]
            error = new_wrist.translation - goal.translation
            if attachment and weight == 1.0:
                # A free object follows the reaching hand, while seated endpoints stay on the authored track.
                carry = smooth((time - 1.03) / 0.19) * (1.0 - smooth((time - 3.32) / 0.30))
                prop = Matrix.Translation(error * carry) @ prop
                matrices[prop_name] = prop
                maximum_miss = max(maximum_miss, error.length * (1.0 - carry) * scale * 1000)
            axis, angle = roll_share(solved[2], new_wrist, bind)
            solved[2] = swing_about(solved[2].translation, Quaternion(axis, angle * weight)) @ solved[2]
            for name, matrix in zip(limb, solved):
                matrices[name] = matrix
            follow = new_wrist @ old_wrist.inverted()
            for child in bones[wrist].children_recursive:
                matrices[child.name] = follow @ matrices[child.name]
            rotations.update({name: (start.slerp(end, progress), weight) for name, (start, end) in offsets.items()})
        for bone in bones:
            matrix = matrices[bone.name]
            if bone.parent:
                local = bone.bone.convert_local_to_pose(matrix, bone.bone.matrix_local,
                                                       parent_matrix=matrices[bone.parent.name],
                                                       parent_matrix_local=bone.parent.bone.matrix_local, invert=True)
            else:
                local = bone.bone.convert_local_to_pose(matrix, bone.bone.matrix_local, invert=True)
            if adjustment := rotations.get(bone.name):
                offset, weight = adjustment
                location, rotation, unit = local.decompose()
                if stable_fingers:
                    start, end = (fingers[bone.name] for fingers in stable_fingers)
                    rotation = rotation.slerp(start.slerp(end, progress), weight)
                else:
                    rotation @= Quaternion().slerp(offset, weight)
                local = Matrix.LocRotScale(location, rotation, unit)
            bone.rotation_mode = 'QUATERNION'
            key_baked_pose(bone, local, first + index, previous)
    scene.frame_start, scene.frame_end = first, last
    scene.frame_set(first)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(output), use_selection=True, object_types={'ARMATURE'},
                             axis_forward='-Y', axis_up='Z', apply_unit_scale=True, add_leaf_bones=False,
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_simplify_factor=0.0, armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X')
    print('CONTACT_BAKE', source.stem, last - first + 1, 'attached_miss_mm', round(maximum_miss, 3), flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    stock, stage, profile_directory = map(Path, args[:3])
    model = args[3]
    options = dict(arg.split('=', 1) for arg in args[4:] if '=' in arg)
    def read_fits(stance):
        directory = profile_directory if stance == 'H' else profile_directory / stance
        return [json.loads((directory / f'contact_fit_{model}_{side}.json').read_text(encoding='utf-8'))
                for side in options.get('sides', 'R')]

    attachment = [float(value) for value in options['attach'].split(',')] if 'attach' in options else None
    references = {}
    if 'hold_fingers' in args[4:] and not attachment:
        for stance in 'HSA' if options.get('poses') == 'HSA' else 'H':
            suffix = '' if stance == 'H' else stance
            references[stance] = fitted_fingers(stock / f'AS_FPVM_{model}_Idle{suffix}.fbx', read_fits(stance))
    for clip in (arg for arg in args[4:] if '=' not in arg):
        if clip == 'hold_fingers':
            continue
        start, end = 'H', None
        if options.get('poses') == 'HSA':
            if clip.startswith('T_'):
                start, end = clip.removeprefix('T_')
            elif clip[-1] in 'AS':
                start = clip[-1]
        if clip == 'Reload' and options.get('reload') == 'fit':
            end = 'Reload'
        name = f'AS_FPVM_{model}_{clip}.fbx'
        stable_fingers = (references[start], references[end or start]) if references and end != 'Reload' else None
        bake(stock / name, stage / name, read_fits(start), attachment, read_fits(end) if end else None, stable_fingers)
