"""Bake the PzB 39 standing reaction on the existing full-body skeleton."""
import json
import math
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_reload_wrists import ASSETS, around, moved, relative, write_tracks


ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = '/Game/Furina/FPVM/PZB39/AS_PZB39_BalanceRecovery'
REFERENCE = '/Game/Furina/TFP/Anim/AS_Furina_TFP_N_Idle'
FPS = 30
KEYS = (
    # Time, pelvis (forward/side/up), pelvis/chest tilt, roll, head pitch, palm blend.
    (0.,    0,  0,   0,   0,   0,  0,   0, 0),
    (.10, -5,   1,  -2,  -8, -12,  1,  -5, 0),
    (.27,-17,   3, -11, -22, -29,  6, -13, 0),
    (.48,-32,   8, -35, -41, -43, 15, -23, .23),
    (.70,-37,   8, -81, -58, -49, 28, -38, 1),
    (.92,-38,   8, -78, -56, -47, 26, -34, 1),
    (1.22,-37,   7, -79, -54, -45, 25, -31, 1),
    (1.53,-34,   6, -78, -38, -21, 26, -13, 1),
    (1.88,-28,   4, -81, -19,  15, 24,   7, 1),
    (2.20,-20,   2, -83,  -2,  49, 12,  19, .50),
    (2.45,-13,   2, -77,   6,  53,  4,  23, .18),
    (2.71, -2,   1, -54,  10,  40,  4,  18, 0),
    (3.01,  5,  -1, -24,   7,  23,  2,   9, 0),
    (3.43,  2,   0,  -3,   1,   5,  1,   2, 0),
    (3.74,  0,   0,   0,   0,   0,  0,   0, 0),
)
DROP_POINT = (-16., 21.)
PICKUP_TIME = 2.39
FORWARD, RIGHT, UP = (unreal.Vector(1., 0., 0.), unreal.Vector(0., 1., 0.), unreal.Vector(0., 0., 1.))


def ramp(t, start, end):
    x = max(0., min(1., (t - start) / (end - start)))
    return x*x*(3. - 2.*x)


def get_state(t):
    for index in range(1, len(KEYS)):
        a, b = KEYS[index - 1:index + 1]
        if t > b[0]:
            continue
        # Cubic Hermite with monotone slopes. Preserve speed across markers
        # except where contact or a genuine change in direction decelerates a joint.
        h = b[0] - a[0]
        x = (t - a[0]) / h
        previous = KEYS[max(0, index - 2)]
        next_key = KEYS[min(index + 1, len(KEYS) - 1)]
        result = []
        for i in range(1, len(a)):
            slope = (b[i] - a[i]) / h
            pre = (a[i] - previous[i]) / max(.001, a[0] - previous[0])
            post = (next_key[i] - b[i]) / max(.001, next_key[0] - b[0])
            m0 = 2.*slope*pre/(slope+pre) if slope*pre > 0. else 0.
            m1 = 2.*slope*post/(slope+post) if slope*post > 0. else 0.
            result.append((2*x**3-3*x*x+1)*a[i] + (-2*x**3+3*x*x)*b[i] +
                          h*((x**3-2*x*x+x)*m0 + (x**3-x*x)*m1))
        return result
    return KEYS[-1][1:]


def transform(row):
    value = unreal.Transform()
    value.translation = unreal.Vector(*row['loc'])
    value.rotation = unreal.Quat(*row['q'])
    value.scale3d = unreal.Vector(*row['scale'])
    return value


def local(world, parent):
    return relative(world, parent, world.scale3d / parent.scale3d.x)


