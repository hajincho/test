"""Repair attachment display and baked arm poses on the first-person weapon rig."""

import json
import math
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_optics import Graph, MATH, PAWN, wire

ASSETS = unreal.EditorAssetLibrary
ANIM = unreal.AnimationLibrary
POSE = unreal.AnimPoseExtensions
WORLD = unreal.AnimPoseSpaces.WORLD
LOCAL = unreal.AnimPoseSpaces.LOCAL
FOLDER = '/Game/Furina/FPVM'
TAG = 'FPVMForearmCorrection'
VERSION = '1'
CLIP_MATERIALS = {'Clip_Steel', 'Clip_Projectile', 'Clip_Case'}
ROCKET_RELOAD = 'AS_FPVM_PANZERSCHRECK_Reload'
MAG_RELOAD = 'AS_FPVM_G43_MagReload'


def key_count(animation):
    return ANIM.get_num_keys(animation)


def write_tracks(animation, tracks):
    controller = animation.controller
    controller.open_bracket('Correct first-person arm and prop tracks', False)
    try:
        for bone, transforms in tracks.items():
            assert controller.set_bone_track_keys(
                bone, [p.translation for p in transforms], [p.rotation for p in transforms],
                [p.scale3d for p in transforms], False), (animation.get_name(), bone)
    finally:
        controller.close_bracket(False)


def normalize_prop_tracks(animation):
    """FBX normalizes scale to the first frame, even when that frame hides a prop."""
    name = animation.get_name()
    if name == ROCKET_RELOAD:
        bone = 'VM_Rocket'
    elif name == MAG_RELOAD:
        bone = 'VM_Clip'
    else:
        return False
    keys = []
    for frame in range(key_count(animation)):
        original = ANIM.get_bone_pose_for_frame(animation, bone, frame, False)
        time = ANIM.get_time_at_frame(animation, frame)
        scale = 1.0 if name == ROCKET_RELOAD and time >= 2.05 else .001
        original.scale3d = unreal.Vector(scale, scale, scale)
        keys.append(original)
    write_tracks(animation, {bone: keys})
    return True


def angle(a, b):
    return math.acos(max(-1.0, min(1.0, a.normal().dot(b.normal()))))


def amount(value, low, high):
    weight = min(1., max(0., (value - low) / (high - low)))
    return weight * weight * (3. - 2. * weight)


def around(axis, radians):
    half = radians * .5
    vec = axis.normal() * math.sin(half)
    return unreal.Quat(vec.x, vec.y, vec.z, math.cos(half))


def twist_angle(rotation, axis):
    signed = unreal.Vector(rotation.x, rotation.y, rotation.z).dot(axis)
    return math.atan2(2 * rotation.w * signed, rotation.w**2 - signed**2)


def moved(transform, position, rotation):
    value = transform.copy()
    value.translation = position
    value.rotation = rotation.normalized()
    return value


def relative(transform, parent, local_scale):
    value = moved(transform, parent.inverse_transform_location(transform.translation),
                  parent.rotation.inversed() * transform.rotation)
    value.scale3d = local_scale
    return value


def bones_for(label, side):
    return (f'{label}-shoulder', f'{label}-arm', f'{label}-elbow', f'{label}-wrist',
            f'zHandTwist_{side}', f'zArmTwist_{side}', f'MiddleFinger1_{side}')


def rig_definition(pose):
    present = {str(b).lower() for b in POSE.get_bone_names(pose)}
    limbs = []
    for label, side in (('Left', 'L'), ('Right', 'R')):
        names = bones_for(label, side)
        if all(b.lower() in present for b in names):
            ref_elbow, ref_wrist, ref_twist = [POSE.get_ref_bone_pose(pose, n, WORLD) for n in names[2:5]]
            neutral = ref_elbow.rotation.inversed()
            limbs.append((names, neutral * ref_wrist.rotation, neutral * ref_twist.rotation))
    return limbs


def relax_palm(shoulder, elbow, palm, hand, rotation, upper_length, forearm_length):
    forearm_dir = (palm - elbow).normal()
    bend = angle(forearm_dir, hand)
    strength = amount(math.degrees(bend), 57., 92.)
    pivot = palm + hand * .56
    if strength == 0.:
        return elbow, palm, rotation, hand, pivot
    correction = min(math.radians(39.) * strength, bend - math.radians(55.))
    rotate = around(hand.normal().cross(forearm_dir), correction)
    new_palm = pivot + rotate.rotate_vector(palm - pivot)
    reach = new_palm - shoulder
    distance = reach.length()
    if not abs(upper_length - forearm_length) < distance < upper_length + forearm_length:
        return elbow, palm, rotation, hand, pivot
    axis = reach.normal()
    radial = elbow - shoulder
    radial = (radial - axis * axis.dot(radial)).normal()
    advance = (distance**2 + upper_length**2 - forearm_length**2) / (2. * distance)
    height = math.sqrt(max(0., upper_length**2 - advance**2))
    new_elbow = shoulder + axis * advance + radial * height
    new_hand = rotate.rotate_vector(hand)
    if angle(new_palm - new_elbow, new_hand) >= bend:
        return elbow, palm, rotation, hand, pivot
    return new_elbow, new_palm, rotate * rotation, new_hand, pivot


