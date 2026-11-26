"""Build the PzB 39 game viewmodel from the existing mesh and Robin arm rig."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpvm_lib as rig
import fpvm_lib2 as pose


FPS = 30
FOLDER = Path(rig.D) / 'FBX/FPVM'
POLES = {'L': Vector((-.11, .16, -.22)), 'R': Vector((-.12, -.16, -.16))}
FINGER_LIMITS = {'Thumb': (25, 35, 28), 'default': (82, 90, 65)}
RELOAD_SECONDS = 3.15
REACH_SHAPE = {
    'Thumb': (12, 8, 4, -17), 'IndexFinger': (12, 9, 5, 8),
    'MiddleFinger': (23, 27, 17, 4), 'RingFinger': (31, 39, 23, -4),
    'LittleFinger': (38, 45, 32, -11),
}
PINCH_SHAPE = {
    'Thumb': (24, 24, 18, -5), 'IndexFinger': (32, 41, 29, 3),
    'MiddleFinger': (36, 45, 29, 2), 'RingFinger': (42, 51, 34, -3),
    'LittleFinger': (47, 55, 37, -5),
}


def delta(offset, pitch=0., roll=0.):
    return (Matrix.Translation(offset) @ Matrix.Rotation(math.radians(-pitch), 4, 'Y')
            @ Matrix.Rotation(math.radians(roll), 4, 'X'))


def smooth(value):
    alpha = min(1., max(0., value))
    return alpha * alpha * (3. - 2. * alpha)


def ramp(progress, start, end):
    return smooth((progress - start) / (end - start))


def shape_release(progress, original):
    approach = ramp(progress, .09, .34) * (1. - ramp(progress, .82, .98))
    pinch = ramp(progress, .34, .43) * (1. - ramp(progress, .74, .83))
    result = original.copy()
    for index, digit in enumerate(rig.FINGERS):
        joints = rig.fbones('R', digit)
        delayed = ramp(progress, .31 + .011 * index, .42 + .010 * index)
        close = min(pinch, delayed)
        for i, bone in enumerate(joints):
            opened = REACH_SHAPE[digit][i]
            grip = opened + (PINCH_SHAPE[digit][i] - opened) * close
            result[bone] = result[bone] * (1. - approach) + grip * approach
        spread = joints[0] + '@spread'
        opened, closed = REACH_SHAPE[digit][3], PINCH_SHAPE[digit][3]
        result[spread] = result.get(spread, 0.) * (1. - approach) + (opened + (closed - opened) * close) * approach
    return result


class CaseClearance:
    """Sample the deformed hand against the actual case panels."""

    def __init__(self, weapon, skin, placement):
        verts = [placement @ vertex.co for vertex in weapon.data.vertices]
        panels = {'Ammo_Case_Aged', 'Case_Fittings'}
        faces = [tuple(p.vertices) for p in weapon.data.polygons
                 if weapon.data.materials[p.material_index].name in panels]
        self.surface = BVHTree.FromPolygons(verts, faces)
        names = {'Right wrist', *(b for digit in rig.FINGERS for b in rig.fbones('R', digit))}
        groups = {group.index for group in skin.vertex_groups if group.name in names}
        right = [vertex.index for vertex in skin.data.vertices
                 if sum(g.weight for g in vertex.groups if g.group in groups) >= .52]
        self.indices = right[::max(1, len(right) // 125)]
        self.skin = skin
        self.depsgraph = bpy.context.evaluated_depsgraph_get()

    def correction(self, change, outside):
        import fpvm_grip
        evaluated = self.skin.evaluated_get(self.depsgraph)
        mesh = evaluated.to_mesh()
        to_case = change.inverted() @ self.skin.matrix_world
        worst = 0.
        for index in self.indices:
            point = to_case @ mesh.vertices[index].co
            distance = fpvm_grip.sdist(self.surface, point, near=.012, rng=.018)
            worst = max(worst, -distance)
        evaluated.to_mesh_clear()
        return outside * min(.031, worst + .003) if worst > .001 else Vector()


def export(name, skeletal_mesh):
    settings = dict(
        use_selection=True, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
        add_leaf_bones=False, armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X',
        bake_anim=not skeletal_mesh, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0., mesh_smooth_type='FACE', path_mode='STRIP',
    )
    bpy.ops.export_scene.fbx(filepath=str(FOLDER / (name + '.fbx')),
                            object_types={'ARMATURE', 'MESH'} if skeletal_mesh else {'ARMATURE'}, **settings)


def cartridge_groups(weapon):
    """Recover the ten authored display props as individually skinned islands."""
    mesh = bmesh.new()
    mesh.from_mesh(weapon.data)
    found = {}
    for material in ('Prop_Brass', 'Prop_Tip_Steel'):
        slot = weapon.data.materials.find(material)
        pending = {v for f in mesh.faces if f.material_index == slot for v in f.verts}
        groups = []
        while pending:
            start = pending.pop()
            vertices = [start]
            for vertex in vertices:
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in pending:
                        pending.remove(other)
                        vertices.append(other)
            middle = sum((v.co for v in vertices), Vector()) / len(vertices)
            groups.append((middle, {v.index for v in vertices}))
        assert len(groups) == 10, (material, len(groups))
        found[material] = sorted(groups, key=lambda item: item[0].z)
    result = []
    for (center, brass), (tip, steel) in zip(found['Prop_Brass'], found['Prop_Tip_Steel']):
        result.append((center, (center - tip).normalized(), brass | steel))
    mesh.free()
    return result


def layer_object(name, vertices, faces, material, matrix, uv_map):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = matrix
    uv = mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        uv.data[loop.index].uv = uv_map[loop.vertex_index]
    return obj


def round_template():
    """Resample the existing imported cartridge art for the ten in-game instances."""
    source = rig.load_weapon('ammo_7_92x94')
    all_vertices = np.array([v.co[:] for v in source.data.vertices])
    material_sets = [set() for _ in source.data.materials]
    for polygon in source.data.polygons:
        material_sets[polygon.material_index].update(polygon.vertices)
    mesh_vertices, mesh_faces, face_slots, uv_coordinates = [], [], [], []
    segments = 24
    materials = list(source.data.materials)
    for slot, ids in enumerate(material_sets):
        if not ids:
            continue
        points = all_vertices[list(ids)]
        low, high = points[:, 1].min(), points[:, 1].max()
        slices = np.linspace(low, high, 74 if slot == 0 else 44)
        bins = np.rint((points[:, 1] - low) / (high - low) * (len(slices) - 1)).astype(int)
        radii = np.zeros(len(slices))
        np.maximum.at(radii, bins, np.linalg.norm(points[:, (0, 2)], axis=1))
        occupied, = np.nonzero(radii)
        radii = np.interp(range(len(slices)), occupied, radii[occupied])
        start = len(mesh_vertices)
        first_face = len(mesh_faces)
        for ring, (along, radius) in enumerate(zip(slices, radii)):
            for index in range(segments):
                angle = index * math.tau / segments
                mesh_vertices.append((radius * math.cos(angle), along, radius * math.sin(angle)))
                uv_coordinates.append((index / segments, ring / (len(slices) - 1)))
        for ring in range(len(slices) - 1):
            for i in range(segments):
                a, b = start + ring*segments + i, start + ring*segments + (i+1)%segments
                mesh_faces.append((b, a, a + segments, b + segments))
        mesh_faces.append(tuple(start + i for i in range(segments)))
        end = start + (len(slices)-1)*segments
        mesh_faces.append(tuple(end + i for i in reversed(range(segments))))
        face_slots.extend([slot] * (len(mesh_faces) - first_face))
    data = bpy.data.meshes.new('Pzb39_CartridgeDisplay')
    data.from_pydata(mesh_vertices, [], mesh_faces)
    for material in materials:
        data.materials.append(material)
    uv = data.uv_layers.new(name='UVMap')
    for polygon, material in zip(data.polygons, face_slots):
        polygon.material_index = material
        polygon.use_smooth = len(polygon.vertices) == 4
        for loop_index in polygon.loop_indices:
            uv.data[loop_index].uv = uv_coordinates[data.loops[loop_index].vertex_index]
    limits = all_vertices[:, 1].min(), all_vertices[:, 1].max()
    bpy.data.objects.remove(source, do_unlink=True)
    return data, limits


def replica_round(template, bounds, center, axis, near, far, index, placement):
    length = (far - near) / float(bounds[1] - bounds[0])
    radial_scale = length * .90
    shift = center + axis * (far - bounds[1] * length)
    align = Vector((0, 1, 0)).rotation_difference(axis)
    step = Matrix.Translation(shift) @ align.to_matrix().to_4x4() @ Matrix.Diagonal(
        (radial_scale, length, radial_scale, 1.))
    part = bpy.data.objects.new(f'W_case_round_{index:02}', template.copy())
    bpy.context.scene.collection.objects.link(part)
    part.matrix_world = placement @ step
    end_radius = max(math.hypot(v.co.x, v.co.z) for v in template.vertices) * radial_scale
    return part, center + axis * far, end_radius


def remove_bundled_rounds(weapon):
    data = weapon.data
    mesh = bmesh.new()
    mesh.from_mesh(data)
    obsolete = {data.materials.find(name) for name in ('Prop_Brass', 'Prop_Tip_Steel')}
    bmesh.ops.delete(mesh, geom=[face for face in mesh.faces if face.material_index in obsolete], context='FACES')
    mesh.to_mesh(data)
    mesh.free()


def open_rear_notch(weapon, placement):
    """Replace the enclosed rear hoop with an open silhouette for the viewmodel."""
    mesh = bmesh.new()
    mesh.from_mesh(weapon.data)
    caps = weapon.data.materials.find('Barrel_Blued')
    outdated = [face for face in mesh.faces if face.material_index == caps and
                all(30.15 < v.co.y < 31.76 and v.co.z > 16.13 for v in face.verts)]
    points = [v.co.copy() for face in outdated for v in face.verts]
    assert points
    bmesh.ops.delete(mesh, geom=outdated, context='FACES')
    mesh.to_mesh(weapon.data)
    mesh.free()
    half = .97 * max(abs(v.x) for v in points)
    center_y = (min(v.y for v in points) + max(v.y for v in points)) * .5
    bottom = min(v.z for v in points) - .35
    profile = [(-1., 0.), (1., 0.), (1., 1.36), (.40, 1.36), (.32, .79),
               (.16, .61), (-.16, .61), (-.32, .79), (-.40, 1.36), (-1., 1.36)]
    vertices = [(x * half, center_y + y, bottom + z * half) for y in (-.28, .28) for x, z in profile]
    size = len(profile)
    faces = [tuple(range(size - 1, -1, -1)), tuple(range(size, 2 * size))]
    faces += [(i, (i+1) % size, (i+1) % size + size, i + size) for i in range(size)]
    notch = layer_object('W_game_rear_notch', vertices, faces, weapon.data.materials[caps], placement,
                         [(.42 + x*.08, .48 + z*.10) for _ in range(2) for x,z in profile])
    return notch, Vector((0., center_y, bottom + .80 * half))


def primer_cap(placement, mouth, axis, rim_radius, material, slot):
    radial_a = axis.cross(Vector((0, 0, 1))).normalized()
    radial_b = axis.cross(radial_a)
    radius = rim_radius * .43
    segments = 20
    rings = ((1., .014), (.82, .042), (.68, .047))
    vertices = []
    uvs = []
    for scale, height in rings:
        for index in range(segments):
            angle = index * math.tau / segments
            ux, uy = math.cos(angle) * scale, math.sin(angle) * scale
            vertices.append(mouth + axis*height + radius*(radial_a*ux + radial_b*uy))
            uvs.append((.5 + .34*ux, .5 + .34*uy))
    faces = [(row * segments + i, row * segments + (i + 1) % segments,
              (row + 1) * segments + (i + 1) % segments, (row + 1) * segments + i)
             for row in range(len(rings) - 1) for i in range(segments)]
    faces.append(tuple(range((len(rings) - 1) * segments, len(rings) * segments)))
    return layer_object(f'W_primer_{slot:02}', vertices, faces, material, placement, uvs)


def record_ads(placement, rear):
    back = placement @ rear
    front = placement @ Vector((0., -70.1, 17.462))
    turn = (front - back).normalized().rotation_difference(Vector((1., 0., 0.)))
    offset = Vector((back.x + .020, 0., -.004)) - turn @ back
    config = {'ue_loc_cm': [offset.x * 100, -offset.y * 100, offset.z * 100],
              'ue_quat_xyzw': [-turn.x, turn.y, -turn.z, turn.w]}
    path = Path(rig.D) / 'Data/pzb39_display_alignment.json'
    path.write_text(json.dumps(config, indent=2), encoding='utf-8')


def main():
    arm, skin, _ = rig.load_arms('a1')
    arm.name = 'Armature'
    pose.pose_clavicles(arm, {'L': [-10.73, 9.89, -16.11], 'R': [-17.46, -9.78, -17.09]})
    pose.fold_sleeves(arm)
    rig.bake_arms_rest(arm, [skin])
    for uv in list(skin.data.uv_layers)[1:]:
        skin.data.uv_layers.remove(uv)
    weapon = rig.load_weapon('pzb39')
    weapon.matrix_world = placement = rig.gun_native_to_cam((51., -8., -20.), 1.5, 0., -2.)
    notch, rear = open_rear_notch(weapon, placement)
    record_ads(placement, rear)
    bpy.context.view_layer.update()
    surface = pose.bvh_of([weapon, notch])
    case = CaseClearance(weapon, skin, placement)
    rig.add_bone(arm, 'VM_Gun', 'Hips', (0, 0, 0), (.10, 0, 0))
    rig.bind_rigid(arm, weapon, 'VM_Gun')
    rig.bind_rigid(arm, notch, 'VM_Gun')
    cartridge_bones = {}
    primers = []
    rounds = []
    primer_material = bpy.data.materials.new('Primer_Metal008')
    template, bounds = round_template()
    for index, (center, axis, vertices) in enumerate(cartridge_groups(weapon), 1):
        name = f'VM_Ammo_{index:02}'
        pivot = placement @ center
        rig.add_bone(arm, name, 'VM_Gun', pivot, pivot + Vector((.025, 0, 0)))
        extents = [(weapon.data.vertices[i].co - center).dot(axis) for i in vertices]
        end = max(extents)
        cartridge_bones[index] = (name, pivot, (placement.to_3x3() @ axis).normalized(), end * .01)
        round_mesh, mouth, radius = replica_round(template, bounds, center, axis, min(extents), end, index, placement)
        rig.bind_rigid(arm, round_mesh, name)
        rounds.append(round_mesh)
        primer = primer_cap(placement, mouth, axis, radius, primer_material, index)
        rig.bind_rigid(arm, primer, name)
        primers.append(primer)
    remove_bundled_rounds(weapon)
    targets = pose.setup_ik(arm)
    wrists, axes, digits, fingers = {}, {}, {}, {}
    diagnostics = {}
    for side, source, direction, forward, bias in (
        ('R', (-12., 44.2, -.5), (1., 0., 0.), (0., -.65, -.76), 1.5),
        ('L', (0., 20., -16.), (0., 0., 1.), (-.9, -.4, .02), 1.45),
    ):
        axes[side] = rig.hand_axes(arm, side)
        digits[side] = rig.finger_axes(arm, side, axes[side])
        hit, normal, _, _ = surface.ray_cast(placement @ Vector(source),
                                             (placement.to_3x3() @ Vector(direction)).normalized(), .26)
        assert hit is not None, side
        # Seat the actual skinned palm before computing contact for individual finger pads.
        toward = (placement.to_3x3() @ Vector(forward)).normalized()
        contact = hit - toward * (.003 if side == 'R' else .008)
        for pass_index in range(2):
            pose.place_hand(arm, targets, side, axes[side], contact, toward, -normal,
                            palm_off_cm=bias, elbow_hint_m=contact + POLES[side])
            if pass_index == 0:
                pose.calib_pole(arm, targets, side, targets['T_' + side].location.copy(), contact + POLES[side])
        diagnostics[side] = pose.seat_hand(arm, skin, targets, side, axes[side], surface, gap_cm=.10)
        fingers[side] = pose.grip_fingers(arm, side, digits[side], surface, r_cm=.50, limits=FINGER_LIMITS)
        wrist = arm.pose.bones[pose.SIDE[side] + ' wrist']
        wrists[side] = Matrix.LocRotScale(arm.matrix_world @ wrist.head,
                                         targets['T_' + side].rotation_quaternion, None)

    bones = arm.pose.bones
    gun_bind = bones['VM_Gun'].matrix.copy()
    constraints = [constraint for bone in bones for constraint in bone.constraints]
    for bone in bones:
        bone.rotation_mode = 'QUATERNION'

    scene = bpy.context.scene
    scene.render.fps = FPS
    arm.animation_data_create()
    clips = {}
    definitions = [('Idle', .20, None), ('Fire', .62, None), ('Reload', RELOAD_SECONDS, 10)]
    definitions.extend((f'ReloadR{count:02}', RELOAD_SECONDS, count) for count in range(1, 11))
    mesh_only = '--mesh-only' in sys.argv
    if mesh_only:
        definitions = definitions[:1]
    for name, duration, picked in definitions:
        frames = round(duration * FPS)
        samples = []
        arm.animation_data.action = None
        for constraint in constraints:
            constraint.mute = False
        for bone_name, *_ in cartridge_bones.values():
            bones[bone_name].matrix_basis = Matrix.Identity(4)
        for frame in range(frames + 1):
            progress = frame / frames
            relax = 0.
            change = Matrix.Identity(4)
            if name == 'Fire':
                time = frame / FPS
                impulse = (time / .065) * math.exp(1. - time / .065) * (1. - smooth((progress - .70) / .30))
                change = delta((-.032 * impulse, -.007 * impulse, .011 * impulse), 4.0 * impulse, -2.0 * impulse)
            if picked is not None:
                lowered = ramp(progress, .02, .23) * (1. - ramp(progress, .86, 1.))
                relax = ramp(progress, .11, .34) * (1. - ramp(progress, .81, .98))
                settle = ramp(progress, .62, .80) * (1. - ramp(progress, .82, .94))
                change = delta((.060 * lowered, .045 * lowered, -.026 * lowered),
                               7. * lowered, 16. * lowered - 7. * settle)
            bones['VM_Gun'].matrix = change @ gun_bind
            active = cartridge_bones[picked] if picked is not None else None
            item_motion = None
            if active:
                item_bone = bones[active[0]]
                item_bone.matrix_basis = Matrix.Identity(4)
                bpy.context.view_layer.update()
                stored = item_bone.matrix.copy()
                pivot, axis, end = active[1:]
                withdraw = ramp(progress, .43, .58)
                pass_over = ramp(progress, .58, .78)
                release = ramp(progress, .78, .82)
                removed = change @ (pivot + axis * (.125 * withdraw) + Vector((.08, .145, .100)) * pass_over)
                if progress >= .82:
                    item_bone.matrix = Matrix.Translation(Vector((0., 0., -.65))) @ stored
                elif withdraw:
                    offset = removed - stored.translation + Vector((0., 0., -.65)) * release
                    show_profile = Quaternion((0, 0, 1), -.42 * ramp(progress, .57, .72)).to_matrix().to_4x4()
                    item_motion = Matrix.Translation(stored.translation + offset) @ show_profile
                    item_motion @= Matrix.Translation(-stored.translation) @ stored
                    item_bone.matrix = item_motion
            for side in 'RL':
                wrist = change @ wrists[side]
                opened = relax if side == 'R' else 0.
                if opened:
                    hand_forward = wrists[side].to_quaternion() @ axes[side]['f_local']
                    arc = math.sin(opened * math.pi)
                    # Clear the side of the sight on both the reach and return.
                    low_slot = (10 - picked) / 9.
                    take = removed - (change.to_quaternion() @ hand_forward) * .070
                    take += Vector((-.010, -.042 - .015 * low_slot, .040 + .012 * low_slot))
                    wrist.translation = wrist.translation.lerp(take, opened) + Vector((-.025, -.045, .041)) * arc
                    wrist = Matrix.LocRotScale(wrist.translation,
                                               Quaternion((1, 0, 0), .62 * opened) @ wrist.to_quaternion(), None)
                target = targets['T_' + side]
                target.location = wrist.translation
                target.rotation_quaternion = wrist.to_quaternion()
                targets['P_' + side].location = wrist.translation + POLES[side]
                pose.settle_wrist(arm, targets, side, wrist.translation)
                shape = shape_release(progress, fingers[side]) if side == 'R' and active else fingers[side]
                pose.apply_fingers(arm, digits[side], shape)
                if side == 'R' and active and .22 < progress < .90:
                    bpy.context.view_layer.update()
                    # The pickup reaches the case first. Once lifted, tie the
                    # displayed prop to the thumb/index pinch through the carry.
                    end_on_case = change.to_3x3() @ axis
                    contact = removed + end_on_case * (end - .004)
                    grip_weight = ramp(progress, .29, .43) * (1. - ramp(progress, .77, .85))

                    def pinch_point():
                        thumb = bones['Thumb2_R']
                        index = bones['IndexFinger3_R']
                        point = thumb.head.lerp(thumb.tail, .60).lerp(index.head.lerp(index.tail, .60), .50)
                        return arm.matrix_world @ point

                    error = (contact - pinch_point()) * grip_weight
                    refined = wrist.translation + error
                    target.location += error
                    targets['P_R'].location += error
                    pose.settle_wrist(arm, targets, side, refined, relax_arm=False)
                    for _ in range(3):
                        bpy.context.view_layer.update()
                        clearance = case.correction(change, end_on_case)
                        if clearance.length < .001:
                            break
                        refined += clearance
                        target.location += clearance
                        targets['P_R'].location += clearance
                        pose.settle_wrist(arm, targets, side, refined, relax_arm=False)
                    if item_motion is not None:
                        carry = ramp(progress, .46, .56) * (1. - ramp(progress, .78, .82))
                        separation = (pinch_point() - contact) * carry
                        item_bone.matrix = Matrix.Translation(separation) @ item_motion
            bpy.context.view_layer.update()
            samples.append({bone.name: arm.convert_space(pose_bone=bone, matrix=bone.matrix,
                                                         from_space='POSE', to_space='LOCAL').copy()
                            for bone in bones})
        for constraint in constraints:
            constraint.mute = True
        action = bpy.data.actions.new('PZB39_' + name)
        arm.animation_data.action = action
        previous = {}
        for index, sample in enumerate(samples, 1):
            for bone in bones:
                pose.key_baked_pose(bone, sample[bone.name], index, previous)
        clips[name] = action, frames + 1
    for bone in bones:
        for constraint in list(bone.constraints):
            bone.constraints.remove(constraint)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = arm
    arm.animation_data.action = clips['Idle'][0]
    scene.frame_set(1)
    for obj in (arm, skin, weapon, notch, *rounds, *primers):
        obj.select_set(True)
    export('SK_FPVM_PZB39', True)
    if mesh_only:
        return
    for obj in (skin, weapon, notch, *rounds, *primers):
        obj.select_set(False)
    for name, (action, last) in clips.items():
        arm.animation_data.action = action
        scene.frame_start, scene.frame_end = 1, last
        export('AS_FPVM_PZB39_' + name, False)
    work = Path(rig.D).parent / 'Saved'
    (work / 'Pzb39Grip.json').write_text(json.dumps(diagnostics, indent=2, default=str), encoding='utf-8')
    print('PZB39_FBX_COMPLETE')


if __name__ == '__main__':
    main()