class Body:
    def __init__(self):
        sample = json.loads((ROOT / 'FurinaSource/Data/lyra_fp_arms_pose_a1.json').read_text(encoding='utf-8'))['samples'][0]
        self.parents = {key: row['parent'] for key, row in sample['bones'].items()}
        self.mesh = transform(sample['mesh'])
        self.base = {key: transform(row['ws']) for key, row in sample['bones'].items()}
        self.start = {key: local(world, self.base.get(self.parents[key], self.mesh))
                      for key, world in self.base.items()}
        self.posed = {}
        self.keys = list(self.base)
        self.floor = self.mesh.translation.z + 3.5
        hip = self.base['Hips'].translation
        self.palm = unreal.Vector(hip.x - 33., hip.y - 16., self.floor)
        self.pickup = unreal.Vector(self.mesh.translation.x + DROP_POINT[0],
                                    self.mesh.translation.y + DROP_POINT[1], self.floor + 7.)
        self.base_eyes = transform(sample['fpcam'])

    def refresh(self):
        self.posed = {}
        for key in self.keys:
            parent = self.posed.get(self.parents[key], self.mesh)
            self.posed[key] = unreal.MathLibrary.compose_transforms(self.locals[key], parent)

    def set_bone(self, key, world):
        self.locals[key] = local(world, self.posed.get(self.parents[key], self.mesh))
        self.refresh()

    def bend(self, key, q, change=None):
        before = self.posed[key]
        after = moved(before, before.translation if change is None else before.translation + change,
                      q * before.rotation)
        self.set_bone(key, after)

    def reach(self, names, target, pole, rotation):
        upper, lower, end = names
        start = self.posed[upper].translation
        joint = self.posed[lower].translation
        tip = self.posed[end].translation
        a, b = (joint - start).length(), (tip - joint).length()
        direction = (target - start).normal()
        distance = min(a + b - .1, max(abs(a - b) + .1, (target - start).length()))
        along = (a*a + distance*distance - b*b)/(2.*distance)
        radial = (pole - direction * pole.dot(direction)).normal()
        next_joint = start + direction * along + radial * math.sqrt(max(0., a*a - along*along))
        reached = start + direction * distance
        self.bend(upper, (joint - start).find_quat_between_vectors(next_joint - start))
        lower_point = self.posed[lower].translation
        self.bend(lower, (self.posed[end].translation - lower_point).find_quat_between_vectors(reached - lower_point))
        tip_pose = self.posed[end]
        self.set_bone(end, moved(tip_pose, tip_pose.translation, rotation))

    def frame(self, time):
        x, y, z, pelvis, chest, roll, head, palm_weight = get_state(time)
        self.locals = self.start.copy()
        self.refresh()
        def tilt(angle):
            return around(RIGHT, math.radians(angle))
        self.bend('Hips', around(FORWARD, math.radians(roll)) * tilt(pelvis), unreal.Vector(x, y, z))
        self.bend('Spine', tilt((chest - pelvis) * .58))
        self.bend('Chest', tilt((chest - pelvis) * .42))
        self.bend('Neck', tilt((head - chest) * .54))
        self.bend('Head', tilt((head - chest) * .46))
        for i, side in enumerate(('Left', 'Right')):
            start = self.base[side + '-ankle']
            step = ramp(time, .13 + i*.08, .62 + i*.06) * (1. - ramp(time, 1.57 + i*.13, 2.39 + i*.14))
            lift = (math.sin(step * math.pi) ** 2) * (6. if i else 4.)
            dest = start.translation + unreal.Vector((-18. if i else -10.) * step, (5. if i else -2.) * step, lift)
            anchor = ramp(time, .05, .30) * (1. - ramp(time, 3.10, 3.73))
            current = self.posed[side + '-ankle']
            self.reach([side + suffix for suffix in ('-leg', '-knee', '-ankle')],
                       current.translation + (dest - current.translation) * anchor,
                       FORWARD + RIGHT * (-.19 if i == 0 else .19), current.rotation.slerp_quat(start.rotation, anchor))
        hand = self.posed['Left-wrist']
        # Keep the palm against one position during the weight transfer.
        hand_forward = (self.posed['MiddleFinger1_L'].translation - hand.translation).normal()
        hand_across = (self.posed['IndexFinger1_L'].translation - self.posed['LittleFinger1_L'].translation).normal()
        direction = (FORWARD - RIGHT*.28).normal()
        turn = hand_forward.find_quat_between_vectors(direction)
        across_now = turn.rotate_vector(hand_across)
        across_goal = UP.cross(direction).normal()
        if across_now.dot(across_goal) < 0.:
            across_goal = -across_goal
        twist = math.atan2(direction.dot(across_now.cross(across_goal)), across_now.dot(across_goal))
        palm_rotation = around(direction, twist) * turn * hand.rotation
        destination = self.palm - direction*5. + UP*2.2
        self.reach(('Left-arm', 'Left-elbow', 'Left-wrist'),
                   hand.translation + (destination - hand.translation) * palm_weight,
                   unreal.Vector(0., -1., .4), hand.rotation.slerp_quat(palm_rotation, palm_weight))
        # The free hand reaches the prop as the shoulders roll over the planted foot.
        pickup = ramp(time, 1.82, PICKUP_TIME) * (1. - ramp(time, 2.48, 3.01))
        if pickup > 0.:
            right = self.posed['Right-wrist']
            contact = self.pickup + UP * (14. * ramp(time, PICKUP_TIME, 2.73))
            fingers = (self.posed['MiddleFinger1_R'].translation - right.translation).normal()
            grip = fingers.find_quat_between_vectors((FORWARD + RIGHT*.45 - UP*.05).normal()) * right.rotation
            self.reach(('Right-arm', 'Right-elbow', 'Right-wrist'),
                       right.translation + (contact - right.translation) * pickup,
                       unreal.Vector(.1, 1., .15), right.rotation.slerp_quat(grip, pickup))
            close = ramp(time, 2.20, PICKUP_TIME) * (1. - ramp(time, 3.08, 3.60))
            for digit in ('IndexFinger', 'MiddleFinger', 'RingFinger', 'LittleFinger'):
                for joint in (1, 2, 3):
                    key = f'{digit}{joint}_R'
                    finger = self.posed[key]
                    axis = finger.rotation.rotate_vector(unreal.Vector(0., 0., 1.))
                    self.bend(key, around(axis, math.radians((20 if digit == 'IndexFinger' else 29) * close)))
        return {
            'head_cm': list((self.posed['Head'].translation - self.base['Head'].translation).to_tuple()),
            'wrist_error_cm': (self.posed['Left-wrist'].translation - destination).length(),
            'palm': palm_weight,
            'right_to_drop_cm': (self.posed['Right-wrist'].translation - self.pickup).length(),
            'right_shoulder_to_drop_cm': list((self.posed['Right-arm'].translation - self.pickup).to_tuple()),
        }


