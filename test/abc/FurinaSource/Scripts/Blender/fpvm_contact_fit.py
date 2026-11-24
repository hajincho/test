"""Fit a posed hand against the evaluated surfaces of a game viewmodel."""

import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from fpvm_contact_views import owner_bone, triangles
from fpvm_grip import sdist, spread_axis
from fpvm_lib import FINGERS, fbones, finger_axes, hand_axes


class ContactPose:
    def __init__(self, arm, hand, props, dominant, side, check_fingers, preserve_handle):
        self.wrist = {'L': 'Left wrist', 'R': 'Right wrist'}[side]
        self.fingers = {finger: fbones(side, finger) for finger in FINGERS}
        self.names = [self.wrist, *(name for chain in self.fingers.values() for name in chain)]
        indices = {name: i for i, name in enumerate(self.names)}
        selected = [index for index in sorted(dominant) if dominant[index] in indices]
        regions = np.array([indices[dominant[index]] for index in selected])
        remap = {index: i for i, index in enumerate(selected)}
        points, faces = triangles(hand)
        self.faces = [tuple(remap[vertex] for vertex in face) for face in faces if all(vertex in remap for vertex in face)]
        self.digit_faces = {}
        if check_fingers:
            for index, face in enumerate(self.faces):
                membership = {divmod(int(regions[vertex]) - 1, 3) for vertex in face if regions[vertex] > 0}
                fingers = {digit for digit, _ in membership}
                if len(fingers) == 1 and membership and all(joint > 0 for _, joint in membership):
                    self.digit_faces[index] = next(iter(fingers))
        self.points = np.array([points[index] for index in selected])
        self.sample = np.arange(len(selected))[::4]
        self.pads = [np.flatnonzero((regions >= start) & (regions < end))[::3]
                     for start, end in ((0, 1), (2, 4), (6, 7), (8, 10), (11, 13), (14, 16))]
        self.handle_pads = []
        if preserve_handle:
            gun = arm.matrix_world @ arm.pose.bones['VM_Gun'].matrix
            self.up = np.array(Vector(gun.col[2][:3]).normalized())
            self.forward = np.array(Vector(gun.col[1][:3]).normalized())
            self.handle_pads = [self.pads[index] for index in (0, 1, 3, 4, 5)]
        self.surface = [(obj.name, BVHTree.FromPolygons(*triangles(obj), all_triangles=True)) for obj in props]
        weights = np.zeros((len(self.names), len(selected), 1))
        groups = {group.index: indices[group.name] for group in hand.vertex_groups if group.name in indices}
        for i, vertex in enumerate(hand.data.vertices[index] for index in selected):
            total = sum(group.weight for group in vertex.groups)
            for group in vertex.groups:
                if group.group in groups:
                    weights[groups[group.group], i, 0] = group.weight / total
        rest = np.array([hand.matrix_world @ hand.data.vertices[index].co for index in selected])
        rest = np.c_[rest, np.ones(len(selected))]
        self.pose = [arm.matrix_world @ arm.pose.bones[name].matrix for name in self.names]
        self.bind_points = np.array([rest @ np.array((arm.matrix_world @ arm.data.bones[name].matrix_local).inverted()).T
                                     for name in self.names])
        self.weights = weights
        self.current = self.deform(self.pose)
        self.local = [None] + [self.pose[0 if i % 3 == 1 else i - 1].inverted() @ matrix
                               for i, matrix in enumerate(self.pose) if i]
        hand_frame = hand_axes(arm, side)
        self.palm_normal = Vector(hand_frame['p_local']).normalized()
        axes = finger_axes(arm, side, hand_frame)
        self.flex = {name: Vector(axes[name]) for name in self.names[1:]}
        self.spread = {chain[0]: spread_axis(self.flex[chain[0]]) for chain in self.fingers.values()}

    def deform(self, matrices):
        transformed = self.bind_points @ np.array(matrices).transpose(0, 2, 1)
        return np.sum(self.weights * transformed[:, :, :3], axis=0)

    def wrist_from(self, values):
        source = self.pose[0]
        location, rotation, scale = source.decompose()
        location += rotation @ (Vector(values[:3]) / 1000.0)
        rotation @= Euler(tuple(math.radians(value) for value in values[3:6])).to_quaternion()
        return Matrix.LocRotScale(location, rotation, scale)

    def evaluate(self, values):
        matrices = [self.wrist_from(values)]
        for i, name in enumerate(self.names[1:], 1):
            digit, joint = divmod(i - 1, 3)
            root = 6 + digit * 4
            q = Quaternion(self.flex[name], math.radians(values[root + joint]))
            if joint == 0:
                q = Quaternion(self.spread[name], math.radians(values[root + 3])) @ q
            base = matrices[0 if joint == 0 else i - 1] @ self.local[i]
            matrices.append(base @ q.to_matrix().to_4x4())
        points = self.points + self.deform(matrices) - self.current
        handle_error = 0.0
        if self.handle_pads:
            movement = (points - self.points) * 1000.0
            for indices in self.handle_pads:
                center = np.median(movement[indices], axis=0)
                height, length = float(center @ self.up), abs(float(center @ self.forward))
                height_error = max(height - 3.0, -height - 9.0, 0.0)
                handle_error += 1.7 * height_error**2 + 0.32 * max(length - 6.0, 0.0)**2
        skin = BVHTree.FromPolygons(points.tolist(), self.faces, all_triangles=True)
        inside, nearest = [], np.full(len(points), np.inf)
        crossings = {}
        for name, surface in self.surface:
            overlap = {a for a, _ in skin.overlap(surface)}
            crossings[name] = len(overlap)
            possible = set(vertex for index in overlap for vertex in self.faces[index])
            for vertex in possible.union(self.sample):
                point = Vector(points[vertex])
                distance = sdist(surface, point)
                if distance < 0:
                    inside.append(-1000.0 * distance)
                nearest[vertex] = min(nearest[vertex], abs(distance) * 1000.0)
            for indices in self.pads:
                for vertex in indices:
                    if nearest[vertex] <= 0.18:
                        continue
                    _, _, _, distance = surface.find_nearest(Vector(points[vertex]))
                    if distance is not None:
                        nearest[vertex] = min(nearest[vertex], distance * 1000.0)
        gaps = np.array([nearest[indices].min(initial=100.0) for indices in self.pads])
        finger_crossings = 0
        if self.digit_faces:
            finger_crossings = sum(1 for first, second in skin.overlap(skin) if first < second
                                   and first in self.digit_faces and second in self.digit_faces
                                   and self.digit_faces[first] != self.digit_faces[second])
        return crossings, np.array(inside), gaps, finger_crossings, handle_error


