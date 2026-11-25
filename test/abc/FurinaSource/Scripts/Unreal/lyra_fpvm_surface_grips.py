"""Apply model-surface contact poses and rebalance the two SMG forearms."""

import json
import math
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_reload_wrists import (
    ANIM, ASSETS, LOCAL, POSE, WORLD, amount, angle, around, key_count, moved, relative, twist_angle, write_tracks,
)

ROOT = Path(unreal.Paths.project_dir()).resolve()
WORK = ROOT / 'Saved/FPVMReview/GripSurfaceWork'
PROFILE = ROOT / 'FurinaSource/Data/fpvm_hand_surface_fit.json'
FOLDER = '/Game/Furina/FPVM'
TAG = 'FPVMHandSurfaceFit'
VERSION = '2'
KAR_CLIPS = ('Idle', 'Fire', 'Reload', 'Loose1', 'Loose2', 'Loose3', 'Loose4')


def asset(family, clip):
    return unreal.load_asset(f'{FOLDER}/{family}/AS_FPVM_{family}_{clip}')


def pose(animation, time, options):
    return POSE.get_anim_pose_at_time(animation, time, options)


def bone(data, name, space=WORLD):
    return POSE.get_bone_pose(data, name, space)


def options():
    values = unreal.AnimPoseEvaluationOptions()
    values.evaluation_type = unreal.AnimDataEvalType.RAW
    return values


def each_pose(animation, settings):
    for frame in range(key_count(animation)):
        yield pose(animation, ANIM.get_time_at_frame(animation, frame), settings)


def receiver_weight(sample, idle, gun, weapon_turn):
    wrist = bone(sample, 'Left-wrist')
    origin = bone(idle, 'VM_Gun').translation
    initial = bone(idle, 'Left-wrist')
    expected = gun.translation + weapon_turn.rotate_vector(initial.translation - origin)
    separation = (expected - wrist.translation).length()
    rotation_error = math.degrees(wrist.rotation.angular_distance(weapon_turn * initial.rotation))
    return (1. - amount(separation, 2.2, 7.0)) * (1. - amount(rotation_error, 18., 48.))


def apply_fingers(animation, offsets, idle_contact=None):
    tracks = {n: [] for n in offsets}
    turns = {n: unreal.Quat(*q) for n, q in offsets.items()}
    inverse_gun = bone(idle_contact, 'VM_Gun').rotation.inversed() if idle_contact else None
    for frame in each_pose(animation, options()):
        weight = 1.
        if idle_contact:
            gun = bone(frame, 'VM_Gun')
            weight = receiver_weight(frame, idle_contact, gun, gun.rotation * inverse_gun)
        for name, offset in turns.items():
            key = bone(frame, name, LOCAL)
            key.rotation = (key.rotation * unreal.Quat.IDENTITY.slerp_quat(offset, weight)).normalized()
            tracks[name].append(key)
    write_tracks(animation, tracks)


def elbow_on_arc(upper, lower, wrist, target, palm, limit):
    base, elbow = upper.translation, lower.translation
    reach = target - base
    axis = reach.normal()
    upper_length = (base - elbow).length()
    lower_length = (elbow - wrist.translation).length()
    distance = min(upper_length + lower_length - .15,
                   max(abs(upper_length - lower_length) + .2, reach.length()))
    target = base + axis * distance
    from_shoulder = elbow - base
    radial = (from_shoulder - axis * from_shoulder.dot(axis)).normal()
    preferred = axis * palm.dot(axis) - palm
    swivel = 0.
    if not preferred.is_nearly_zero():
        preferred = preferred.normal()
        desired = math.atan2(axis.dot(radial.cross(preferred)), radial.dot(preferred))
        swivel = max(-limit, min(limit, desired)) * amount(1. + radial.dot(preferred), 0., .12)
    along = (distance**2 + upper_length**2 - lower_length**2) / (2. * distance)
    height = math.sqrt(max(0., upper_length**2 - along**2))
    revised = base + axis * along + around(axis, swivel).rotate_vector(radial) * height
    return revised, target


def solve_arm(upper, lower, wrist, hand_twist, upper_twist, want, hand_direction, bind, limit):
    start = upper.translation
    prior_elbow = lower.translation
    prior_wrist = wrist.translation
    elbow, end = elbow_on_arc(upper, lower, wrist, want.translation, hand_direction, limit)
    arm_swing = (prior_elbow - start).find_quat_between_vectors(elbow - start)
    fore_swing = (prior_wrist - prior_elbow).find_quat_between_vectors(end - elbow)
    axis = (end - elbow).normal()
    lower_rotation = fore_swing * lower.rotation
    remaining = twist_angle(want.rotation * (lower_rotation * bind).inversed(), axis)
    strength = amount(abs(math.degrees(remaining)), 24., 84.)
    shared = remaining * strength * .50
    upper_axis = (elbow - start).normal()
    shoulder_share = around(upper_axis, shared * .23)
    new_upper = moved(upper, start, shoulder_share * arm_swing * upper.rotation)
    new_lower = moved(lower, elbow, around(axis, shared) * lower_rotation)
    new_wrist = moved(wrist, end, want.rotation)
    new_hand_twist = moved(hand_twist, elbow + fore_swing.rotate_vector(hand_twist.translation - prior_elbow),
                           around(axis, shared * .65) * fore_swing * hand_twist.rotation)
    new_upper_twist = moved(upper_twist, start + arm_swing.rotate_vector(upper_twist.translation - start),
                            arm_swing * upper_twist.rotation)
    return new_upper, new_lower, new_wrist, new_hand_twist, new_upper_twist