def solve_arm(upper, forearm, wrist, hand_twist, arm_twist, palm_direction, bind, neutral_twist, previous_roll):
    shoulder, elbow, palm = upper.translation, forearm.translation, wrist.translation
    chord = (palm - shoulder).normal()
    lower_axis = (palm - elbow).normal()
    bend_before = angle(lower_axis, palm_direction)
    radial = elbow - shoulder
    radial = radial - chord * radial.dot(chord)
    facing = palm_direction - chord * palm_direction.dot(chord)
    shift = 0.0
    if not radial.is_nearly_zero() and not facing.is_nearly_zero():
        preferred = facing.normal().negated()
        direction = radial.normal()
        desired = math.atan2(chord.dot(direction.cross(preferred)), direction.dot(preferred))
        limit = math.radians(57) * amount(math.degrees(bend_before), 39., 80.)
        # A facing reversal should not flip the elbow to the other side in a single frame.
        shift = max(-limit, min(limit, desired)) * amount(1. + direction.dot(preferred), 0., .14)
    arc = around(chord, shift)
    new_elbow = shoulder + arc.rotate_vector(elbow - shoulder)
    new_elbow, new_palm, palm_rotation, hand, contact = relax_palm(
        shoulder, new_elbow, palm, palm_direction, wrist.rotation, (elbow - shoulder).length(), (palm - elbow).length())
    upper_dir = (new_elbow - shoulder).normal()
    forearm_dir = (new_palm - new_elbow).normal()
    upper_swing = (elbow - shoulder).find_quat_between_vectors(new_elbow - shoulder)
    forearm_swing = (palm - elbow).find_quat_between_vectors(new_palm - new_elbow)
    elbow_rotation = forearm_swing * forearm.rotation

    # Separate roll from the bend, then share roll with the forearm and its twist bone.
    delta = palm_rotation * (elbow_rotation * bind).inversed()
    roll = twist_angle(delta, forearm_dir)
    if previous_roll is not None:
        roll = previous_roll + math.remainder(roll - previous_roll, 2. * math.pi)
    active_roll = max(-math.pi, min(math.pi, roll))
    weight = amount(abs(math.degrees(active_roll)), 35., 95.)
    forearm_roll = active_roll * .58 * weight
    hand_twist_roll = active_roll * .81 * weight
    upper_roll = active_roll * .16 * weight * max(0., upper_dir.dot(forearm_dir) * .5 + .5)
    upper_revised = moved(upper, shoulder, around(upper_dir, upper_roll) * upper_swing * upper.rotation)
    lower_revised = moved(forearm, new_elbow, around(forearm_dir, forearm_roll) * elbow_rotation)
    authored_twist = forearm_swing * hand_twist.rotation
    spread_twist = around(forearm_dir, hand_twist_roll) * elbow_rotation * neutral_twist
    hand_revised = moved(hand_twist,
                         new_elbow + forearm_swing.rotate_vector(hand_twist.translation - elbow),
                         authored_twist.slerp_quat(spread_twist, weight))
    arm_revised = moved(arm_twist, shoulder + upper_swing.rotate_vector(arm_twist.translation - shoulder),
                        around(upper_dir, upper_roll * .55) * upper_swing * arm_twist.rotation)

    bend_after = angle(forearm_dir, hand)
    wrist_revised = moved(wrist, new_palm, palm_rotation)
    # The center of the palm stays on the grip when a severe bend needs hand rotation.
    grip_error = (new_palm + hand * .56 - contact).length()
    return (upper_revised, lower_revised, wrist_revised, hand_revised, arm_revised,
            roll, (math.degrees(bend_before), math.degrees(bend_after),
                   abs(math.degrees(active_roll)), abs(math.degrees(active_roll - forearm_roll)),
                   abs(math.degrees(active_roll - hand_twist_roll)), grip_error))


