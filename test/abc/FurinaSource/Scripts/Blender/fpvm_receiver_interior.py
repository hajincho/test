"""Build an opaque lining for the existing receiver meshes used in first person."""
from pathlib import Path
import math

import bmesh
import bpy

from fpvm_lib import bind_rigid, load_weapon
from fpvm_scope_joinery import attach_surfaces, finish_surfaces


def add_receiver_interior(name, armature, native_to_camera):
    # Coordinates are in the imported model's local scene space. Keep the lip
    # below the existing shell so the original opening and silhouette remain.
    profiles = {
        'Kar98k': (5.45, 19.55, ((-.66, 6.36), (-.30, 5.76), (1.60, 5.76), (1.96, 6.36))),
        'G43': (-.90, 10.20, ((-1.13, 6.42), (-.76, 5.52), (.76, 5.52), (1.13, 6.42))),
    }
    front, back, profile = profiles[name]
    vertices = [(x, depth, height) for depth in (front, back) for x, height in profile]
    # Top-facing floor, inward-facing walls, and caps recessed under the rims.
    faces = [(i, i + 1, i + 5, i + 4) for i in range(3)]
    faces += [(3, 2, 1, 0), (4, 5, 6, 7)]
    if name == 'Kar98k':
        # Close the visual gap deep inside the opening from the reload camera.
        vertices.extend((.45 + 1.03 * math.cos(a * math.tau / 16), 4.0,
                         6.7 + 1.03 * math.sin(a * math.tau / 16)) for a in range(16))
        faces.append(tuple(range(8, 24)))
    else:
        vertices.extend([(-1.14, -1.4, 6.84), (1.14, -1.4, 6.84),
                         (1.14, 13.6, 6.84), (-1.14, 13.6, 6.84)])
        faces.append((8, 9, 10, 11))
    mesh = bpy.data.meshes.new('ReceiverInterior')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        x, y, _ = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((x - profile[0][0]) / (profile[-1][0] - profile[0][0]), (y - front) / (back - front))
    material = bpy.data.materials.new('ReceiverInterior')
    material.diffuse_color = (.072, .065, .057, 1)
    mesh.materials.append(material)
    lining = bpy.data.objects.new('ReceiverInterior', mesh)
    bpy.context.scene.collection.objects.link(lining)
    lining.matrix_world = native_to_camera
    bind_rigid(armature, lining, 'VM_Gun')
    return lining


def export_mesh_only(path, armature, meshes):
    """Export the repaired reference mesh without replacing baked animations."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in (armature, *meshes):
        obj.select_set(True)
    for obj in armature.children:   # 병과 캐릭터 7종 1인칭 팔(fpvm_lib.class_arm_objects)
        if obj.name.startswith('Arms_'):
            obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={'ARMATURE', 'MESH'},
        axis_forward='-Y', axis_up='Z', apply_unit_scale=True, add_leaf_bones=False,
        bake_anim=False, mesh_smooth_type='FACE', path_mode='STRIP',
        armature_nodetype='NULL', primary_bone_axis='Y', secondary_bone_axis='X',
    )


def add_existing_optic(key, armature, native_to_camera):
    """Reuse the existing mounted optic and lens meshes with the animated rifle."""
    optic = load_weapon(key)
    materials = [mat.name if mat else '' for mat in optic.data.materials]
    scope = key.split('_')[-1].upper()
    mesh = bmesh.new()
    mesh.from_mesh(optic.data)
    unwanted = [face for face in mesh.faces if not materials[face.material_index].startswith((scope + '_', 'Mount_'))]
    bmesh.ops.delete(mesh, geom=unwanted, context='FACES')
    bmesh.ops.delete(mesh, geom=[vertex for vertex in mesh.verts if not vertex.link_faces], context='VERTS')
    mesh.to_mesh(optic.data)
    mesh.free()
    assert any(poly for poly in optic.data.polygons if materials[poly.material_index].endswith('_Glass')), key
    if len(optic.data.polygons) > 45000:
        # 2026-11-21: 유리(렌즈) 면은 줄이지 않음. 전체를 한꺼번에 줄이면 ZF41 의 얇은 렌즈 원판(9,506면)이 뭉개져
        # 관 벽 같은 조각만 남았고, 조준경 화면 속 화면에서 렌즈가 '이중 원통'처럼 보였음 -> 유리를 떼어 두고 나머지만 줄인 뒤 다시 합침
        glass_ids = {i for i, name in enumerate(materials) if name.endswith('_Glass')}
        mesh = bmesh.new(); mesh.from_mesh(optic.data)
        lens_data = optic.data.copy(); lens_mesh = bmesh.new(); lens_mesh.from_mesh(lens_data)
        bmesh.ops.delete(lens_mesh, geom=[f for f in lens_mesh.faces if f.material_index not in glass_ids], context='FACES')
        bmesh.ops.delete(lens_mesh, geom=[v for v in lens_mesh.verts if not v.link_faces], context='VERTS'); lens_mesh.to_mesh(lens_data); lens_mesh.free()
        bmesh.ops.delete(mesh, geom=[f for f in mesh.faces if f.material_index in glass_ids], context='FACES')
        bmesh.ops.delete(mesh, geom=[v for v in mesh.verts if not v.link_faces], context='VERTS'); mesh.to_mesh(optic.data); mesh.free()
        budget = max(1000, 45000 - len(lens_data.polygons))
        if len(optic.data.polygons) > budget:
            modifier = optic.modifiers.new('Scope render budget', 'DECIMATE')
            modifier.ratio = budget / len(optic.data.polygons)
            bpy.context.view_layer.objects.active = optic
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        lens = bpy.data.objects.new('ScopeLens', lens_data); bpy.context.scene.collection.objects.link(lens); lens.matrix_world = optic.matrix_world.copy()
        bpy.ops.object.select_all(action='DESELECT'); lens.select_set(True); optic.select_set(True); bpy.context.view_layer.objects.active = optic; bpy.ops.object.join()
    if scope == 'ZF41':
        # 실제 ZF41 은 접안부 끝에서 렌즈 한 장이 관을 꽉 채워 보임. 원본은 접안부 끝(y -1.75)에 안쪽 반지름 0.55 의 금속 고리와
        # 여러 렌즈 조각이 겹쳐 뒤에서 보면 '이중 원'이 됨 -> 끝면 바로 바깥(y -1.70)에 관 안쪽 반지름(0.80)의 유리 원판(양면)을 덧댐
        glass = next(i for i, name in enumerate(materials) if name == 'ZF41_Glass')
        cx, cz, yc, rr = 0.95, 10.76, -1.70, 0.80
        disc = bmesh.new(); disc.from_mesh(optic.data)
        for flip in (False, True):
            ring_v = [disc.verts.new((cx + rr * math.cos(2 * math.pi * k / 48), yc, cz + rr * math.sin(2 * math.pi * k / 48))) for k in range(48)]
            face = disc.faces.new(ring_v[::-1] if flip else ring_v); face.material_index = glass
        disc.to_mesh(optic.data); disc.free()
    attach_surfaces(optic.data, scope, materials)
    finish_surfaces(optic.data)
    optic.name = scope + '_Optic'
    optic.matrix_world = native_to_camera
    bind_rigid(armature, optic, 'VM_Gun')
    return optic