def names(side, code):
    return (f'{side}-shoulder', f'{side}-arm', f'{side}-elbow', f'{side}-wrist',
            f'zHandTwist_{code}', f'zArmTwist_{code}', f'MiddleFinger1_{code}')


def change_smg(animation, idle, fitted, handheld):
    evaluation = options()
    initial_gun = bone(idle, 'VM_Gun')
    correction = unreal.Quat(*fitted['rotation'])
    shift = unreal.Vector(*fitted['position'])
    arms = [names('Left', 'L'), names('Right', 'R')]
    bind = {}
    for limb in arms:
        fore, hand = [POSE.get_ref_bone_pose(idle, name, WORLD).rotation for name in limb[2:4]]
        bind[limb[1]] = fore.inversed() * hand
    tracks = {n: [] for limb in arms for n in limb[1:6]}
    summary = {'max_bend_before': [0.,0.], 'max_bend_after': [0.,0.]}
    for sample in each_pose(animation, evaluation):
        gun = bone(sample, 'VM_Gun')
        weapon_turn = gun.rotation * initial_gun.rotation.inversed()
        for index, limb in enumerate(arms):
            collar, upper, lower, wrist, mid, upper_mid, knuckle = [bone(sample, n) for n in limb]
            hand_direction = knuckle.translation - wrist.translation
            want = wrist
            limit = math.radians(43.)
            if index == 0:
                # During reload, keep the authored moving prop and free-hand contacts.
                weight = 1. if handheld else receiver_weight(sample, idle, gun, weapon_turn)
                placement = wrist.translation + weapon_turn.rotate_vector(shift) * weight
                local_turn = weapon_turn * correction * weapon_turn.inversed()
                turn = unreal.Quat.IDENTITY.slerp_quat(local_turn, weight)
                want = moved(wrist, placement, turn * wrist.rotation)
                hand_direction = turn.rotate_vector(hand_direction)
                limit = math.radians(26. + 26. * weight)
            solved = solve_arm(upper, lower, wrist, mid, upper_mid, want, hand_direction, bind[limb[1]], limit)
            u,l,w,hm,um = solved
            original = knuckle.translation - wrist.translation
            for key, value in (('max_bend_before', angle(wrist.translation-lower.translation, original)),
                               ('max_bend_after', angle(w.translation-l.translation, hand_direction))):
                summary[key][index] = max(summary[key][index], round(math.degrees(value), 2))
            for name, world, parent in zip(limb[1:6], solved, (collar,u,l,l,u)):
                result = relative(world,parent,bone(sample,name,LOCAL).scale3d)
                history = tracks[name]
                if history:
                    result.rotation = result.rotation.get_shortest_arc_to(history[-1].rotation)
                history.append(result)
    write_tracks(animation, tracks)
    return summary


def mark_save(animation):
    ASSETS.set_metadata_tag(animation, TAG, VERSION)
    assert ASSETS.save_loaded_asset(animation, False), animation.get_name()


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    data = json.loads(PROFILE.read_text(encoding='utf-8'))
    path = WORK / 'AppliedGripFit.json'
    report = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    for clip in KAR_CLIPS:
        current = asset('Kar98k', clip)
        tag = ASSETS.get_metadata_tag(current, TAG)
        if tag == VERSION:
            continue
        if tag != '1':
            apply_fingers(current, data['Kar98k']['rotations'])
        clearance = data['Kar98k']['moving_clearance']['adjustments'].get(clip)
        if clearance:
            apply_fingers(current, clearance)
        mark_save(current)
        report[current.get_name()] = 'contact corrected'
    for family in ('MP38','MP40'):
        idle = pose(asset(family,'Idle'), 0., options())
        for clip in ('Idle','Fire','Reload'):
            current = asset(family, clip)
            tag = ASSETS.get_metadata_tag(current, TAG)
            if tag == VERSION:
                continue
            if tag != '1':
                report[current.get_name()] = change_smg(current, idle, data[family], clip != 'Reload')
            contact = pose(asset(family, 'Idle'), 0., options()) if clip == 'Reload' else None
            apply_fingers(current, data[family]['fingers']['rotations'], contact)
            mark_save(current)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('SURFACE_GRIPS_APPLIED',len(report))


if __name__ == '__main__':
    main()

