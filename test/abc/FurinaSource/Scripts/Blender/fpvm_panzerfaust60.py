"""Fit the supplied Panzerfaust game prop to the existing viewmodel rig."""
from pathlib import Path

import bpy
from mathutils import Matrix


def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    return result


def load_panzerfaust60(source, muzzle, rear, axis_height):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(Path(source)))
    imported = set(bpy.data.objects) - before
    by_name = {obj.name: obj for obj in imported}
    shaft = by_name['tube1']
    ring = by_name['в5']
    shell = by_name['patrone']
    raised_sight = by_name['d33']
    reference_pose = shaft.matrix_world @ by_name['tube'].matrix_world.inverted()
    shaft_bounds = [shaft.matrix_world @ vert.co for vert in shaft.data.vertices]
    front = max(v.x for v in shaft_bounds)
    back = min((ring.matrix_world @ vert.co).x for vert in ring.data.vertices)
    lateral = (min(v.y for v in shaft_bounds) + max(v.y for v in shaft_bounds)) / 2
    height = (min(v.z for v in shaft_bounds) + max(v.z for v in shaft_bounds)) / 2
    size = (rear - muzzle) / (front - back)
    fit = Matrix(((0, size, 0, -size * lateral),
                  (-size, 0, 0, muzzle + size * front),
                  (0, 0, size, axis_height - size * height),
                  (0, 0, 0, 1)))

    tube_parts = [shaft, ring, *(by_name[key] for key in ('spring', 'd1', 'd2', 'd4', 'pin', 'circle'))]
    components = tube_parts + [shell, raised_sight]
    for obj in imported - set(components):
        bpy.data.objects.remove(obj, do_unlink=True)
    for obj in components:
        reference = reference_pose if obj is raised_sight else Matrix.Identity(4)
        transform = fit @ reference @ obj.matrix_world
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        obj.data = obj.data.copy()
        obj.data.transform(transform)
        for material in obj.data.materials:
            if material:
                material.name = 'Panzerfaust60Surface'
    shell.name = 'W_Panzerfaust60_Head'
    raised_sight.name = 'W_Panzerfaust60_Sight'
    return join(tube_parts, 'W_Panzerfaust60_Tube'), shell, raised_sight

