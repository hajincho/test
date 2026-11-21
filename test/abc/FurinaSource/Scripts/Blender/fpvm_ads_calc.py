"""blender -b --python fpvm_ads_calc.py -- <json in> <out json> : 뷰모델 정조준 변환 계산(카메라 공간 -> UE 상대 변환 행렬)
 입력: gun_pos, gun_rot(대기 자세), rear/front(원본 cm: 뒤 가늠자 홈 바닥, 앞 가늠쇠 끝), rear_dist_cm(눈-뒤가늠자, 없으면 대기 자세 거리).
 정조준 = 조준선이 카메라 축(+X) 위, 총 윗면 위쪽.
 출력: UE 행렬(행벡터 규약: x_plane..w_plane) + 위치(cm)/쿼터니언"""
import sys, json, math
from pathlib import Path
sys.path.insert(0, r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Scripts\Blender')
from mathutils import Matrix, Vector
import fpvm_lib as L
def align(settings):
    authored_pose = L.gun_native_to_cam(settings['gun_pos'], *settings['gun_rot'])
    rear = authored_pose @ Vector(settings['rear'])
    front = authored_pose @ Vector(settings['front'])
    distance = settings.get('rear_dist_cm', rear.x * 100) / 100
    # Align the rendered prop's two-point line with the game camera axis.
    axis = (front - rear).normalized()
    top = (authored_pose.to_3x3() @ Vector((0, 0, 1))).normalized()
    side = top.cross(axis).normalized()
    rotate = Matrix((axis, side, axis.cross(side))).to_4x4()
    target = Matrix.Translation(Vector((distance, 0, 0)) - rotate @ rear) @ rotate
    flip_y = Matrix.Diagonal((1, -1, 1, 1))
    ue_transform = flip_y @ target @ flip_y
    ue_transform.translation *= 100
    result = {
        'ue_loc_cm': list(ue_transform.translation),
        'ue_quat_xyzw': list(ue_transform.to_quaternion())[1:] + [ue_transform.to_quaternion().w],
        'rows': [list(row) for row in ue_transform],
        'check_rear_cam_m': list(target @ rear),
        'check_front_cam_m': list(target @ front),
        'rear_dist_cm': distance * 100,
    }
    assert max(abs(coord) for p in ('check_rear_cam_m', 'check_front_cam_m') for coord in result[p][1:]) < 1e-5
    return result


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    if args != ['all']:
        settings = json.loads(Path(args[0]).read_text(encoding='utf-8'))
        Path(args[1]).write_text(json.dumps(align(settings), indent=2), encoding='utf-8')
        return
    data = Path(L.D) / 'Data'
    rifles = {key: json.loads((data / f'fpvm_{key}_ads_in.json').read_text(encoding='utf-8')) for key in ('kar98k', 'g43')}
    scopes = json.loads((data / 'de_scoped_build.json').read_text(encoding='utf-8'))
    targets = {key: align(settings) for key, settings in rifles.items()}
    # The assembled artist models supply the optical centers and tube extents.
    for key, rifle, x, z, onscreen_distance, power in (
        ('kar98k_zf39', 'kar98k', .65, 11.90, 18., 4.),
        ('kar98k_zf41', 'kar98k', .90, 10.74, 45., 1.5),
        ('g43_zf4', 'g43', 0., 11.50, 18., 4.),
    ):
        front_y, rear_y = scopes[key]['scope_y_range']
        settings = dict(rifles[rifle], front=[x, front_y, z], rear=[x, rear_y, z], rear_dist_cm=onscreen_distance)
        targets[key] = dict(align(settings), magnification=power)
    for key, rear, front in (
        ('p38', [-.20, 8.95, 5.71], [-.20, -9.38, 4.63]),
        ('p08', [0., 9.38, 6.42], [0., -10.2, 6.72]),
        ('pp', [-.07, 4.83, 4.95], [-.07, -7.75, 4.59]),
    ):
        targets[key] = align({'gun_pos': (28., -6., -6.5), 'gun_rot': (2.5, 4., -3.), 'rear': rear, 'front': front, 'rear_dist_cm': 32.})
    for key in ('mp40', 'mp38', 'stg44'):   # 기관단총/돌격소총(fpvm_smg.py export 가 입력을 씀)
        f = data / f'fpvm_{key}_ads_in.json'
        if f.is_file(): targets[key] = align(json.loads(f.read_text(encoding='utf-8')))
    (data / 'fpvm_view_alignment.json').write_text(json.dumps(targets, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
