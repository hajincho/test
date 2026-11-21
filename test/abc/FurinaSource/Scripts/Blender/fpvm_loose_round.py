"""Author loose-round game animation variants with the existing rifle rigs."""
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def mix_pose(a, b, t):
    location_a, rotation_a, scale_a = a.decompose()
    location_b, rotation_b, scale_b = b.decompose()
    return Matrix.LocRotScale(location_a.lerp(location_b, t), rotation_a.slerp(rotation_b, t), scale_a.lerp(scale_b, t))


def phase(t, a, b):
    f = min(1., max(0., (t - a) / (b - a)))
    return f * f * (3 - 2 * f)


def build_timeline(base, gun_ref, clip_anchor, amount, opening, closing, duration):
    edge = base(opening - .001)
    pouch = edge['Cw']
    open_hand = 'R_BOLT' if 'theta' in edge else 'R_GRIP'
    cycle_duration = .63
    insert_end = opening + cycle_duration * amount
    total = insert_end + duration - closing

    def animation(t):
        if t < opening:
            state = base(t)
            state['clip_vis'] = 0
        elif t < insert_end:
            state = dict(edge)
            beat = (t - opening) % cycle_duration
            move = phase(beat, .0, .38) * (1 - phase(beat, .44, .62))
            gun = state['D'] @ gun_ref
            destination = gun @ Matrix.Translation(Vector(clip_anchor) + Vector((0, 0, 1.35 * (1 - phase(beat, .28, .42)))))
            state['Cw'] = mix_pose(pouch, destination, move)
            state['Ch'] = state['Cw']
            state['R'] = ('R_CLIP', 'R_CLIP', 0, 0)
            state['clip_vis'] = .08 <= beat < .44
        else:
            tail = min(duration, closing + t - insert_end)
            state = base(tail)
            state['clip_vis'] = 0
            if t - insert_end < .24:
                state['R'] = ('R_POUCH', open_hand, phase(t - insert_end, 0, .24), 2.)
        state['push'] = 0
        state['rounds_vis'] = 0
        return state

    return animation, total


def one_clip(base):
    # The first authored G43 clip sequence, followed by the original recovery.
    def animation(t):
        if t < 2.49:
            return base(t)
        if t < 2.79:
            state = base(2.49)
            state['clip_vis'] = False
            state['rounds_vis'] = False
            state['R'] = ('R_CLIP', 'R_GRIP', phase(t, 2.49, 2.79), 2.)
            return state
        return base(min(5.9, 4.85 + (t - 2.79)))
    return animation, 3.84


def export_animations(directory, model, armature, controls, clips, bake, fps):
    bpy.context.scene.render.fps = fps
    bpy.context.scene.render.fps_base = 1.
    actions = {}
    for name, (animation, duration) in clips.items():
        action, frames = bake(name, animation, duration)
        actions[name] = (action, frames)
    for bone in armature.pose.bones:
        for constraint in list(bone.constraints):
            bone.constraints.remove(constraint)
    for control in controls.values():
        bpy.data.objects.remove(control)
    for name, (action, _) in actions.items():
        armature.animation_data.action = action
        start, end = action.frame_range
        bpy.context.scene.frame_start = round(start)
        bpy.context.scene.frame_end = round(end)
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        path = Path(directory) / 'FBX' / 'FPVM' / f'AS_FPVM_{model}_{name}.fbx'
        bpy.ops.export_scene.fbx(
            filepath=str(path), use_selection=True, object_types={'ARMATURE'},
            axis_forward='-Y', axis_up='Z', apply_unit_scale=True, add_leaf_bones=False,
            bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.,
            armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X',
        )
