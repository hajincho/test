"""Relax the Kar98k viewmodel's support hand and reveal its left thumb."""

import json
import math
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import Graph, MATH, PAWN, STRINGS, wire
from lyra_fpvm_reload_wrists import ANIM, ASSETS, LOCAL, POSE, WORLD, around, key_count, moved, relative, write_tracks

FOLDER = '/Game/Furina/FPVM/Kar98k'
ASSET_TAG = 'Kar98kRelaxedSupport'
CLIPS = ('Idle', 'Fire', 'Reload', 'Loose1', 'Loose2', 'Loose3', 'Loose4')
ARM = ('Left-shoulder', 'Left-arm', 'Left-elbow', 'Left-wrist', 'zHandTwist_L', 'zArmTwist_L')
FINGERS = {f'{name}{joint}_L': relaxation for name in ('IndexFinger', 'MiddleFinger', 'RingFinger', 'LittleFinger')
           for joint, relaxation in ((1, .16), (2, .22), (3, .28))}
NAMES = (*ARM[1:], 'Thumb0_L', *FINGERS)
FINGER_GUIDES = {
    'IndexFinger': ((.32, .78, .53), (.85, -.22, .47), (.91, -.27, .08)),
    'MiddleFinger': ((.25, .65, .70), (.82, -.29, .50), (.89, -.36, .02)),
    'RingFinger': ((.17, .59, .78), (.78, -.34, .52), (.86, -.36, -.18)),
    'LittleFinger': ((.08, .65, .76), (.73, -.30, .60), (.88, -.32, -.14)),
}


def raw_options():
    options = unreal.AnimPoseEvaluationOptions()
    options.evaluation_type = unreal.AnimDataEvalType.RAW
    return options


def pose_at(animation, time, options):
    return POSE.get_anim_pose_at_time(animation, time, options)


def bone_pose(pose, name, space=WORLD):
    return POSE.get_bone_pose(pose, name, space)


def solve_support_arm(old, reach, rotation, forward):
    collar, upper, lower, wrist, hand_twist, arm_twist = old
    shoulder, elbow, old_end = (part.translation for part in (upper, lower, wrist))
    a, b = (elbow - shoulder).length(), (old_end - elbow).length()
    direction = (reach - shoulder).normal()
    distance = min(a + b - .15, max(abs(a-b) + .15, (reach - shoulder).length()))
    target = shoulder + direction * distance
    pole = elbow - shoulder
    pole = (pole - direction * direction.dot(pole)).normal()
    along = (a*a - b*b + distance*distance) / (2.*distance)
    new_elbow = shoulder + direction * along + pole * math.sqrt(max(0., a*a-along*along))
    upper_turn = (elbow - shoulder).find_quat_between_vectors(new_elbow - shoulder)
    lower_turn = (old_end - elbow).find_quat_between_vectors(target - new_elbow)
    axis = (target - new_elbow).normal()
    roll = math.radians(17.) * axis.dot(forward)
    revised_upper = moved(upper, shoulder, upper_turn * upper.rotation)
    revised_lower = moved(lower, new_elbow, around(axis, roll * .28) * lower_turn * lower.rotation)
    revised_wrist = moved(wrist, target, rotation)
    revised_hand_twist = moved(hand_twist, new_elbow + lower_turn.rotate_vector(hand_twist.translation - elbow),
                               around(axis, roll * .60) * lower_turn * hand_twist.rotation)
    revised_arm_twist = moved(arm_twist, shoulder + upper_turn.rotate_vector(arm_twist.translation - shoulder),
                              upper_turn * arm_twist.rotation)
    return (revised_upper, revised_lower, revised_wrist, revised_hand_twist, revised_arm_twist), (collar, revised_upper, revised_lower, revised_lower, revised_upper)


def support_tracks(animation, initial_gun):
    options = raw_options()
    result = {b: [] for b in NAMES}
    left_move = unreal.Vector(0., -1.05, .6)
    thumb_direction = unreal.Vector(3.9, -.35, 2.9)
    stock_contact = unreal.Vector(24., 8.8, -12.15) - initial_gun.translation
    furthest_wrist = 0.
    for frame in range(key_count(animation)):
        time = ANIM.get_time_at_frame(animation, frame)
        pose = pose_at(animation, time, options)
        gun = bone_pose(pose, 'VM_Gun')
        motion = gun.rotation * initial_gun.rotation.inversed()
        forward = motion.rotate_vector(unreal.Vector.FORWARD)
        base = gun.translation + motion.rotate_vector(stock_contact)
        old = [bone_pose(pose, n) for n in ARM]
        wrist = old[3]
        opening = around(forward, math.radians(17.))
        new_position = base + opening.rotate_vector(wrist.translation - base) + motion.rotate_vector(left_move)
        solved, parents = solve_support_arm(old, new_position, opening * wrist.rotation, forward)
        for bone, transform, parent in zip(ARM[1:], solved, parents):
            result[bone].append(relative(transform, parent, bone_pose(pose, bone, LOCAL).scale3d))

        new_wrist = solved[2]
        hand_turn = new_wrist.rotation * wrist.rotation.inversed()
        thumb = bone_pose(pose, 'Thumb0_L')
        tip = bone_pose(pose, 'Thumb2_L')
        thumb_origin = new_wrist.translation + hand_turn.rotate_vector(thumb.translation - wrist.translation)
        authored_direction = hand_turn.rotate_vector(tip.translation - thumb.translation)
        guide_rotation = authored_direction.find_quat_between_vectors(motion.rotate_vector(thumb_direction))
        guided_thumb = moved(thumb, thumb_origin, guide_rotation * hand_turn * thumb.rotation)
        result['Thumb0_L'].append(relative(guided_thumb, new_wrist, bone_pose(pose, 'Thumb0_L', LOCAL).scale3d))
        for name, value in FINGERS.items():
            key = bone_pose(pose, name, LOCAL)
            neutral = POSE.get_ref_bone_pose(pose, name, LOCAL)
            key.rotation = key.rotation.slerp_quat(neutral.rotation, value)
            result[name].append(key)

        furthest_wrist = max(furthest_wrist, (new_wrist.translation - wrist.translation).length())
        if frame:
            for keys in result.values():
                keys[-1].rotation = keys[-1].rotation.get_shortest_arc_to(keys[-2].rotation)
    return result, furthest_wrist


