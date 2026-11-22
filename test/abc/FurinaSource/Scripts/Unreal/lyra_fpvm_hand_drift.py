"""에디터(편집 전용, 2026-11-22): 1인칭 뷰모델 클립(AS_FPVM_*)에서 손이 총(VM_Gun) 위에서 미끄러지는 양 측정 -> Saved/FpvmHandDrift.json
 Blender 원본에선 Idle/Fire 동안 손목-총 상대 위치 편차가 0.00cm 인데, 게임에서 '흐느적'거림 -> 언리얼 가져오기(뼈 압축 등) 단계 확인.
 클립마다 12개 시각에서 손목·검지 끝·엄지 끝 뼈의 VM_Gun 기준 위치를 구해 첫 시각 대비 최대 편차(cm). 압축 설정 이름도 같이 적음."""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); R = {}
BONES = ['Right wrist', 'IndexFinger3_R', 'Thumb2_R', 'Left wrist', 'IndexFinger3_L', 'Thumb2_L']
AR = unreal.AssetRegistryHelpers.get_asset_registry()


def rel(pose, b, gun):
    t = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD)
    return gun.inverse_transform_location(t.translation)


try:
    assets = AR.get_assets_by_path('/Game/Furina/FPVM', recursive=True)
    clips = sorted(str(a.package_name) for a in assets if str(a.asset_class_path.asset_name) == 'AnimSequence' and ('_Idle' in str(a.asset_name) or '_Fire' in str(a.asset_name)))
    opt = unreal.AnimPoseEvaluationOptions(); opt.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW)
    for mode in ('raw', 'compressed'):
        opt.set_editor_property('evaluation_type', unreal.AnimDataEvalType.RAW if mode == 'raw' else unreal.AnimDataEvalType.COMPRESSED)
        for p in clips:
            seq = unreal.load_asset(p); ln = seq.get_play_length(); hist = {b: [] for b in BONES}
            for k in range(12):
                pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, ln * k / 11.0, opt)
                gun = unreal.AnimPoseExtensions.get_bone_pose(pose, 'VM_Gun', unreal.AnimPoseSpaces.WORLD)
                for b in BONES: hist[b].append(rel(pose, b, gun))
            out = {}
            for b, h in hist.items(): out[b] = round(max((v - h[0]).length() for v in h), 3)
            e = R.setdefault(p.split('/')[-1], {}); e[mode] = out
            if mode == 'raw':
                bc = seq.get_editor_property('bone_compression_settings'); e['bone_comp'] = bc.get_name() if bc else None
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'FpvmHandDrift.json').write_text(json.dumps(R, indent=1, default=str), encoding='utf-8'); print('HAND_DRIFT', json.dumps(R, default=str)[:3000])