def fit_contact(model, clip, output, arm, hand, props, dominant, goto, frames, side, prop=None, seed=None,
                check_fingers=False, preserve_handle=False):
    measured = [obj for obj in props if not prop or owner_bone(obj) == prop]
    if not measured:
        raise ValueError(f'No surface meshes for {prop}')
    poses = []
    for frame in frames:
        goto(frame)
        poses.append(ContactPose(arm, hand, measured, dominant, side, check_fingers, preserve_handle))
    witness = poses[0]
    values = np.zeros(26)
    limits = np.array([37, 37, 37, 34, 34, 34] + [40, 48, 38, 30] * 5)
    contact = np.array([3.6, 2.85, 0.30 if side == 'R' and not prop else 1.0, 1.6, 1.3, 1.15])
    free_gap = np.array([2.0, 2.5, 2.8, 2.5, 2.5, 3.2])

    def score(state):
        total = 0.0
        for pose in poses:
            overlap, depths, gaps, finger_crossings, handle_error = pose.evaluate(state)
            touch = np.dot(contact, np.maximum(0.0, gaps - free_gap))
            penetration = np.square(np.maximum(depths - 0.15, 0.0)).sum()
            total += touch + 1.15 * sum(overlap.values()) + 0.27 * penetration + 4.2 * depths.max(initial=0.0)
            total += 1.2 * finger_crossings + handle_error
        if check_fingers:
            digits = state[6:].reshape(5, 4)
            total += 0.10 * np.maximum(np.abs(digits[1:, 2] - 0.65 * digits[1:, 1]) - 10.0, 0.0).sum()
            total += 0.012 * np.square(np.maximum(np.abs(digits[1:, 3]) - 12.0, 0.0)).sum()
        return total / len(poses) + float(np.dot(state, state)) * 0.00060

    before = [pose.evaluate(values) for pose in poses]
    if seed is not None:
        values = np.array(seed, dtype=float)
    def descend(state, axes, length, angle, passes):
        state = state.copy()
        best_cost = score(state)
        for _ in range(passes):
            moved = False
            for axis in axes:
                origin = state[axis]
                best = origin
                for direction in (-1, 1):
                    candidate = float(np.clip(origin + direction * (length if axis < 3 else angle), -limits[axis], limits[axis]))
                    if candidate == origin:
                        continue
                    state[axis] = candidate
                    cost = score(state)
                    if cost < best_cost - 0.0005:
                        best_cost, best = cost, candidate
                state[axis] = best
                moved |= best != origin
            if not moved:
                break
        return best_cost, state

    rng = np.random.default_rng(1750)
    seeds = [(score(values), values), (score(np.zeros(26)), np.zeros(26))]
    for _ in range(100):
        state = values.copy()
        state[:3] += rng.normal(0.0, 13.0, size=3)
        state[:3] += rng.uniform(-17.0, 12.0) * np.array(witness.palm_normal)
        state[3:6] += rng.normal(0.0, 14.0, size=3)
        state[6:] += rng.normal(0.0, 12.0, size=20)
        state = np.clip(state, -limits, limits)
        seeds.append((score(state), state))
    candidates = []
    for _, state in sorted(seeds, key=lambda row: row[0])[:4]:
        _, state = descend(state, range(6), 6.0, 12.0, 4)
        candidates.append(descend(state, range(26), 2.5, 7.5, 6))
    _, values = min(candidates, key=lambda row: row[0])
    minimum, values = descend(values, range(26), 0.65, 1.75, 5)
    print('CONTACT_SCORE', model, side, round(minimum, 3), flush=True)
    after = [pose.evaluate(values) for pose in poses]
    goto(frames[0])
    reference = arm.matrix_world @ arm.pose.bones[prop or 'VM_Gun'].matrix
    source_local = reference.inverted() @ witness.pose[0]
    target_local = reference.inverted() @ witness.wrist_from(values)
    offsets = []
    for index, name in enumerate(witness.names[1:]):
        digit, joint = divmod(index, 3)
        base = 6 + digit * 4
        q = Quaternion(witness.flex[name], math.radians(values[base + joint]))
        if joint == 0:
            q = Quaternion(witness.spread[name], math.radians(values[base + 3])) @ q
        offsets.append((name, list(q)))
    result = {'clip': clip, 'side': side, 'prop': prop or 'VM_Gun', 'frames': frames,
              'reference': [list(row) for row in source_local], 'target': [list(row) for row in target_local],
              'correction_mm_deg': values.tolist(), 'offsets': dict(offsets), 'score': minimum,
              'before': [{'crossings': count, 'max_depth_mm': float(depths.max(initial=0.0)),
                          'contact_gaps_mm': gap.tolist(), 'between_fingers': self_crossings}
                         for count, depths, gap, self_crossings, _ in before],
              'after': [{'crossings': count, 'max_depth_mm': float(depths.max(initial=0.0)),
                         'contact_gaps_mm': gap.tolist(), 'between_fingers': self_crossings}
                        for count, depths, gap, self_crossings, _ in after]}
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f'contact_fit_{model}_{side}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('CONTACT_FIT', model, side, result['before'], result['after'])
