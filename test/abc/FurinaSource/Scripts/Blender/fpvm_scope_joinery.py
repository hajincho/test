"""Shape the visible joins of the existing game scope props."""
from math import cos, hypot, pi, sin, tau

import bmesh
import bpy


def loft(layers):
    """Connect chamfered silhouettes with continuous corner vertices."""
    geometry = []
    for x, y, z, a, b in layers:
        cut = min(a, b) * .36
        contour = [(-a + cut, -b), (a - cut, -b), (a, -b + cut), (a, b - cut),
                   (a - cut, b), (-a + cut, b), (-a, b - cut), (-a, -b + cut)]
        geometry.append([(x + i, y + j, z) for i, j in contour])
    vertices = [vertex for row in geometry for vertex in row]
    faces = [tuple(reversed(range(8)))]
    for i in range(len(geometry) - 1):
        for j in range(8):
            k = (j + 1) % 8
            faces.append((8*i+j, 8*i+k, 8*(i+1)+k, 8*(i+1)+j))
    faces.append(tuple(range(len(vertices) - 8, len(vertices))))
    return vertices, faces


def attach_surfaces(mesh, name, materials):
    """Seat each scope assembly visually against the original render mesh."""
    style = {
        'ZF39': ('Mount_K98_Blued', [
            [(.65, 3.4, 8.37, 1.14, 1.48), (.65, 3.4, 8.64, 1.19, 1.46), (.65, 3.4, 9.39, .84, .74)],
            [(.65, 15.5, 8.12, 1.13, 1.45), (.65, 15.5, 8.4, 1.16, 1.42), (.65, 15.5, 9.13, .83, .73)],
        ]),
        'ZF41': ('Mount_ZF41_Satin', [
            [(1.74, -7.75, 7.49, .38, 2.11), (1.74, -7.75, 7.8, .44, 2.16), (2.13, -7.75, 8.16, .46, 2.26)],
        ]),
        'ZF4': ('Mount_ZF4_Phosphate', [
            [(-1.43, 12.12, 7.30, .23, 5.84), (-1.49, 12.12, 7.65, .36, 5.84), (-1.65, 12.12, 8.34, .30, 5.52)],
            [(-1.61, 7.6, 8.08, .32, .95), (-1.57, 7.6, 8.5, .34, .85), (-1.56, 7.6, 9.33, .27, .70)],
            [(-1.61, 16.7, 8.08, .32, .95), (-1.57, 16.7, 8.5, .34, .85), (-1.56, 16.7, 9.33, .27, .70)],
        ]),
    }
    mount_name, parts = style[name]
    if mount_name not in materials:
        materials.append(mount_name)
        mesh.materials.append(bpy.data.materials.new(mount_name))
    mount_id = materials.index(mount_name)
    geom = bmesh.new()
    geom.from_mesh(mesh)
    if name == 'ZF41':
        for face in geom.faces:
            center = face.calc_center_median()
            if (materials[face.material_index] == 'ZF41_Blued' and
                    -11.6 < center.y < -5.15 and center.x > 1.55 and center.z < 9.7):
                face.material_index = mount_id
    for layers in parts:
        vertices, faces = loft(layers)
        points = [geom.verts.new(point) for point in vertices]
        for ids in faces:
            geom.faces.new([points[i] for i in ids]).material_index = mount_id
    add_circular_rims(geom, name, materials.index(name + '_Blued'))
    geom.to_mesh(mesh)
    geom.free()


def add_circular_rims(geom, name, metal_id):
    """Rebuild the silhouette of round rims with enough segments for close shots."""
    x, z, low, high = {
        'ZF39': (.65, 11.90, -6., 22.),
        'ZF41': (.90, 10.74, -14.75, -1.75),
        'ZF4': (0., 11.50, -1., 26.),
    }[name]
    for y, sign in ((low, 1.), (high, -1.)):
        if name == 'ZF4' and sign > 0:
            # The rectangular front housing stays angular.
            continue
        radii = sorted(hypot(v.co.x-x, v.co.z-z) for v in geom.verts if abs(v.co.y-y) < .2 and abs(v.co.z-z) < 2.5)
        if not radii:
            continue
        radius = radii[int(.88 * (len(radii)-1))]
        if radius < .6:
            continue
        profile = ((y+sign*.32, radius-.03), (y+sign*.13, radius+.06),
                   (y-sign*.005, radius+.025), (y-sign*.008, radius-.115))
        points = [[geom.verts.new((x + r*cos(tau*j/64), yy, z + r*sin(tau*j/64))) for j in range(64)]
                  for yy, r in profile]
        for a, b in zip(points, points[1:]):
            for j in range(64):
                k = (j+1) % 64
                ring = [a[j], a[k], b[k], b[j]]
                geom.faces.new(ring if sign > 0 else list(reversed(ring))).material_index = metal_id


def finish_surfaces(mesh):
    """Smooth curved shells, leaving glass rims and square cast housings defined."""
    geom = bmesh.new()
    geom.from_mesh(mesh)
    geom.normal_update()
    uv = geom.loops.layers.uv.verify()
    for face in geom.faces:
        material = mesh.materials[face.material_index].name
        face.smooth = not material.endswith('_Glass')
        if material.startswith('Mount_') or all(loop[uv].uv.length_squared < 1e-10 for loop in face.loops):
            dominant = max(range(3), key=lambda axis: abs(face.normal[axis]))
            axes = [axis for axis in range(3) if axis != dominant]
            for loop in face.loops:
                point = loop.vert.co
                loop[uv].uv = tuple(point[axis] / 8. for axis in axes)
    for edge in geom.edges:
        if edge.is_manifold:
            first, second = edge.link_faces
            edge.smooth = (first.material_index == second.material_index and
                           edge.calc_face_angle() < pi / 5)
    geom.to_mesh(mesh)
    geom.free()
    mesh.update()