def correct_arms(animation, *, persist=True):
    options = unreal.AnimPoseEvaluationOptions()
    options.evaluation_type = unreal.AnimDataEvalType.RAW
    sample = POSE.get_anim_pose_at_time(animation, 0., options)
    limbs = rig_definition(sample)
    if not limbs:
        return None
    tracks = {name: [] for names, _, _ in limbs for name in names[1:6]}
    report = {'frames': key_count(animation), 'roll_before': 0., 'roll_after': 0.,
              'roll_at_twist_bone': 0., 'bend_before': 0., 'bend_after': 0., 'grip_location_error': 0.}
    previous = [None] * len(limbs)
    for frame in range(key_count(animation)):
        time = min(animation.get_play_length(), ANIM.get_time_at_frame(animation, frame))
        pose = POSE.get_anim_pose_at_time(animation, time, options)
        for index, (names, bind, neutral_twist) in enumerate(limbs):
            collar, upper, elbow, wrist, hand_twist, arm_twist, knuckle = [POSE.get_bone_pose(pose, n, WORLD) for n in names]
            solved = solve_arm(upper, elbow, wrist, hand_twist, arm_twist,
                               knuckle.translation - wrist.translation, bind, neutral_twist, previous[index])
            new_upper, new_elbow, new_wrist, hand, arm, previous[index], values = solved
            for name, world, parent in zip(names[1:6], (new_upper, new_elbow, new_wrist, hand, arm),
                                           (collar, new_upper, new_elbow, new_elbow, new_upper)):
                existing = POSE.get_bone_pose(pose, name, LOCAL)
                result = relative(world, parent, existing.scale3d)
                if tracks[name]:
                    result.rotation = result.rotation.get_shortest_arc_to(tracks[name][-1].rotation)
                tracks[name].append(result)
            reconstructed = new_elbow.transform_location(tracks[names[3]][-1].translation)
            report['grip_location_error'] = max(report['grip_location_error'], values[-1],
                                                (reconstructed - new_wrist.translation).length())
            for k, value in zip(('bend_before', 'bend_after', 'roll_before', 'roll_after', 'roll_at_twist_bone'), values):
                report[k] = max(report[k], round(value, 2))

    if persist and (report['roll_before'] > 36. or report['bend_before'] > 40.):
        assert report['grip_location_error'] < .05, report
        write_tracks(animation, tracks)
        ASSETS.set_metadata_tag(animation, TAG, VERSION)
        assert ASSETS.save_loaded_asset(animation, False), animation.get_name()
        report['saved'] = True
    return report


def mask_scoped_clip():
    mesh = unreal.load_asset(FOLDER + '/G43/SK_FPVM_G43_ZF4')
    mask = unreal.load_asset(FOLDER + '/M_FPVM_HiddenClip')
    assert mask
    slots = []
    changed = set()
    for slot in mesh.materials:
        name = str(slot.material_slot_name)
        if name in CLIP_MATERIALS:
            slot.material_interface = mask
            changed.add(name)
        slots.append(slot)
    assert changed == CLIP_MATERIALS, changed
    mesh.set_editor_property('materials', slots)
    assert all(slot.material_interface == mask for slot in mesh.materials if str(slot.material_slot_name) in CLIP_MATERIALS)
    assert ASSETS.save_loaded_asset(mesh, False)


def lower_scoped_rifle():
    pawn = unreal.load_asset(PAWN)
    graph = Graph(pawn, 'ZF4ReloadView_')
    active = graph.nodes.get('ZF4ReloadView_ReloadingScoped')
    if active is None:
        active = graph.call('ReloadingScoped', MATH + 'BooleanAND',
                            A=graph.nodes['STC_IsZF4'].find_result_pin(),
                            B=graph.get('FurinaReloading'))
        interp = graph.locate('VM_AdsI_').find_input_pin('Target')
        (original,) = interp.list_connected_pins()
        revised = graph.call('ReloadTarget', MATH + 'SelectFloat', A=0., B=original, bPickA=active.find_result_pin())
        interp.break_pin_links()
        wire(revised.find_result_pin(), interp)
    if 'ZF4ReloadView_ReloadFOV' not in graph.nodes:
        camera = graph.nodes['ScopeView_SetCamera'].find_input_pin('InFieldOfView')
        (aim_fov,) = camera.list_connected_pins()
        normal_fov = float(graph.nodes['ScopeView_StandardFOV'].find_input_pin('B').get_pin_value())
        wide = graph.call('ReloadFOV', MATH + 'SelectFloat', A=normal_fov, B=aim_fov, bPickA=active.find_result_pin())
        camera.break_pin_links()
        wire(wide.find_result_pin(), camera)
    unreal.BlueprintEditorLibrary.compile_blueprint(pawn)
    assert pawn.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR
    defaults = unreal.get_default_object(pawn.generated_class())
    offsets = defaults.get_editor_property('FurinaRlOfs')
    offsets['g43_zf4'] = unreal.Vector(19., 0., -5.)
    defaults.set_editor_property('FurinaRlOfs', offsets)
    assert ASSETS.save_loaded_asset(pawn, False)


def main():
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not subsystem.get_game_world(), 'Exit PIE before changing animation assets'
    mask_scoped_clip()
    lower_scoped_rifle()
    for family, name in (('G43', MAG_RELOAD), ('PANZERSCHRECK', ROCKET_RELOAD)):
        animation = unreal.load_asset(f'{FOLDER}/{family}/{name}')
        assert normalize_prop_tracks(animation)
        assert ASSETS.save_loaded_asset(animation, False)
    output = Path(unreal.Paths.project_dir()).resolve() / 'Saved/FPVMReview/WristReloadRepairs.json'
    report = {}
    for path in sorted(ASSETS.list_assets(FOLDER, True, False)):
        name = path.rsplit('/', 1)[-1].split('.', 1)[0]
        if not name.startswith('AS_FPVM_'):
            continue
        sequence = unreal.load_asset(path)
        if not isinstance(sequence, unreal.AnimSequence) or ASSETS.get_metadata_tag(sequence, TAG) == VERSION:
            continue
        result = correct_arms(sequence)
        if result is not None:
            report[name] = result
            output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('FPVM_RELOAD_WRIST_SAVED', sum(bool(r.get('saved')) for r in report.values()), len(report))


if __name__ == '__main__':
    main()

