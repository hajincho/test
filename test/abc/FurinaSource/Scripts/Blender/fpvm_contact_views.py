"""Capture the contact surface from six fixed model-relative directions."""

import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from fpvm_lib import FINGERS


def triangles(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        faces = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
        return points, faces
    finally:
        evaluated.to_mesh_clear()


def owner_bone(obj):
    mass = {group.index: 0.0 for group in obj.vertex_groups}
    for vertex in obj.data.vertices:
        for group in vertex.groups:
            mass[group.group] += group.weight
    return obj.vertex_groups[max(mass, key=mass.get)].name if mass else None


def inspect_contacts(model, clip, output, arm, hand, props, dominant, goto, frame_range, sides, seconds, prop=None):
    measured = [obj for obj in props if not prop or owner_bone(obj) == prop]
    if not measured:
        raise ValueError(f'No mesh for {prop}')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = scene.render.resolution_y = 560
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    for obj in [hand, *props]:
        for material in obj.data.materials:
            if material:
                material.diffuse_color = ((0.80, 0.52, 0.39, 1) if obj == hand else
                                          (0.36, 0.48, 0.52, 1) if obj in measured and prop else
                                          (0.19, 0.22, 0.26, 1))
    camera = bpy.data.objects.new('Contact view', bpy.data.cameras.new('Contact view'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.clip_end = 4
    result = {'model': model, 'clip': clip, 'prop': prop, 'samples': []}
    first, last = frame_range
    for second in seconds:
        frame = min(last, max(first, first + round(second * fps)))
        goto(frame)
        hand_points, hand_faces = triangles(hand)
        surfaces = []
        for obj in measured:
            points, faces = triangles(obj)
            surfaces.append((obj.name, BVHTree.FromPolygons(points, faces, all_triangles=True)))
        gun = arm.matrix_world @ arm.pose.bones['VM_Gun'].matrix
        x, y, z = (Vector(gun.col[index][:3]).normalized() for index in range(3))
        views = {'left': (x, z), 'right': (-x, z), 'top': (z, -y), 'bottom': (-z, -y),
                 'front': (y, z), 'back': (-y, z)}
        row = {'frame': frame, 'seconds': round((frame - first) / fps, 4), 'hands': {}}
        for side in sides:
            wrist_name = {'L': 'Left wrist', 'R': 'Right wrist'}[side]
            regions = {index: name for index, name in dominant.items()
                       if name == wrist_name or name.endswith('_' + side) and name.startswith(tuple(FINGERS))}
            selected = [face for face in hand_faces if sum(index in regions for index in face) >= 2]
            skin = BVHTree.FromPolygons(hand_points, selected, all_triangles=True)
            detail = {}
            for name, surface in surfaces:
                crossing = {index for index, _ in skin.overlap(surface)}
                if crossing:
                    counts = {}
                    for index in crossing:
                        labels = [regions[vertex] for vertex in selected[index] if vertex in regions]
                        group = max(dict.fromkeys(labels), key=labels.count)
                        counts[group] = counts.get(group, 0) + 1
                    detail[name] = counts
            wrist = arm.matrix_world @ arm.pose.bones[wrist_name].matrix
            reference = arm.matrix_world @ arm.pose.bones[prop].matrix if prop else gun
            relative = reference.inverted() @ wrist
            if prop:
                center = reference.translation
                camera.data.ortho_scale = 0.38
            else:
                center = sum((hand_points[index] for index in regions), Vector()) / len(regions)
                camera.data.ortho_scale = 0.22
            captures = []
            for view, (direction, up) in views.items():
                right = up.cross(direction).normalized()
                mat = Matrix((right, direction.cross(right), direction)).transposed().to_4x4()
                mat.translation = center + direction * 0.8
                camera.matrix_world = mat
                name = f'{clip}_{frame:03d}_{side}_{view}.png'
                scene.render.filepath = str(output / name)
                bpy.ops.render.render(write_still=True)
                captures.append(name)
            row['hands'][side] = {'surface_crossings': detail, 'views': captures,
                                  'wrist_relative': [list(vec) for vec in relative]}
        result['samples'].append(row)
    (output / f'contact_review_{clip}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('CONTACT_REVIEW', clip, [row['frame'] for row in result['samples']])