def main():
    body = Body()
    builtin = unreal.load_asset(REFERENCE)
    result = unreal.load_asset(OUT) if ASSETS.does_asset_exist(OUT) else ASSETS.duplicate_asset(REFERENCE, OUT)
    controller = result.controller
    controller.set_frame_rate(unreal.FrameRate(FPS, 1), False)
    frames = round(KEYS[-1][0] * FPS)
    controller.set_number_of_frames(unreal.FrameNumber(frames), False)
    normalize = lambda name: name.casefold().replace('_', '-').replace(' ', '-')
    track_names = {normalize(str(n)): str(n) for n in unreal.AnimationLibrary.get_animation_track_names(builtin)}
    tracks = {key: [] for key in body.keys if normalize(key) in track_names}
    assert {'Hips', 'Head', 'Left-wrist'}.issubset(tracks), list(track_names)[:24]
    report = []
    for frame in range(frames + 1):
        sample = body.frame(frame / FPS)
        for bone, values in tracks.items():
            values.append(body.locals[bone])
        report.append({'t': frame / FPS, **sample})
    write_tracks(result, {track_names[normalize(key)]: values for key, values in tracks.items()})
    assert ASSETS.save_loaded_asset(result, False)
    (ROOT / 'Saved/Pzb39FullBody.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PZB39_RECOVERY_POSE_SAVED', result.get_play_length())


if __name__ == '__main__':
    main()
