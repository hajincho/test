"""Fit the Kar98k contact pose against the exported in-game skin and stock."""

import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path.cwd()
WORK = ROOT / 'Saved/FPVMReview/GripSurfaceWork'
sys.path.insert(0, str(ROOT / 'FurinaSource/Scripts/Blender'))
from fpvm_grip import sdist

CONVERT = Matrix.Diagonal((.01, -.01, .01, 1.))


def component_pose(key):
    location, (x, y, z, w), scale = key
    return CONVERT @ Matrix.LocRotScale(Vector(location), Quaternion((w, x, y, z)), Vector(scale))


def dominant(vertex, names):
    return names[max(vertex.groups, key=lambda group: group.weight).group] if vertex.groups else ''


def stock_surface(mesh, owners, transform=None):
    transform = mesh.matrix_world if transform is None else transform @ mesh.matrix_world
    points = [transform @ v.co for v in mesh.data.vertices]
    mesh.data.calc_loop_triangles()
    faces = [tuple(f.vertices) for f in mesh.data.loop_triangles if all(owners[i] == 'VM_Gun' for i in f.vertices)]
    return BVHTree.FromPolygons(points, faces, all_triangles=True)


class Digit:
    def __init__(self, mesh, group_names, owners, name, bind, posed):
        suffix = '_L'
        self.names = [name + str(joint) + suffix for joint in (range(3) if name == 'Thumb' else range(1, 4))]
        self.local = [posed[parent].inverted() @ posed[child]
                      for parent, child in zip(['Left-wrist', *self.names], self.names)]
        self.parent = posed['Left-wrist']
        picked = []
        for index, bone in enumerate(self.names):
            indices = [v.index for v in mesh.data.vertices if owners[v.index] == bone]
            picked.extend((point, index) for point in indices[::max(1, len(indices)//60)])
        self.regions = np.array([joint for _, joint in picked])
        self.base = np.zeros((len(picked), 3))
        self.bind_points = np.zeros((3, len(picked), 4))
        self.weights = np.zeros((3, len(picked), 1))
        changes = {key: posed[key] @ matrix.inverted() for key, matrix in bind.items() if key in posed}
        for column, (vertex_index, _) in enumerate(picked):
            v = mesh.data.vertices[vertex_index]
            point = mesh.matrix_world @ v.co
            weight_sum = sum(w.weight for w in v.groups if group_names[w.group] in changes)
            if not weight_sum:
                self.base[column] = point
                continue
            for part in v.groups:
                bone = group_names[part.group]
                if bone not in changes:
                    continue
                weight = part.weight / weight_sum
                if bone in self.names:
                    idx = self.names.index(bone)
                    self.bind_points[idx, column] = (*tuple(bind[bone].inverted() @ point), 1.)
                    self.weights[idx, column, 0] = weight
                else:
                    self.base[column] += np.array(changes[bone] @ point) * weight
        assert len(picked) > 0, name

    @staticmethod
    def rotations(values):
        return [Euler(tuple(math.radians(deg) for deg in values[start:start + 3])).to_quaternion()
                for start in (0, 3, 6)]

    def transforms(self, values):
        world = self.parent
        transforms = []
        for rest, turn in zip(self.local, self.rotations(values)):
            world = world @ rest @ turn.to_matrix().to_4x4()
            transforms.append(world)
        return transforms

    def positions(self, values):
        transforms = self.transforms(values)
        skin = self.bind_points @ np.array(transforms).transpose(0, 2, 1)
        return self.base + np.sum(self.weights * skin[:, :, :3], axis=0)


def scores(surface, digit, values):
    distances = np.array([1000. * sdist(surface, Vector(point)) for point in digit.positions(values)])
    return distances


def run_fit(name, surface, digit, relax_fingers=False):
    zero = np.zeros(9)
    current = zero.copy()
    lower = np.array([-36.,-33.,-37.,-28.,-28.,-28.,-25.,-25.,-25.])
    upper = -lower

    def cost(values):
        distance = scores(surface, digit, values)
        inner = np.maximum(-distance - .08, 0.)
        pads = [distance[digit.regions == joint] for joint in (1, 2)]
        # A soft pad should touch across a small area. The dorsal side stays free.
        near = [float(np.percentile(np.abs(points), 8.)) for points in pads]
        touch = sum(max(min_gap - .22, 0.) ** 2 for min_gap in near)
        penalty = 5. * (inner**2).sum() + 22. * inner.max(initial=0.)**2 + 3. * touch + .0018 * np.dot(values, values)
        if relax_fingers and name != 'Thumb':
            a,b,c = (transform.translation for transform in digit.transforms(values))
            curl = math.degrees((b-a).angle(c-b,0.))
            penalty += .095 * max(curl - 63.,0.)**2
        return penalty

    rng = np.random.default_rng(28)
    seeds = [(cost(zero), zero)]
    for _ in range(35):
        v = np.clip(rng.normal(0., 9., len(zero)), lower, upper)
        seeds.append((cost(v), v))
    finals = []
    for best, candidate in sorted(seeds, key=lambda item: item[0])[:3]:
        current = candidate.copy()
        for step in (9., 5., 2.5, 1.25, .5):
            for _ in range(3):
                improved = False
                for axis in range(9):
                    center = current[axis]
                    choice = center
                    for sign in (-1., 1.):
                        current[axis] = np.clip(center + sign * step, lower[axis], upper[axis])
                        value = cost(current)
                        if value < best:
                            best, choice, improved = value, current[axis], True
                    current[axis] = choice
                if not improved:
                    break
        finals.append((best, current))
    _, result = min(finals, key=lambda item: item[0])
    record = {}
    for label, values in [('before', zero), ('after', result)]:
        d = scores(surface, digit, values)
        record[label] = {
            'max_penetration_mm': round(max(0., -float(d.min())), 3),
            'nearest_pad_mm': [round(float(np.min(np.abs(d[digit.regions == n]))), 3) for n in (1,2)],
        }
    print('CONTACT', name, record, flush=True)
    return {n: [q.x,q.y,q.z,q.w] for n,q in zip(digit.names,digit.rotations(result))}, record


def main():
    picks = json.loads((WORK/'poses.json').read_text())['Kar98k']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(WORK/'Kar98k_mesh.fbx'))
    mesh = next(obj for obj in bpy.context.scene.objects if obj.type == 'MESH')
    group_names = {g.index:g.name.replace(' ','-') for g in mesh.vertex_groups}
    owners = [dominant(v,group_names) for v in mesh.data.vertices]
    surface = stock_surface(mesh, owners)
    bind = {n:component_pose(t) for n,t in picks['rest'].items() if not n.startswith('VM_')}
    posed = {n:component_pose(t) for n,t in picks['Idle'][0]['bones'].items()}
    result = {'rotations':{},'skin':{}}
    for name in ('Thumb','IndexFinger','MiddleFinger','RingFinger','LittleFinger'):
        digit = Digit(mesh,group_names,owners,name,bind,posed)
        offsets, report = run_fit(name,surface,digit)
        result['rotations'].update(offsets)
        result['skin'][name] = report
    (WORK/'Kar98kContactFit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()