def keep_fingers_outside(animation, initial_gun):
    """Lay the other fingers on the far face without hiding the supporting thumb."""
    options = raw_options()
    result = {f'{finger}{joint}_L': [] for finger in FINGER_GUIDES for joint in (1, 2, 3)}
    inverse_initial = initial_gun.rotation.inversed()
    rest = pose_at(animation, 0., options)
    distal_axes = {}
    for finger in FINGER_GUIDES:
        joint, tip = [POSE.get_ref_bone_pose(rest, f'{finger}{index}_L', WORLD) for index in (2, 3)]
        distal_axes[finger] = tip.rotation.inversed().rotate_vector((tip.translation - joint.translation).normal())
    for frame in range(key_count(animation)):
        pose = pose_at(animation, ANIM.get_time_at_frame(animation, frame), options)
        orient = bone_pose(pose, 'VM_Gun').rotation * inverse_initial
        wrist = bone_pose(pose, 'Left-wrist')
        for finger, (proximal, middle, distal) in FINGER_GUIDES.items():
            names = [f'{finger}{joint}_L' for joint in (1, 2, 3)]
            base, second, tip = [bone_pose(pose, name) for name in names]
            first_dir = second.translation - base.translation
            first_target = orient.rotate_vector(unreal.Vector(*proximal)).normal()
            first_turn = first_dir.find_quat_between_vectors(first_target)
            adjusted_base = moved(base, base.translation, first_turn * base.rotation)
            key1 = relative(adjusted_base, wrist, bone_pose(pose, names[0], LOCAL).scale3d)
            next_dir = first_turn.rotate_vector(tip.translation - second.translation)
            next_target = orient.rotate_vector(unreal.Vector(*middle)).normal()
            next_turn = next_dir.find_quat_between_vectors(next_target)
            new_second = base.translation + first_target * first_dir.length()
            adjusted_second = moved(second, new_second, next_turn * first_turn * second.rotation)
            key2 = relative(adjusted_second, adjusted_base, bone_pose(pose, names[1], LOCAL).scale3d)
            tip_rotation = next_turn * first_turn * tip.rotation
            tip_target = orient.rotate_vector(unreal.Vector(*distal)).normal()
            final_turn = tip_rotation.rotate_vector(distal_axes[finger]).find_quat_between_vectors(tip_target)
            new_tip = new_second + next_target * next_dir.length()
            adjusted_tip = moved(tip, new_tip, final_turn * tip_rotation)
            key3 = relative(adjusted_tip, adjusted_second, bone_pose(pose, names[2], LOCAL).scale3d)
            for name, key in zip(names, (key1, key2, key3)):
                if result[name]:
                    key.rotation = key.rotation.get_shortest_arc_to(result[name][-1].rotation)
                result[name].append(key)
    return result


def pull_viewmodel():
    pawn = unreal.load_asset(PAWN)
    g = Graph(pawn, 'Kar98kGrip_')
    if 'Kar98kGrip_RestingPull' in g.nodes:
        return
    key = g.get('FurinaGameWeaponId')
    kar98k = g.call('IsKar98k', STRINGS + 'EqualEqual_StrStr', A=key, B='kar98k').find_result_pin()
    base = g.nodes['STC_BaseV'].find_input_pin('X')
    (previous,) = base.list_connected_pins()
    pull = g.call('RestingPull', MATH + 'SelectFloat', A=-6.7, B=previous, bPickA=kar98k)
    base.break_pin_links()
    wire(pull.find_result_pin(), base)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    assert ASSETS.save_loaded_asset(pawn, False)


def main():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    animations = {clip: unreal.load_asset(f'{FOLDER}/AS_FPVM_Kar98k_{clip}') for clip in CLIPS}
    anchor_gun = bone_pose(pose_at(animations['Idle'], 0., raw_options()), 'VM_Gun')
    results = {}
    for clip, animation in animations.items():
        applied = ASSETS.get_metadata_tag(animation, ASSET_TAG)
        if applied == '3':
            continue
        if applied not in ('1', '2'):
            tracks, wrist_delta = support_tracks(animation, anchor_gun)
            assert wrist_delta < 4., (clip, wrist_delta)
            write_tracks(animation, tracks)
        write_tracks(animation, keep_fingers_outside(animation, anchor_gun))
        ASSETS.set_metadata_tag(animation, ASSET_TAG, '3')
        assert ASSETS.save_loaded_asset(animation, False), clip
        results[clip] = {'frames': key_count(animation)}
    pull_viewmodel()
    path = Path(unreal.Paths.project_dir()).resolve() / 'Saved/FPVMReview/Kar98kGripSaved.json'
    path.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print('KAR98K_GRIP_SAVED', ', '.join(results))


if __name__ == '__main__':
    main()

