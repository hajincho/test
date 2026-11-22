# FurinaSource

abc 프로젝트의 플레이어를 Furina로 바꾸면서 만든 원본 파일·스크립트·데이터입니다.
`Content/` 밖에 있어서 언리얼이 임포트하지 않습니다. 결과 에셋은 `Content/Furina`에 있습니다.

## 현재 총기·앉기 설정 (2026-11-15)

- 표시 총기는 제공된 `Downloads/ar15` 모델을 사용한 `M4/SK_M4A1`입니다. 길이를 80cm로 정규화하고 기존 무기 뼈대에 바인딩했습니다. Honey Badger 메시는 플레이어의 표시 경로에서 제외했습니다. 기존 템플릿의 손·재장전 모션과 무기 뼈대는 참고 자료로 유지하며, 푸리나의 짧은 팔에 맞춘 양팔 IK와 3인칭 전용 총 위치를 적용합니다.
- `Downloads/223-remington-556mm-nato-case-and-shell`의 탄두는 비행 메시, 빈 탄피는 배출 메시로 분리했습니다. 탄피는 총의 오른쪽 배출구에서 나가며 물리·회전·중력을 적용하고 6초 뒤 정리합니다. 배출은 로컬 벡터 `(-140,180,130) cm/s`를 총 회전으로 변환하고, 가시성을 위해 탄피 메시를 1.35배로 표시합니다. `BP_M4Flash`는 0.045초의 발광 메시와 조명을 사용합니다.
- 30발 탄창입니다. HUD에 잔탄을 표시하고, 잔탄 0 또는 재장전 중에는 발사하지 않습니다. R은 3초 재장전이며 완료 시 30발로 채웁니다. 예비탄 120발을 사용하며 부족한 탄수만큼 옮겨 채웁니다. 예: 25/120에서 재장전하면 30/115입니다. 두 번째로 제공한 HUD 이미지는 원본 그대로 임포트하고 HUD 머티리얼에서 인쇄된 탄수만 가려 실제 잔탄/예비탄을 표시합니다. 시점 전환으로 잔탄을 초기화하지 않습니다.
- C를 누를 때마다 앉기/서기를 전환합니다. `Downloads/tfpfl_example/TFPFL_Example`의 Character 폴더를 같은 콘텐츠 경로에 복사하고 102개 애니메이션/블렌드스페이스를 Furina 비율로 리타겟했습니다. 서기·걷기·달리기·방향 이동·앉기 보행은 새 `TFP/BS_FurinaStanding`, `BS_FurinaCrouching`을 사용합니다. 실제 수평 속도/방향과 CMC 앉기 상태를 게임 스레드의 실수 변수로 캐시합니다. 캡슐 반높이는 96→58cm이며, 새 앉기 모션 위에 예전 절차적 골반 하강이나 달리기 다리 IK를 중복 적용하지 않습니다. 발이 접지한 구간의 리타겟된 발 속도를 측정해 각 클립의 재생률을 맞췄습니다. 견착 시 60cm/s에서도 보행이 유지됩니다. `IMC_FurinaStance`를 우선순위 100으로 등록합니다. 실제 ExampleLevel의 `ThirdPersonCharacter_BP_2`에는 Blueprint 기본값과 별개로 `NavAgentProperties.can_crouch=False`가 저장되어 있어 이를 True로 수정하고, 캡슐 앉기 높이 58cm를 맵에도 저장했습니다.

| 상태 | 걷기 | Shift 이동 |
|---|---:|---:|
| 서기 | 120 | 600 |
| 앉기 | 90 | 360 |
| 서서 견착 | 60 | 120 |
| 앉아서 견착 | 45 | 72 |
| 정조준 | 120 / 앉으면 90 | 동일 |

- 이동 중 비조준 사격은 차단합니다(정지 허용 오차 2cm/s). 견착·정조준에서는 이동 사격이 가능합니다. 전력질주 중 발사 입력은 첫 발을 쏘지 않고 견착으로 바꿉니다. 계속 누르고 있으면 견착 상태에서 연사하고, 발사 입력을 놓으면 자동 견착을 해제합니다.
- 기본 확산 반각 0.15°, 이동 계수 0.0015°/(cm/s), 기존 자세별 배율은 유지합니다. 앉았을 때만 최종 확산각에 0.90을 곱합니다. 이는 게임상의 정확도 보너스이며 명중 확률을 고정으로 10%p 올리는 판정은 아닙니다.
- M4용 반동 기본값은 수직 0.46°/발입니다. 3인칭 카메라에는 0.30, 정조준에는 1.80 배율을 적용합니다. 나이·성별·키만으로 실제 반동 제어 수치를 계산했다고 주장하지 않으며, 155cm 성인 숙련 사수의 제어감을 표현하는 게임 튜닝입니다. 탄퍼짐 계산과 카메라 반동 계산은 분리됩니다.
- 3인칭 기본 암 길이는 469cm(기존 700cm의 67%), 견착 시 234.5cm(추가 50% 당김)입니다. 견착 시 옆 오프셋은 110cm, 높이는 20cm이며 보간합니다. 장애물 충돌에 따른 카메라 당김과 기존 1인칭/정조준 전환은 유지합니다. ExampleLevel의 설명용 TextRender 8개와 플랫폼 데모 Guide 위젯을 숨깁니다. 위젯 객체는 유지하되 Collapsed로 처리합니다.
- 탄도는 .223 Remington 55gr FMJ 기준으로 바꾸었습니다. 910m/s는 14.5인치 총열을 위한 게임 설정값이며, Hornady의 24인치 시험 총열 수치 988m/s를 그대로 적용하지 않았습니다. 공기저항은 공개 속도표로 맞췄고 영점은 50m입니다. 실제 M4 뒤 가늠자 구멍과 앞 가늠쇠 끝을 측정해 ADS 무기 위치/기울기를 맞추고, 카메라 전방 50m 조준점에 총구 높이 차와 중력 낙차를 보상합니다. 수치는 `Data/ballistics.json`, 기본 생성기는 `Tools/gen_m4_tuning.py`, 현재 50m 보정 생성기는 `Tools/gen_tfp_ballistics.py`입니다.
- 근거: [미 육군 M4A1 제원 — 30발 탄창, 14.5인치 총열](https://cpeground.army.mil/Equipment/Equipment-Portfolio/PM-SL-Portfolio/M4A1-Carbine/), [Hornady 탄도표](https://static.hornady.media/presscenter/docs/2024-Hornady-International-Catalog-UK.pdf).
- 검증: `Data/combat_validation.json`(Control Rig 접지), `combat_runtime.json`(일반 PIE에서 잔탄·재장전·이동 사격·앉기·효과), `combat_fresh_load.json`(실제 에디터 재실행 후 저장 확인). 이전 에셋 백업은 `Backups/CombatStance_20261115`, 이번 수정 전 백업은 `Backups/TFPMotionHUD_20261115`입니다. 이번 검증은 `tfp_runtime.json`(입력·보행·견착·탄수·카메라), `tfp_ads_runtime.json`(실제 가늠자 정렬·탄피), `tfp_main_level.json`(실제 시작 맵 C키·문구), `tfp_fresh_load.json`, `tfp_save.json`에 기록합니다. 실제 ExampleLevel에서 C키 앉기와 캡슐 58cm, 자세 가중치 0.9998, 안내 위젯 Collapsed, TextRenderActor 8개 숨김을 확인했습니다. HUD는 실제 HUD Blueprint를 Canvas Render Target에서 실행해 `Saved/Screenshots/WindowsEditor/TFP_HUD.png`로 확인했습니다. 조준 구멍은 후방 평면의 원형 정점에 원을 맞춰 중심을 구했으며 양 가늠자의 카메라 좌우/상하 오차는 0.001cm 미만입니다.

## 2026-11-15 추가 수정 (다리 보폭·조준·반동·재장전·특수이동)

- **달리기·걷기 보폭 축소:** 측정해 보니 발 사이 앞뒤 간격(발목 기준)이 걷기 최대 69cm, 달리기 최대 84cm였습니다. Control Rig가 발 목표를 골반 쪽으로 당깁니다(`StrideD`). 걷기 0.72배(28% 축소), 달리기 0.80배(20% 축소)이고, 값은 `gen_cr_params.py`의 `walk_stride`·`run_stride`입니다.
  - 발이 땅에서 미끄러지지 않게 `BS_FurinaStanding`의 걷기·달리기 샘플 재생률을 1/배율로 올렸습니다(`ue_tfp_stride.py`, 원래 값은 `Data/tfp_stride_base.json`).
  - 달리기는 이미 재생률 약 2배라 더 줄이면 발이 너무 빨리 돌아 20%까지만 줄였습니다. PIE 측정: 달리기 평균 49.0 → 40.8cm, 최대 83.7 → 67.0cm.
  - 이를 위해 걷기·달리기 중에도 다리 IK가 켜집니다(`Move`로 가중). 서 있을 때는 예전과 같습니다.
- **조준점:** 이전에는 탄이 항상 카메라 앞 50m 점을 향해서, 3인칭 견착(총구가 카메라에서 옆으로 약 1m)에서는 50m보다 가까운 곳을 쏠 때 크로스헤어에서 최대 1m 가까이 빗나갔습니다.
  - 비조준·견착(크로스헤어): 카메라 레이가 처음 맞는 점(`ImpactPoint`)으로 쏩니다. 아무것도 없으면 50m 점입니다.
  - 정조준(기계식 조준기): 크로스헤어 없이 조준선 위 50m 점으로 영점을 둡니다. 탄은 총구에서 나가 50m에서 조준선을 지나고, 가까운 곳은 총구 높이 차만큼 조금 아래에 맞습니다.
  - 낙차 보정각은 조준 거리에 비례합니다(50m 영점각 × 거리/50m, 0.2~4배). 수정은 `Scripts/Unreal/ue_fp_aim_recoil_fix.py`(BlueprintGraphEditor로 `K2Node_FPF_*` 노드를 수정)입니다.
  - PIE 측정(견착 3인칭, 단발): 탄이 조준선과 47.8m에서 만났습니다(오차 4cm).
- **초기 반동 120%:** `FurinaShotCount`(정수)가 연사 중 발수를 세고, 1~4발은 반동 ×1.2, 5발부터 ×1.0입니다. 발사 입력을 놓으면 0으로 돌아갑니다. PIE 측정: 처음 4발 평균 0.92°, 이후 0.70°(지터 ±12% 포함).
- **탄피 황동색:** `M_Brass`를 금속 1.0, 황금색(0.80, 0.56, 0.18), 거칠기 0.16으로 바꾸고, 반사 캡처가 없는 곳에서도 빛나도록 프레넬 림 발광을 더했습니다(`ue_brass_shine.py`).
- **재장전:** 템플릿 재장전(탄창을 뽑아 떨구고 허리에서 새 탄창을 꺼내 올려 끼움)의 왼손 궤적을 총 기준 좌표로 뽑아 곡선 `ReloadLX/LY/LZ`(0.9배, 최대 이동 17/37/34cm)로 `AS_Furina_FP_Reload`·`AM_Furina_FP_Reload`에 넣었습니다(`ue_reload_motion.py`). `CR_FurinaSecondary`가 왼손 목표에 더합니다. 총의 탄창 뼈 모션(`A_FP_WEP_AssaultRifle_Reload`)은 같은 시각에 재생됩니다.
  - 예전에는 왼손이 고정 탄창 위치로 보간만 했습니다. 템플릿 재장전 길이는 3.13초이고 잔탄 로직(3초)과 같이 동작합니다.
  - 한계: 총이 재장전 중 기울지는 않습니다(템플릿은 약 30° 기웁니다). 손가락은 뼈가 없어 모양을 바꿀 수 없습니다.
- **왼손 잡는 위치:** 손목을 총 기준 앞으로 2cm, 위로 1.2cm, 총열 쪽으로 0.8cm 옮겼습니다(`fp_rig.json`의 `left_grip_tweak`). 푸리나의 팔(39cm)이 짧아 손이 닿지 않는 위치는 IK가 끝까지 펴진 상태에서 멈춥니다. 3인칭은 기존 `tp_lback`을 유지합니다. 손가락 뼈가 없어 손 모양(펴진 손)은 그대로이며, 어색한 점은 스크린샷으로 알려 주시면 이어서 조정할 수 있습니다.
- **정조준 가늠자:** 정적 측정으로 가장 가까운 총 정점이 카메라에서 7.3cm이고 근접면(4cm) 안에 들어오는 정점은 0개입니다. 그래도 ini의 `NearClipPlane`은 재시작 후에만 적용되므로, `BeginPlay`에서 `r.SetNearClipPlane 2`를 실행합니다(`ue_near_clip_beginplay.py`). 정조준 중 반동 후퇴량도 30%로 줄였습니다(`KickGain`).
- **레일·레펠 등 특수이동 모션 복원:** TFP 보행으로 바꾸면서 `ABP_Furina`가 `IsMovingOnGround`가 참이면 번들 Manny의 모션(레일 그라인드·집라인·점프)을 버렸는데, 레일과 집라인 위에서도 참이었습니다. 이제 캐릭터가 0.05초마다 `FurinaSpecial` 플래그를 `UsingRail? OR UsingZipline? OR RailJumpActive?`로 설정하고, ABP의 `TFPGround`는 `IsMovingOnGround AND NOT FurinaSpecial`입니다(`ue_special_motion.py`). 이 경우 지상 블렌드가 번들 Manny의 포즈를 리타겟한 쪽으로 갑니다.
  - PIE에서 레일에 올라 탔을 때 그라인드 자세와 불꽃이 나오고 내려오면 공중 자세로 이어지는 것을 확인했습니다. 레펠(집라인)은 직접 타 보지 못했습니다.
- **작업 방식 메모:**
  - 이번 수정은 Python 그래프 API(`unreal.BlueprintGraphEditor`)로 직접 했습니다. `Tools/gen_fp_aim_tick_t3d.py`, `gen_fp_aim_t3d.py`(앉기·견착 속도)와 `Data/fp_aim_tick.t3d` 등은 이 방식 이전의 초안이라 적용하지 않았습니다.
  - 에디터가 Chrome에 가려지면 PowerShell로 에디터 창만 앞으로 가져옵니다. PIE가 아닐 때 Shift+F1을 누르면 도움말(Chrome)이 열리므로 PIE 중일 때만 누릅니다.
  - 확인 도구: `ue_leg_probe.py`, `ue_fp_shot_probe.py`, `ue_fp_zero_probe.py`, `ue_fp_shots_probe.py`, `ue_ads_clip_probe.py`, `ue_hand_grip_probe.py`, `ue_probe_reload_anim.py`, `ue_dump_char_graph.py`, `ue_dump_bp_graph.py`.

## 2026-11-15 추가 수정 2 (3인칭 카메라·달리기 보폭·재장전·총구 화염·정조준 사격)

- **3인칭 카메라(`ue_cam_closer.py`):** 암 길이 469 → 330(견착 234.5 → 165), `CameraBoom.TargetOffset` 위로 +55cm, 견착 옆 오프셋 110 → 60cm, 견착 높이 20 → 30cm. 옆 80cm로 해 봤더니 몸이 화면 왼쪽 가장자리에 잘려서 60cm로 줄였습니다. 견착 상태 PIE 화면에서 화면 중앙 크로스헤어가 몸과 겹치지 않고 캐릭터가 왼쪽 아래에 보이는 것을 확인했습니다.
- **달리기 발 속도(`gen_cr_params.py`, `ue_tfp_stride.py`):** 걷기 0.72, 달리기 0.92(`stride_warp`, `StrideD`). 0.80은 달릴 때 발이 너무 빨라 보여 0.92로 풀었습니다. `BS_FurinaStanding`의 걷기(120)/달리기(600) 샘플 재생 속도를 기준값(`Data/tfp_stride_base.json`)에서 다시 계산합니다.
- **재장전을 진짜 탄창으로(`Scripts/Blender/split_m4_mag.py`, `ue_m4_mag_import.py`, `ue_reload_mag.py`, `ue_mag_fix_links.py`):**
  - 이전 `prepare_m4.py`는 정점 상자 테스트로 탄창을 잘라 방아쇠울·탄창 삽입구까지 잘렸습니다. 이제 AR15 메시를 연결 성분으로 나눠 아래쪽까지 닿는 덩어리(탄창)만 분리합니다. 아무 면도 가로로 자르지 않습니다. 결과는 `SK_M4A1`(탄창 없음)과 `SM_M4Mag`(탄창만, 원점이 총 원점이라 장착 위치가 항등)입니다.
  - `ABP`의 `MagState` 커브(몽타주/시퀀스에 키)로 상태를 나눕니다. 손이 탄창을 잡고 빼면 총의 탄창을 숨기고 `BP_M4MagDrop`(물리)을 떨어뜨립니다. 새 탄창은 허리춤에서 손으로 가져온 뒤 총에 꽂습니다. 손 위치는 `ReloadLX/LY/LZ` 커브로 왼손 IK 목표를 움직입니다.
  - PIE에서 상태 열이 잡기 → 숨김(떨어진 탄창 정확히 1개) → 새 탄창 손에 → 장착으로 가는 것과 탄약 표시가 23 → 30으로 채워지는 것을 확인했습니다.
  - 알려진 문제와 미확인: 버려진 탄창이 땅으로 떨어지는지는 수치로 확인하지 못했습니다(`z`가 156에서 그대로). 손에 든 탄창의 모양은 1인칭 화면에서 거의 보이지 않아 눈으로 확인하지 못했습니다. `ue_mag_fix_links.py`는 상태 꼬리를 `FMG_SetLast`로 모으는 링크 오류(드롭 25개)를 고친 스크립트입니다.
- **총구 화염(`ue_m4_flash_real.py`):** `BP_M4Flash`에 흰 핵(`FlashCore`, `M_MuzzleFlashCore`), 38° 벌어진 꽃잎 4개, 옆으로 퍼지는 링, 더 밝은 조명을 넣었고 `BeginPlay`에서 총열 축 둘레로 0~360° 무작위 회전, 0.8~1.3배 무작위 크기를 줍니다. 수명은 0.045초 그대로입니다. 3인칭 연사에서 주황 별 모양 화염이 나오는 것을 확인했습니다.
- **정조준 사격은 조준경 기준(`ue_fp_sight_aim.py`):** 정조준에서는 탄이 조준경 선(뒤쪽 구멍 중심 → 앞쪽 가늠쇠 끝)의 50m 지점을 향합니다. 이 선을 사격 순간의 총 컴포넌트 변환으로 매번 계산하므로 반동으로 총이 튀어도 그 프레임의 조준경 선을 기준으로 쏩니다.
  - **미확인:** PIE에서 정조준 연사의 탄 방향을 수치로 재려 했으나(`ue_ads_sight_probe.py`) 정조준 중 탄 액터가 잡히지 않아 값을 얻지 못했습니다. 비조준 값은 조준경 기준이 아니라 의미가 없습니다. 연사 중 시야가 한 발당 약 1°씩 계속 올라가므로(마우스를 고정했을 때 17발에 거의 위를 봄), 반동 후의 조준경 화면보다 탄이 아래에 맞는 것은 설계상 남아 있습니다. 직접 쏴 보고 아직 아래로 가면 알려 주세요.
- **작업 방식 메모:** PIE 중 `register_slate_post_tick_callback` 프로브로 확인했습니다(`ue_mag_probe.py`, `ue_ads_sight_probe.py`). `remove_nodes`는 에디터가 죽어서 쓰지 않습니다. 실패한 부분 실행은 저장되지 않으므로 에디터를 다시 열어 재시도합니다.

## 2026-11-15 추가 수정 3 (정조준 탄 방향 버그·특수이동 사격 차단·달리기 발 속도·레펠 한 손)

- **정조준에서 탄이 뒤로 날아가던 버그(`ue_fp_sight_fix.py`):** 조준경 선 50m 지점을 만드는 `FPN_Sight50` 노드가 `vector * vector`로 만들어져 B 핀이 0,0,0이었습니다. 그래서 조준점이 뒷가늠자 자체가 되어 총구에서 카메라 쪽(뒤)으로 쐈고, 탄이 바로 사라져 PIE 프로브(`ue_ads_sight_probe.py`)에 한 발도 안 잡혔습니다(yaw 오차 180°). B를 `5000,5000,5000`으로 고쳤습니다. 수정 후 정조준 연사 10발의 방향 오차는 yaw·pitch 모두 ±0.07° 이내(발사 순간의 조준경 선 기준)이고 탄이 총구 앞 15m 지점에서 잡힙니다. 연사 중 조준경 선 자체가 발당 약 0.5~1°씩 올라가는 것은 반동이라 그대로입니다.
- **특수이동 중 사격 차단(`ue_special_nofire.py`):** `FurinaRifleShot` 맨 앞에 `NOT FurinaSpecial.IsActive` 분기를 넣었습니다(`FurinaSpecial`은 레일·집라인·레일 점프 중 `ue_special_motion.py`가 0.05초마다 켭니다). 연사 타이머도 이 이벤트를 부르므로 첫 발과 연사 모두 막히고 탄약도 줄지 않습니다. `ue_zip_force.py`로 플래그를 켠 PIE에서 발사 입력을 줘도 탄약이 30/120 그대로인 것을 확인했습니다.
- **달리기 발 속도(`ue_tfp_stride.py 0.72 0.92 3.5`):** 달리기 발의 걸음 수가 초당 약 4.8~5였는데, 달리기 발소리(Manny `Run_Fwd_Anim`의 `Footstep` 6개/1.9초)는 3.2걸음/초였습니다. 달리기 샘플(`BS_FurinaStanding`, y=600)의 재생 속도를 `애니 길이 × 3.5 / 2`로 바꿨습니다(앞 1.4, 뒤 1.17). PIE 측정(`ue_step_probe.py`): 발 교차 간격 Furina 0.28~0.30초(3.4걸음/초), Manny 0.30~0.32초(3.2걸음/초)입니다. 지면 속도 600cm/s에 비해 발이 조금 미끄러집니다(약 25%).
- **레펠 한 손 잡기(`ue_zip_flag.py`, `ue_build_cr.py`):** 번들에는 `One_Handed_Zipline_Anim`이 있고(왼손이 머리 위 z≈194, 오른팔은 옆으로 늘어짐), 이전에는 Control Rig가 양팔을 소총 IK로 덮어써서 그 모션이 사라졌습니다. 이제 캐릭터에 `FurinaZip` 플래그(Grind 컴포넌트 `UsingZipline?`로 0.05초마다 설정)가 있고, ABP의 `ModifyCurve_ViewState`에 `Zip` 커브(0/1)가 추가됩니다. `CR_FurinaSecondary`는 `Zip`일 때 왼팔 IK 가중치를 0으로(애니메이션의 머리 위 손잡이 자세 유지), 오른손목을 오른쪽 엉덩이 앞 `(-22, 28, 100)`(메시 공간 cm)로 보내 한 손으로 소총을 듭니다(`fp_rig.json`의 `poses.zip_right_hand`로 조정 가능). `ue_zip_hand_probe.py`로 `Zip`을 강제했을 때 오른손목이 정확히 그 좌표에 오는 것을 확인했습니다.
  - **미확인:** 실제로 레펠(집라인)을 타서 확인하지는 못했습니다. `ue_zip_hold.py`로 풀리 위치에 캐릭터를 붙여 봤지만 `UsingZipline?`가 켜지지 않아(진짜 잡기가 아님) 실제 탑승 자세는 보지 못했습니다. `UsingZipline?`가 실제 레펠 중 참이 되는지, 왼손이 손잡이에 닿는지는 직접 타서 봐야 합니다.
- **도구:** `ue_tp_player.py`(순간이동), `ue_zip_force.py`(플래그 강제), `ue_zip_state_probe.py`·`ue_zip_series_probe.py`(상태 기록), `ue_save_all.py`(더티 에셋 저장). 에디터가 다른 창에 가려지면 `UnrealEditor.exe` 창을 PowerShell `SetForegroundWindow`로 앞에 가져옵니다(복원은 `ShowWindow` 9가 아니라 3으로 최대화).

## 2026-11-15 추가 수정 4 (버린 탄창 낙하·3인칭 총열 잡기·서 있을 때 휴식 자세)

- **버린 탄창이 바닥까지 떨어지게(`ue_mag_box_collision.py`, `ue_mag_drop_fix.py`, `ue_mag_drop_fix2.py`):** `ue_drop_probe.py`로 보니 버린 탄창(`BP_M4MagDrop`)이 바닥을 뚫고 z=-20000까지 떨어져 공중에서 사라졌습니다. 원인은 `SM_M4Mag`의 볼록(convex) 충돌체였고, 메시 경계 상자 하나로 바꿨습니다. 이제 바닥(z≈51.5)에 닿아 멈추고 20초 뒤 사라집니다. 물리 채널은 PhysicsBody 객체로, Pawn·시야·카메라·WorldDynamic은 무시합니다.
- **탄창에 총알이 박히던 문제(추정):** 총알 구체(`BP_FurinaBullet.Bullet`)가 BlockAllDynamic이라 모든 물리 바디를 막았고, 이제 바닥에 놓인 버린 탄창에 걸려 박힐 수 있었습니다. 총알이 PhysicsBody 채널을 무시하도록 했습니다. 시각적으로 재현해 확인하지는 못했고, AR15 탄창 메시 자체에는 총알 모양이 없는 것을 Blender 렌더(`render_m4_mag_view.py`, `Data/renders/m4_mag_view.png`)로 확인했습니다.
- **3인칭 왼손 총열 잡기:** 이전에는 3인칭에서 왼손목이 소총 좌표 y=-11(권총손잡이 옆, 탄창 뒤)에 있었습니다. 팔 길이가 39cm뿐이라 총열 쪽으로 손을 뻗을 수 없어서, 3인칭 총 위치를 몸쪽으로 15cm 당기고(`poses.tp_hip_d`/`tp_sh_d`의 y 21.07 → 6.07) 왼손 뒤로 빼는 양을 21 → 13.5cm(`tp_lback`)로 줄였습니다. 이제 왼손목이 소총 y=+1.4로 핸드가드 시작 부분에서 쥐고 손바닥은 약 +7~9에 놓입니다. 개머리판 끝은 몸 안쪽으로 몇 cm 겹칩니다. 총열 끝쪽으로 더 나가려면 팔 길이 제약 때문에 개머리판을 더 파묻어야 합니다. 변경 전 값은 `Data/fp_rig.before_barrel_grip.json`입니다.
- **서 있을 때 휴식 자세(`ue_build_cr.py`, `poses.rest`):** 3인칭에서 정지·비조준·재장전 아님일 때 소총을 가슴 앞 대각선으로 듭니다(총구가 위·앞, 개머리판이 아래, 양손은 총에 그대로). 가중치 `RestW = TpW × NotAim × (1-Move) × (1-Reload)`로 부드럽게 전환하고, 걷기·조준·재장전이 시작되면 풀립니다. 값은 `poses.rest`(yaw 30°, pitch 30°, 오프셋 [-3, 15, -30])입니다. PIE 옆모습에서 소총이 가슴 앞 대각선에 놓이는 것을 확인했지만, 사진처럼 정확히 같은 모양은 아니라 각도는 `rest` 값으로 조정할 수 있습니다.

## 2026-11-15 추가 수정 5 (왼손-총 틈·3인칭 정조준 지연·휴식 자세 총구 아래)

- **1인칭 왼손이 핸드가드에서 떠 있던 틈(`Data/fp_rig.json`의 `left_grip_tweak`):** `ue_hand_grip_probe2.py`로 재 보니 허리 자세에서 왼손목 목표가 팔 길이(39.2cm)보다 약 3cm 멀어 IK가 끝까지 뻗고 멈췄고, 손목이 핸드가드(폭 x -1.9~2.2, 높이 z 2.8~7.1) 아래 왼쪽 약 2.6cm에 떠 있었습니다. 목표를 소총 좌표 (3.2, 12.6, 2.0)(팔이 닿는 범위)으로 옮겼습니다(`left_grip_tweak` = [-1.4, -1.87, 2.23], 3인칭 손 위치는 그대로 유지하려고 `tp_lback` 13.5 → 9.6). PIE 1인칭에서 손바닥과 손가락이 핸드가드 아래·옆면을 감싸는 것을 확인했습니다. 변경 전 값은 `Data/fp_rig.before_gap_rest.json`입니다.
- **3인칭 정조준이 오래 걸리던 버그:** `ue_ads_time_probe.py`로 PIE에서 우클릭 탭 후 조준선 정렬까지를 쟀더니 약 1.3초(시점은 0.03초에 1인칭으로 바뀌지만 소총이 가슴 앞 휴식 자세에서 서서히 올라옴)였습니다. 휴식 자세 가중치 `RestW`가 5/s로만 줄어든 것이 원인이었고, `RestWF = RestW × NotAim`(조준 가중치는 14/s)을 자세 혼합에 쓰도록 바꿨습니다. 수정 후 우클릭 → 조준선 정렬까지 약 0.25초입니다.
- **휴식 자세를 총구 아래로(`poses.rest`):** 소총을 몸 앞에서 대각선 아래로 듭니다(총구는 왼쪽 아래, 개머리판은 오른쪽 가슴 앞). yaw -60°(왼쪽), pitch -50°(아래)이고, 오른손은 배 앞 권총손잡이, 왼손은 핸드가드 시작 부분입니다. 값은 `Data/m4_geometry.json`으로 양손이 팔 길이 안(오른쪽 31cm, 왼쪽 35cm)에 들어가고 개머리판이 가슴 타원에 파고들지 않도록 계산했습니다. 위치 기준을 눈(머리 숙임에 따라 움직임)에서 오른쪽 어깨 관절(`Right-arm`)로 바꿨고 오프셋은 [21.07, 22.51, -24.86]입니다. PIE 정면 캡처로 사진과 비슷한 모양(오른쪽 어깨 앞에서 왼쪽 아래로 향하는 소총)을 확인했습니다. 사진과 완전히 같지는 않아서 `rest`의 yaw/pitch/off로 조정할 수 있습니다.
- **저장 누락 수정:** `Data/hair_stage_only` 파일이 있으면 `ue_build_cr.py`는 컨트롤 릭을 만들기만 하고 저장하지 않습니다. 그래서 휴식 자세(`RestW`) 노드가 디스크 파일에 없고 에디터 메모리에만 있었습니다. 빌드 뒤에 `ue_force_save_cr.py`(`save_loaded_asset(.., False)`)를 실행해 저장하고, `Content/Furina/CR_FurinaSecondary.uasset`에 `RestWF`·`RArmXf` 등이 들어 있는 것을 파일에서 확인했습니다. 컨트롤 릭을 다시 빌드한 뒤에는 항상 `ue_force_save_cr.py`를 실행해야 합니다.
- **도구:** `ue_ads_time_probe.py`(정조준 전환 시간), `ue_hand_grip_probe2.py`(손 본 이름·소총 정점 거리), `ue_eye_probe.py`(눈·어깨·손목 위치), `ue_api_find.py`(파이썬 API 이름 검색).

## 2026-11-15 추가 수정 6 (쉬는 자세 허리 펴기·발사 입력 시 기존 3인칭 사격 자세)

- **허리 펴기(`poses.rest.back_deg`):** 쉬는 자세에서 상체가 앞으로 숙여져 있었습니다(`ue_spine_probe.py`: 엉덩이→머리 앞기울기 13.8°, Spine→Chest 20°). 컨트롤 릭이 쉬는 자세 가중치(`RestWF`)만큼 Spine·Chest를 메시 X축으로 각각 6° 뒤로 젖힙니다(자식 본 포함, 팔을 놓기 전에 실행). 측정 결과 엉덩이→머리 앞기울기가 13.8° → 5.2°로 줄었고 PIE 정면 캡처에서 허리가 펴진 것을 확인했습니다. 다른 자세에는 적용되지 않습니다. 값은 `poses.rest.back_deg`(Spine·Chest)로 조정합니다.
- **발사 입력이 있으면 기존 3인칭 사격 자세(`ue_fire_hold.py`):**
  - 캐릭터 BP: `FurinaRifleShot`(발사 타이머가 첫 발과 연사마다 부르는 이벤트) 맨 앞에서 변수 `FurinaLastFire`에 게임 시간을 기록합니다(제한 조건보다 앞이라 탄이 없거나 막혀도 입력이면 기록).
  - 0.05초마다 도는 뷰 타이머가 `FurinaFireHold` 컴포넌트를 `(지금 − FurinaLastFire) < 2.5초`로 켜고 끕니다. ABP의 `ModifyCurve_ViewState`가 이를 `FireHold` 커브로 내보냅니다.
  - 컨트롤 릭은 `FireHold`가 켜지면 쉬는 자세를 끄고(`NotFire`, 14/s로 빠르게 나가고 5/s로 느리게 돌아옴) 기존 3인칭 소총 자세로 바꿉니다.
  - PIE 측정(`ue_fire_hold_probe.py`): 발사 이벤트 후 0.1초 안에 총구 각도가 -50° → +3°(앞)로 바뀌고, 마지막 입력 후 약 2.4초 뒤 쉬는 자세로 돌아가기 시작해 약 1초에 걸쳐 복귀합니다. 유지 시간은 `py ue_fire_hold.py <초>`로 바꿉니다. 직접 마우스 클릭으로 연사한 것은 확인하지 못했고, 같은 이벤트를 스크립트로 불러 확인했습니다.
- **빌드 후 저장:** 컨트롤 릭을 다시 만들면 `ue_force_save_cr.py`로 저장합니다(위 "저장 누락 수정").
- **도구:** `ue_spine_probe.py`, `ue_fire_hold_probe.py`, `ue_fire_hold.py`, `ue_force_save_cr.py`, `ue_api_dir.py`.

## 2026-11-15 추가 수정 7 (1인칭 총열 받치는 손 흔들림)

- **원인(`ue_lhand_probe.py`):** 왼손 목표(소총 좌표 (3.2, 12.6, 2.0))가 왼쪽 어깨에서 39.2cm 팔 길이 한계에 걸쳐 있었습니다. 걷기·대기 애니메이션이 어깨를 앞뒤로 움직여 목표가 닿았다 안 닿았다 하면서 손이 핸드가드를 따라 미끄러졌습니다. 수정 전 1인칭 걷기에서 소총 기준 손목 위치의 표준편차는 총열 방향 2.7cm(대기 중에도 0.29cm)였습니다.
- **수정(`ue_build_cr.py`, `LSh*` 노드):** 팔 IK 직전에 왼쪽 어깨 관절(`Left-arm`)을 목표 쪽으로, 거리가 `poses.left_reach_max`(기본 37cm)를 넘는 만큼만 당깁니다(자식 본 포함). 팔에 항상 여유가 있어 손이 총에 붙어 있습니다. 레펠 중(`Zip`)에는 `ZipInv`로 꺼집니다.
- **측정:** 수정 후 1인칭 대기·걷기(120cm/s)에서 소총 기준 손목 위치가 (3.2, 12.6, 2.0)에서 표준편차 0.000으로 고정됩니다. 전력질주와 연사 중 측정은 하지 못했습니다(프로브가 중간에 3인칭 전환/발사대에 걸려 무효). 시각 확인은 1인칭 정지 화면에서만 했습니다.
- 컨트롤 릭 재빌드 후 `ue_force_save_cr.py`로 저장했고 파일에 `LShSet`이 들어 있는 것을 확인했습니다.

## 2026-11-15 추가 수정 8 (견착 사격 자체 오차, 현재 1%)

- **현재 값: 견착 1%, 비조준(허리) 3%, 정조준 0%**(`py ue_shoulder_error.py 1 3`; 견착 반각 0.573°, 비조준 1.718°). 오차 = 정조준이면 0, 아니면 견착 ? 1% : 3%를 원뿔 반각에 더합니다(`FPN_ShErrSel`·`FPN_ShErrOuter`). 아래 5% 설명과 측정값은 처음 적용했던 값 기준입니다. 비조준 28발 측정(`ue_shoulder_err_probe.py hip 28`)에서 대부분 약 2° 안이었지만, 반동으로 조준점이 바뀌고 카메라와 총구 위치 차이(시차)가 섞여 깨끗한 측정은 아니고, 첫 발이 3.96°로 크게 벗어났습니다. 견착 1%는 다시 측정하지 않았습니다.

- **견착(우클릭 길게, `FurinaShoulder` 활성)이고 정조준이 아닐 때** 탄퍼짐 원뿔 반각에 `atan(0.05) = 2.862°`를 더합니다(`ue_shoulder_error.py`, 캐릭터 BP `FPN_ShErr*` 노드, 자세 배율·앉기 배율을 곱한 뒤에 더함). 조준점 방향을 기준으로 거리의 5%(10m에서 최대 0.5m, 50m에서 2.5m) 반지름 원 안에 균일하게 흩어집니다. 비조준·정조준은 그대로입니다. 퍼센트는 `py ue_shoulder_error.py <퍼센트>`로 바꾸고 0이면 오차가 없어집니다. 5%를 "거리 대비 편차"로 해석한 것입니다.
- **PIE 측정(`ue_shoulder_err_probe.py shoulder 28`):** 견착 28발의 편차 평균 중심에서의 흩어짐은 평균 1.4°, 최대 2.4°(약 4.2%)였고 비조준 기준선(5발)은 최대 0.55°였습니다. 3인칭 견착 카메라가 총과 떨어져 있어 조준선 기준 쏠림(요 +1°, 피치 +1.7°)이 따로 있습니다.

## 2026-11-15 추가 수정 9 (자체 제작 HUD, 탄종 제거)

- **이전 HUD:** 제공받은 이미지(`T_M4HUDFrame`, `M_M4HUDFrame`)를 그대로 쓰고 숫자만 글자로 덮었습니다. 이미지에 인쇄된 ".223 Remington"(탄종)이 같이 나왔습니다. 이 에셋은 지우지 않고 더 이상 쓰지 않습니다.
- **새 HUD(`ue_hud_build.py`, `ue_hud_wire.py`):**
  - `M_FurinaHUD`(Custom HLSL 한 노드)가 오른쪽 아래 패널 전체를 그립니다: 양 모서리를 사선으로 자른 반투명 판, 우리 M4 모델에서 뽑은 흰 실루엣(`T_M4HUDSilhouette`, `Scripts/Blender/render_m4_hud_silhouette.py`로 SK_M4A1 + SM_M4Mag 측면을 렌더), 30칸 잔탄 막대, 7세그먼트 숫자(잔탄 크게, 예비탄 작게, 꺼진 획은 흐리게 남김).
  - **탄종 표시는 없습니다.** 무기 이름 "M4A1"만 글자로 표시합니다.
  - 잔탄이 8발 이하이면 잔탄 숫자와 막대가 주황색이 됩니다(예비탄은 그대로). 재장전 중에는 막대를 따라 빛이 흐릅니다.
  - `BP_FurinaHUD`는 매 프레임 `MPC_FurinaHUD`(Ammo, Reserve, Reloading)에 값을 쓰고 `M_FurinaHUD`를 그립니다(기존 크기·위치 계산 그대로: 화면 너비의 30%, 360~540px, 오른쪽 아래 24px).
  - 크로스헤어·정조준 분기·데모 안내 숨기기는 그대로입니다. 옛 DrawText 잔탄 문자열 노드들은 그래프에 연결이 끊긴 채 남아 있습니다(노드 삭제가 에디터를 죽이는 문제로 지우지 않음).
- **PIE 확인(고해상도 캡처):** 30/120, 6/120(주황, 막대 6칸), 재장전 중 막대 위 빛 이동을 확인했습니다. 재장전 중에도 숫자는 현재 잔탄을 보여 줍니다. 해상도가 낮은 화면(너비 < 1200)이나 정조준/다른 시점에서의 모양은 따로 보지 않았습니다.

## 2026-11-15 추가 수정 10 (앉아쏴 반동 -10% 확인, 엎드리기 추가)

- **앉아서 쏠 때 반동 -10%:** 이미 `STATE_MULT.crouch = 0.9`가 확산과 반동(수직·수평, 카메라 반동)에 똑같이 곱해지고 있었습니다. 이번에 코드는 바꾸지 않고 PIE로 측정만 했습니다(`ue_recoil_probe.py`, 3인칭, 비조준 24발): 서기 0.158°/발, 앉기 0.140°/발(0.89배), 엎드리기 0.118°/발(0.75배). 앉기 1발당 값이 ±15% 무작위라 측정 오차는 약 ±3%입니다.
- **엎드리기(Z 토글, `ue_prone_char.py`, `ue_prone_abp.py`, `ue_build_cr.py`):**
  - Z를 누르면 엎드리고 다시 Z를 누르면 일어섭니다. 엎드린 상태에서 C를 눌러도 일어섭니다(앉지 않고 섭니다). 키는 `IA_FurinaProne`(`IMC_FurinaStance`).
  - **구현:** CMC 앉기에 더 작은 캡슐을 씁니다(앉기 반높이 58 → 엎드리기 42, 캡슐 반지름과 같음). 시작할 때 UnCrouch 후 0.06초 뒤 Crouch를 호출해야 캡슐이 새 높이로 줄어듭니다. 상태는 BP 변수 `FurinaProneWant`와 플래그 `FurinaProne`(= Want && IsCrouching, 0.05초마다 갱신)입니다.
  - **이동:** 걷기와 Shift 이동 모두 40cm/s입니다(달리기 불가). 점프는 앉기와 같이 막힙니다. 걷기/Shift 속도 선택 노드(`K2Node_FPT_WalkSpd`/`RunSpd`) 뒤에 `Want ? 40 : 원래 값` 선택 노드를 끼웠습니다.
  - **반동 -25%:** `K2Node_FPF_CrouchMul` 뒤에 `Want ? 0.75 : 원래 값`을 끼웠습니다. 앉기와 같은 노드라 확산 각도에도 같은 배율이 곱해집니다(엎드리면 탄퍼짐도 25% 줄어듭니다).
  - **자세(컨트롤 릭 `CR_FurinaSecondary`, `poses.prone`):** `Prone` 커브(ABP `ModifyCurve_ViewState`)로 스켈레톤의 단일 루트 `Hips`를 발 기준으로 -90° 눕히고(`angle_deg`) 몸이 캡슐 중심에 오도록 (0, -70, 8)cm 옮깁니다. 머리를 80° 들어 앞을 보게 하고, Spine/Chest를 8°/10° 젖혀 가슴을 듭니다. 눕는 동안에는 쉬는 자세(`RestW`)가 꺼집니다.
  - **다리 동작:** 새 포복 애니메이션은 만들지 않았습니다. ABP가 엎드린 동안 앉기 대신 서기 블렌드 스페이스를 쓰게 해(`ProneNotAnd`), 40cm/s로 이동하면 걷기 다리 동작이 낮은 속도로 섞여 번갈아 다리를 움직입니다. 팔은 기존 IK로 소총을 앞에 듭니다.
  - **PIE 확인:** 엎드린 3인칭(옆모습 고해상도 캡처), 이동 속도 40 고정, 1인칭 시점에서 소총과 손이 정상으로 보임, Z/C로 서기 복귀(캡슐 96, 속도 120).
  - **한계:** 몸통과 팔·다리가 땅에 파묻히는지, 벽·낮은 구조물과의 충돌, 엎드린 채 조준(견착/정조준)과 재장전은 따로 보지 않았습니다. 엎드릴 때 동작이 순간 이동이 아니라 CR 가중치(4/s)로 부드럽게 눕습니다. 캡슐은 높이 84cm, 반지름 42cm라 몸이 캡슐 밖으로 앞뒤로 길게 튀어나옵니다.

## 2026-11-15 추가 수정 11 (엎드리기에 'Free Crawl Animation' 에셋 적용)

- **에셋:** `Content/Free_Crawl_Animation`(UE5 Manny 스켈레톤 `SK_Mannequin`, 애니메이션 10개: Prone_Idle, Fwd_Loop L/R, Fwd_Start L/R, Fwd_Stop L/R, Stand_To_Prone, Prone_To_Stand, Idle). 이 폴더는 원본 그대로 두었습니다.
- **리타깃(`ue_crawl_retarget.py`):** `IK_CrawlManny`(`IK_TFPManny` 복사, 소스 메시만 이 팩의 `SKM_Manny_Simple`)와 `RTG_CrawlToFurina`(`RTG_TFPToFurina` 복사)로 10개를 `/Game/Furina/Crawl/AS_Furina_Crawl_*`에 만들었습니다(길이: 루프 1.0초, 시작 2.63초, 정지 1.63초, 서기↔엎드리기 2.5초).
- **제자리 루프(`ue_crawl_inplace.py`):** Furina 스켈레톤은 루트가 `Hips` 하나뿐이라 팩의 루트 모션이 Hips 이동으로 들어가 있었습니다(루프 1초에 앞으로 61cm → 반복마다 되돌아감). 한 사이클(왼팔·오른팔·양발이 모두 한 번씩)인 `Fwd_Loop_L`을 복제해 `AS_Furina_Crawl_Move`를 만들고 Hips Y 이동의 선형 성분을 뺐습니다. 그 61cm/s가 발·손이 미끄러지지 않는 포복 속도라 엎드린 이동 속도를 40 → **61cm/s**로 바꿨습니다(`ue_prone_speed.py`).
- **ABP(`ue_crawl_abp.py`):** `ProneMoveBlend`(`Prone_Idle` ↔ `Crawl_Move`, 알파 `TFPProneMove` = 속도 5~30cm/s → 0~1)를 `ProneBlend`(알파 `TFPProne` = 엎드림 플래그를 7/s로 보간)로 기존 걷기/앉기 포즈와 섞어 FP 레이어 블렌드의 기본 포즈로 넣었습니다. 변수 `TFPProne`, `TFPProneMove`는 이벤트 그래프(`CacheTFPProne`, `CacheTFPProneMove`)에서 매 프레임 갱신합니다.
- **컨트롤 릭:** 이전 절차적 눕히기(`poses.prone`)는 값을 0으로 중립화했고(이전 값은 `poses.prone_procedural_backup`) 코드는 남겨 두었습니다. 팔 IK·소총·쉬는 자세 끄기 등은 그대로 동작합니다.
- **PIE 확인:** 엎드리면 팔꿈치로 상체를 받치고 소총을 앞에 둔 엎드려쏴 자세가 되고, 이동하면 포복 루프가 돌며 속도 61cm/s로 고정됩니다(3인칭 고해상도 캡처).
- **한계:** `Stand_To_Prone`, `Prone_To_Stand`(각 2.5초)와 `Start`/`Stop` 클립은 쓰지 않았습니다. 서기 ↔ 엎드리기는 약 0.4초 보간이라 몸이 빠르게 눕고 일어섭니다. 포복 중 한쪽 다리가 공중으로 꽤 높이 들리는 프레임이 있습니다(Furina 다리 비율로 리타깃한 결과). 뒤·옆 이동용 클립이 없어 옆/뒤로 움직여도 같은 앞 포복 동작이 재생됩니다.

## 2026-11-15 추가 수정 12 (포복 골반 회전 절반·엎드렸을 때 망토 내려앉기)

- **골반 회전 절반(`ue_crawl_inplace.py [배율]`, 기본 0.5):** `AS_Furina_Crawl_Move`의 Hips 회전은 루프 평균 회전을 중심으로 흔들립니다. 평균(눕는 자세)은 그대로 두고 흔들림만 배율로 줄였습니다. 평균에서 가장 크게 벗어나는 각도가 17.4° → 8.7°입니다(`crawl_inplace.json`). 값을 바꾸려면 배율을 주고 다시 실행합니다.
- **망토/치마 내려앉기(`poses.prone.cape`, `ue_build_cr.py`, `ue_cape_probe.py`):** 허리에 걸린 `HB*` 체인(허리 둘레 `HB1_*` 9개, 뒤쪽 `HB2_0_1`·`HB3_0_1`·`HB4_0_1` 3개, 뒤쪽 두 개는 길이 75~90cm)이 서 있을 때 등 뒤로 늘어진 모양 그대로 몸이 눕는 바람에 다리 위 공중으로 25~45° 솟아 부채처럼 펼쳐졌습니다. 엎드린 대기 자세를 PIE에서 측정(`cape_probe_prone.json`)해 체인 방향이 거의 수평(발 쪽, 약간 아래: `cape_target_z` -0.15)이 되도록 루트 본별 회전각(30~54°, X축 기준)을 계산했고, 컨트롤 릭이 엎드림 가중치만큼 각 루트 본을 돌립니다(체인 전체가 따라감). PIE 3인칭 옆 캡처에서 망토가 등과 다리 위로 낮게 눕는 것을 확인했습니다.
- **한계:** 포복 중에는 일부 가는 띠가 위로 펄럭이는 순간이 있습니다(이동 속도에 따른 기존 천 흔들림). 서 있다가 엎드리는 전환 때 망토가 몸을 통과해 눕는 순간이 있을 수 있고 그 부분은 따로 보지 않았습니다. 망토 각도는 서 있는 기준 모양에서 한 번 측정한 값이라 애니메이션에 따라 다리와 약간 겹칠 수 있습니다.

## 2026-11-15 엎드리기 일시 비활성화

- **현재 엎드리기는 꺼져 있습니다.** Z 키는 그대로 매핑돼 있지만 캐릭터 BP의 입력 이벤트(`FPN_ProneToggle.Started`)와 토글 로직(`FPN_ProneBranch`) 사이 연결을 끊었습니다(`ue_prone_enable.py off`). PIE에서 Z를 눌러도 앉기/캡슐/속도가 바뀌지 않는 것을 확인했습니다.
- 캐릭터 노드, ABP의 엎드림 상태(`TFPProne`, `Prone` 커브), 컨트롤 릭 엎드림 블록(망토 보정 포함), 크롤 에셋(`Content/Furina/Crawl`, `Free_Crawl_Animation`)은 지우지 않고 그대로 있습니다. 엎드리지 않을 때는 이 값들이 0이라 다른 동작에 영향이 없습니다.
- **다시 켜기:** `py ue_prone_enable.py on` (PIE를 끄고 실행).
- `IMC_FurinaStance`의 Z 매핑을 파이썬으로 빼려다 저장이 실패해(PIE 중이었음) 디스크 파일은 그대로 Z가 매핑돼 있습니다. 메모리의 매핑은 다시 맞춰 놨습니다.

## 2026-11-15 추가 수정 13 (수직/오르막 집라인 한 손 잡기·집라인 왼팔 곧게)

- **수직·오르막 집라인에서 한 손으로 안 잡던 이유:** 번들은 이런 집라인(액터 태그 `Vertical Zipline`)을 `Grind_Rail_Component_BP.UsingZipline?`만이 아니라 `Platformer_Component_BP`의 `Zipline Actor`로도 처리해서, 그쪽에서는 `FurinaZip`·`FurinaSpecial` 플래그가 켜지지 않았습니다(`ue_zip_graph_search.py`, `ue_zip_vars.py`). `ue_zip_vertical_flag.py`로 두 플래그에 `IsValid(Zipline Actor) AND NOT IsMovingOnGround`를 OR로 추가했습니다(`FPN_ZipVert*` 노드). 지상 조건은 변수가 타고 난 뒤에도 안 비워질 경우 플래그가 계속 켜져 있는 것을 막는 안전장치입니다. 실제 수직 집라인을 타서 확인하지는 못했습니다.
- **오르막/수직 집라인 클립은 양손 클립입니다**(`Zipline_Up_1/2`, `Zipline_Down_1`: 양 손이 머리 위 x ±28). 애니메이션에 맡기던 왼팔을 이제 컨트롤 릭이 직접 잡습니다(`LHPosZip`·`LHRotZip` 노드): 타는 동안 왼손은 왼쪽 어깨 바로 위 (0, 9, 37.5)cm(`poses.zip_left_hand_off`, 팔 길이 39.2 중 38.6)에 두어 팔이 거의 곧게 펴지고 손목 회전은 애니메이션 값을 유지합니다. 오른손은 이전처럼 허리 옆에서 소총을 한 손으로 듭니다. 원래 한 손 클립에서 왼팔 팔꿈치가 33cm 옆으로 벌어져 있던 것도 같이 곧게 펴집니다.
- **PIE 확인(`ue_zip_force.py`로 양손 클립 `Zipline_Up_1_Anim`을 강제 재생):** 왼쪽 어깨 (11.7, -8.7, 131.8) → 팔꿈치 (10.8, -0.6, 151.4) → 손목 (11.7, 0.3, 169.3)로 팔이 거의 수직으로 곧게 펴지고(상완 21.2 / 하완 17.9cm), 오른손목은 (-18.9, 19.9, 107)로 허리 옆에 있습니다.

## 2026-11-15 배경 음악 제거, 재장전 HUD 점 채우기

- **배경 음악 제거(`ue_remove_bgm.py`):** `ExampleLevel`의 `AmbientSound` 액터는 `3xBlast_The_Best_Move_Is_To_Keep_Going_Looped_Cue` 하나뿐이었고(자동 재생), 이 액터를 삭제하고 레벨을 저장했습니다. 오디오 에셋(`3DPlatformerGameBundle/Audio/Cues/...`)은 지우지 않았습니다. 다시 넣으려면 그 큐를 레벨에 끌어다 놓으면 됩니다. 발소리·집라인 소리 등 효과음은 그대로입니다. PIE로 소리를 직접 들어 확인하지는 않았고, 레벨에 `AmbientSound`가 남아 있지 않은 것만 확인했습니다.
- **재장전 중 HUD 점이 재장전 시간에 맞춰 채워지게(`ue_hud_build.py`, `ue_hud_wire.py`):** 이전에는 재장전 중 막대 위로 빛이 지나갔습니다. 이제 30칸이 0에서 30까지 재장전 시간(3초)에 맞춰 채워집니다. `BP_FurinaHUD`가 캐릭터의 `FurinaFinishReload` 타이머 경과 시간(`K2_GetTimerElapsedTime`)을 3.0으로 나눠 0~1로 제한한 `ReloadP`를 `MPC_FurinaHUD`에 쓰고, 머티리얼은 `saturate(ReloadP × 30 − i)`로 i번째 칸의 밝기를 정합니다(채우는 중인 칸은 부드럽게 켜짐). 재장전 중에는 잔탄이 적어도 주황이 아니라 기본 색입니다. PIE 확인: 재장전 시작 1.0초에 30칸 중 약 11칸이 채워졌습니다.

## 2026-11-15 정조준 속도 1.5배

- "정조준 속도"를 **정조준 자세로 들어가고 나오는 전환 속도**로 해석했습니다. 컨트롤 릭의 정조준 가중치(`AdsW`) 보간을 14/s → 21/s(1.5배)로 바꿨습니다(`ue_build_cr.py`, `poses.ads_blend`, 기본 21). 견착(`ShW`)은 14/s 그대로입니다.
- **현재 값은 5.25/s입니다.** 요청이 이어져서 21 → 42(2배) → 10.5(지금의 1/4) → 5.25(지금의 1/2)로 바꿨고, 처음 값 14의 0.375배입니다(시정수 약 0.19초, 0.6초 안에 95% 도달 예상). 다시 측정하지는 않았습니다. 아래 측정은 21/s일 때입니다.
- PIE 측정(21/s): 1인칭 허리 자세에서 정조준을 켜면 가늠자가 조준선에 0.1초 만에 3.9 → 0.3cm, 0.2초에 완전히 정렬됩니다.
- 이동 속도(정조준 중 걷기 120cm/s)와 시야각 전환(FOV 85→60은 즉시)은 바꾸지 않았습니다.

## 2026-11-15 정조준 중 V로 3인칭이 되던 버그

- **원인:** 정조준(ADS)은 1인칭 선호 컴포넌트 `FurinaFPWanted`를 켜서 1인칭으로 바꿉니다. V(`IA_FurinaViewToggle`)는 이 컴포넌트를 `ToggleActive`로 끄기 때문에, 정조준 중에 V를 누르면 1인칭 선호가 꺼져 정조준한 채로 3인칭이 됐습니다.
- **수정(`ue_view_ads_fix.py`, `FPN_ViewAds*` 노드):** V 입력을 `FurinaADS.IsActive`로 분기합니다. 정조준 중이면 시점은 1인칭으로 그대로 두고, 정조준을 풀고 돌아갈 시점(`FurinaADSRestoreTP`: 켜짐 = 3인칭으로 복귀, 꺼짐 = 1인칭 유지)만 뒤집습니다. 정조준 중이 아니면 원래대로 1인칭/3인칭을 바꿉니다.
- **PIE 확인(`ue_view_state.py`):** 3인칭에서 정조준 → 1인칭, 복귀 표시 켜짐. 정조준 중 V → 1인칭 유지, 복귀 표시 꺼짐. 정조준을 풀면 1인칭 유지. 정조준 아닐 때 V → 3인칭.

## 2026-11-15 캐릭터 외형 교체 작업: Joumae Saori (시도 후 푸리나로 되돌림)

- **현재 캐릭터는 푸리나입니다**(메시 `SK_Furina`, 배율 1.0). 요청에 따라 `py ue_saori_apply.py 155 furina`로 캐릭터 BP 템플릿과 레벨 인스턴스를 되돌렸습니다. 사오리 에셋(`/Game/Saori`, `FBX/Saori`)과 빌드 스크립트는 지우지 않고 남겨 두었습니다. 다시 쓰려면 `py ue_saori_apply.py 167 saori`.
- 적용이 안 되던 원인(기록): 캐릭터 BP의 메시 템플릿에는 `skeletal_mesh_asset` 속성을 `get_object`로 얻은 컴포넌트에 설정해야 하고, `skinned_asset`/`get_associated_object`로 바꾸면 컴파일 때 푸리나로 되돌아갑니다. 위 "미완/미확인 1"은 이 문제였고 고쳐서 PIE에서 사오리(키 167cm, 배율 1.1163)가 나오는 것을 확인한 뒤 되돌렸습니다.
- 아래는 되돌리기 전의 작업 기록입니다.

- **방식:** 사오리의 메시를 **푸리나 스켈레톤(240개 본, 이름·계층·바인드 포즈 그대로)에 스키닝**해서 `SK_Furina_Skeleton`, 리타깃된 모든 애니메이션, `ABP_Furina`, `CR_FurinaSecondary`가 수정 없이 동작하게 했습니다. 사오리 원본은 MMD 본 305개(일본어 이름)라서 그대로 쓰면 애니메이션·컨트롤 릭·소총 소켓을 모두 새로 만들어야 합니다.
- **`Scripts/Blender/build_saori_on_furina.py` → `FBX/Saori/Saori_cm.fbx`:** 푸리나 FBX(`Furina_cm.fbx`)의 아마추어를 쓰고, 사오리 관절을 푸리나 관절에 균일 배율 7.138 + 이동으로 맞췄습니다(관절 오차 1~3.5cm, 골반 6.5cm). 사오리 버텍스 그룹 57개를 MMD→푸리나 본 표로 합치고(손가락·꼬임본 포함, 치마·머리끈 등 표에 없는 본은 가장 가까운 매핑된 조상으로), 정점당 영향 4개로 제한했습니다. 36개 메시를 하나(`Body`, 38,598정점, 36 머티리얼 슬롯)로 합쳤습니다. 이 크기에서 사오리는 발바닥~머리 끝 149.6cm입니다(헤일로 제외).
- **`ue_saori_import.py`:** `/Game/Saori/SK_Saori`(스켈레톤 `SK_Furina_Skeleton`), 텍스처 7개(`T_Saori_*`), 머티리얼 인스턴스 36개(`MI_Saori_*`, 부모 `M_Furina_Opaque`/`M_Furina_Translucent`)를 만들었습니다. 원본 모델이 가리키는 `fac1.png`, `face5.png`, `lip.png`, `Saori_Original_Body2.png`는 폴더에 없어서 얼굴 보조 메시는 `Saori_Original_Face`, 옷은 `Saori_Original_Body`로 대신 붙였습니다(UV가 맞는지는 확인하지 못했습니다).
- **키 167cm(`ue_saori_apply.py 167`):** 푸리나 스켈레톤 기준 149.6cm → `FurinaMesh` 컴포넌트 상대 배율 1.1163(소총·1인칭 카메라 소켓도 함께 커짐). 캐릭터 BP 템플릿은 `SK_Saori`+1.1163으로 저장했습니다.
- **미완/미확인:**
  1. 레벨의 `ThirdPersonCharacter_BP_2`는 메시 에셋을 따로 덮어쓴 상태라 PIE에서 여전히 `SK_Furina`(배율만 1.1163)로 나옵니다. 덮어쓰기를 지우는 `reset_editor_property`를 넣었지만 다시 확인하지 못했습니다.
  2. 사오리가 화면에 제대로 나오는 모습, 관절 변형, 얼굴·눈 텍스처, 헤일로/모자/머리가 1인칭 카메라를 가리는지(Head 본 숨김은 그대로 동작할 것으로 보임)는 아직 보지 못했습니다.
  3. 사오리 메시에는 모프 타깃(눈 깜빡임)이 없고, 겉옷(`Coat`)의 고급 물리(트렌치코트처럼 찰랑이는 천)는 아직 만들지 않았습니다. 계획: 겉옷 버텍스를 푸리나 허리 둘레 `HB*` 체인 가중치로 옮기고 ABP에 체인별 AnimDynamics를 추가.
  4. 워킹 속도·보폭은 푸리나 기준이라 키가 11.6% 커진 만큼 발이 약간 미끄러질 수 있습니다.
- **되돌리기:** `py ue_saori_apply.py 155 furina`로 푸리나 메시·배율 1.0으로 되돌릴 수 있습니다(배율은 인수 무시).

아래 Honey Badger 관련 설명은 이전 구현 기록입니다. 현재 사용 값은 위 설정과 M4 데이터가 우선합니다.

## 폴더

| 폴더 | 내용 |
|---|---|
| `FBX/Furina_cm.fbx` | **현재 사용 중인 모델.** 예전 Unity 프로젝트의 `BlenderAlternate.fbx`(Furina)를 cm 단위로 다시 내보낸 것. 루트 스케일 없음 |
| `FBX/Variants/` | 테스트용 내보내기. `Furina_UE.fbx`는 Hips에 ×100 스케일이 걸려 다리 IK가 깨지던 옛 버전 |
| `Textures/` | 머티리얼 원본 텍스처 5장 (Face, HairDetail, HairSheen, Outfit, SkinHair) |
| `Scripts/Blender/` | FBX 정리·내보내기 (`blender.exe -b --python <script> -- <args>`) |
| `Scripts/Unity/` | Unity 씬에서 Furina 데이터 추출, idle 녹화 스크립트 |
| `Scripts/Tools/` | 일반 Python으로 실행하는 변환·생성·분석 도구 |
| `Scripts/Unreal/` | 언리얼 에디터 Output Log의 Cmd 칸에서 `py "<경로>"`로 실행 |
| `Data/` | 추출·측정 데이터, 생성된 AnimGraph 텍스트(`.t3d`), 각 스크립트의 결과 JSON |

## 언리얼 쪽 결과 에셋 (`/Game/Furina`)

- `SK_Furina`, `SK_Furina_Skeleton`, `Materials/`, `Textures/`
- `Retarget/IK_Manny`, `Retarget/IK_Furina`, `Retarget/RTG_Manny_To_Furina`: Manny 애니메이션을 Furina 관절로 리타겟. 다리는 양쪽 Limb IK
- `Anim/AS_Furina_Idle`: Unity에서 녹화한 옛 idle (10.5초 루프, 평지에 양발 접지 보정, 깜빡임 커브)
- `CR_FurinaSecondary`: 속도 비례 옷자락(HB 사슬 12개) + 머리카락(땋은 머리·옆머리·아호게) Control Rig
- `ABP_Furina`: 리타겟 포즈 ↔ 옛 idle을 `FurinaIdle` 커브로 블렌드 → Control Rig
- 캐릭터 BP 4개에 `FurinaMesh` 추가(Manny는 숨김 상태로 애니메이션만 계산)
- Manny `Idle_Anim`에 `FurinaIdle` 커브 추가 (idle 판정 신호)
- `Input/IA_CameraZoom` + `Default_IMC`의 MouseWheelAxis 매핑, `ThirdPersonCharacter_BP` 이벤트 그래프의 "Mouse wheel camera zoom (Furina)" 노드:
  휠 1칸당 CameraBoom 길이 ±60, 200~1600 사이로 제한 (값은 `Scripts/Tools/gen_zoom_t3d.py`의 STEP/MIN_LEN/MAX_LEN)

## 부드러운 머리카락 움직임 (2026-11-14)

- **대상:** 땋은 머리 `F_0..17_1_L/R`, 옆머리 `CF_1..2_L/R`, 아호게 `DM_0..5_1`.
- **출력:** `ABP_Furina`에서 `CR_FurinaSecondary`의 포즈를 최종 출력에 직접 연결합니다. 이전 AnimDynamics 5개는 보존하지만 출력 경로에서 제외했습니다. 겹친 물리·스프링·몸 충돌 제약이 머리카락을 튀게 만들던 처리를 없앴습니다.
- **속도:** 메시 컴포넌트 원점의 실제 수평 이동을 측정합니다. 골반·머리 애니메이션의 흔들림과 수직 낙하는 달리기 속도로 계산하지 않습니다. 6~600 cm/s를 0~1로 제한하고 보간 계수 3.8/s로 완충합니다(`HairFlow` 커브).
- **움직임:** 대기 중 작은 바람 → 걷기 → 달리기 순서로 진폭과 주기가 부드럽게 증가합니다. 위상은 연속으로 진행하며 양쪽 사슬에 작은 위상 차이를 둡니다. 뿌리는 작게, 끝은 크게 움직이고, 달릴 때 긴 머리의 뿌리는 최대 8도 뒤로 따라갑니다.
- **찰랑임(모든 관절 따라오기):** 각 머리 사슬의 `ChainHarmonicsPerItem`에 Pendulum을 켰습니다. 땋은 머리 18관절, 옆머리 2관절, 아호게 6관절이 각자 쉬는 방향을 약간 늦게 따라가서, 머리 회전과 발걸음 반동이 뿌리에서 끝으로 물결처럼 전달됩니다. 값은 `gen_cr_params.py`의 `PEND`에 있습니다. `stiff`가 클수록 덜 늦게 따라오고, `drag`가 작을수록 빨리 가라앉습니다. `min`/`max`는 뿌리와 끝의 지연 비율이고, `grav`는 약간의 처짐입니다. 출렁임이 과하다는 요청으로 처음 값(기본: 뿌리 0 → 끝 0.1)과 전체 따라오기의 중간으로 줄였습니다(땋은 머리 `max` .45, 옆머리 .45, 아호게 .27). PIE 측정값(땋은 머리 끝 기준): 대기 ±1.2cm, 걷기 ±4.3cm(전체 따라오기 때 ±9cm). 진동 축(Unwind)은 뼈 길이 축(Y)과 수직인 X축을 씁니다.
- **튜닝:** `Scripts/Tools/gen_cr_params.py`의 hair 프로필. `idle`은 정지 진폭, `amp`는 최고 속도에서 더할 진폭(rad/관절), `lift`는 뒤로 따라가는 각도, `rootAmp`는 뿌리 가중치입니다.
- **적용 순서:** `gen_cr_params.py <Data 경로>` → 에디터에서 `ue_build_cr.py` → `ue_apply_soft_hair.py`. 이전 `gen_t3d3.py` / `gen_t3d4.py`의 AnimDynamics 그래프를 다시 사용하면 마지막 적용 스크립트로 출력 연결을 복구해야 합니다.
- **검증:** `ue_validate_soft_hair.py`가 현재 메시의 cm 기준 포즈로 대기·걷기·달리기, 30/60 fps 전환, 움직임 범위와 본 길이를 검사합니다. `ue_verify_soft_hair_runtime.py`는 임시 PIE 검사 후 편집 모드와 기존 뷰포트 카메라로 돌아갑니다.
- **백업:** `Backups/HairSoftMotion_20261114/`.

## 눈 깜빡임 (Unity `UntitledCharacterIdle.UpdateIdleBlink` 타이밍 → `CR_FurinaSecondary`)

- **조건:** 대기·걷기·뛰기 상태와 관계없이 깜빡입니다. `FurinaIdle` 블렌드 값으로 눈 감김을 차단하지 않습니다.
- **간격:** 4~5초(TimeLoop 4.5초 + 사인 지터)입니다.
- **동작:** 감기 0.045초 → 유지 0.065초 → 뜨기 0.085초, 스무스스텝입니다.
- **출력:** `IdleBlink` 모프 커브를 설정합니다. 빌더가 Control Rig 커브와 스켈레톤의 morph-target 메타데이터를 유지합니다.

## 1·3인칭 전환과 소총 (2026-11-14)

- **원본:** `Downloads/blender_source_files_freefpstemplate`의 UE5 무료 FPS 템플릿. UE5 Manny 뼈대(89개)용 돌격소총 1인칭 모션 12개와 소총 메시, 소총 사격·재장전 모션이 들어 있습니다.
  - 소총 모델: "Low-Poly AAC Honey Badger" by TastyTony (https://skfb.ly/6SMsu), **CC BY 4.0**. 배포할 때 이 출처 표기를 유지해야 합니다.
- **조작:**
  - **V:** 1인칭과 3인칭을 전환합니다.
  - **좌클릭:** 누르고 있는 동안 연사합니다(800발/분, 예광탄과 탄 낙차는 아래 '조준·예광탄·탄도' 참고). 예전 단발 레이 판정(`IA_FurinaFire`)과 반동 없는 연사(`IA_FurinaFireAuto`)는 키 매핑을 해제해 그래프에 남아 있어도 동작하지 않습니다.
  - **우클릭:** 짧게 누르면 정조준을 켜고 끕니다. 길게(0.2초 이상) 누르고 있으면 견착합니다.
  - **R:** 재장전합니다. 왼손이 탄창으로 갔다가 돌아오고, 소총 탄창 모션도 함께 재생됩니다.
  - 1·3인칭 모두 항상 총을 들고 있으며, 화면 중앙에 크로스헤어가 있습니다.
  - 기존 번들의 `Direction_IA`(레일 방향 전환)도 좌클릭에 묶여 있어서, 레일 위에서는 둘 다 동작합니다.
- **분석 결과 (`Data/fp_template_inspect.json`, `fp_gun_hand.json`, `fp_measure.json`):**
  - 총은 모든 모션에서 오른손에 고정입니다(0.6cm 이하). 왼손도 재장전을 빼면 총에 고정입니다.
  - 그런데 푸리나는 Manny보다 28cm 작고 팔도 39cm로 짧습니다(Manny는 54cm). 그래서 리타깃만 하면 손이 허리 높이(105cm)에 옵니다.
  - Manny의 1인칭 모션은 카메라용으로 어깨가 왜곡돼 있어, 몸 기준 비율 변환을 쓸 수 없습니다.
- **구성:**
  - **총 위치:** `CR_FurinaSecondary`가 총 기준점을 목 기준 (오른쪽 8, 앞 18, 위 3cm)에 둡니다. 조준 피치(`AimPitch`)만큼 목을 축으로 회전하고, 사격 반동(`RifleKick`)에 따라 3cm 뒤로, 4° 위로 움직입니다. 양팔은 투본 IK로 총 손잡이와 총열 받침에 붙입니다. 재장전 중(`RifleReload`)에는 왼손이 탄창 위치로 이동합니다. 머리는 조준 피치의 절반만큼 따라 숙이거나 듭니다.
  - **손 모양:** 손목과 손가락은 1인칭 대기·걷기·달리기 모션(리타깃본)에서 가져옵니다. `ABP_Furina`의 손목 전용 레이어가 이 역할을 하고, 몽타주 슬롯 `DefaultSlot`은 여기에 있습니다.
  - **조준 피치:** AnimGraph 안의 순수 함수 체인(`TryGetPawnOwner → GetBaseAimRotation → Pitch`)이 `AimPitch` 커브를 만듭니다.
  - **캐릭터 BP:**
    - `FurinaRifle`(오른손목 소켓)과 `FPCamera`(머리 소켓, 눈높이)를 시작(Possessed) 시점에 부착합니다.
    - 1인칭에서는 머리 뼈를 숨기고(머리카락·모자 포함), 컨트롤러 방향을 바라봅니다.
    - 3인칭에서는 원래대로 이동 방향을 바라봅니다.
  - **HUD:** `BP_FurinaHUD`가 크로스헤어를 그립니다.
- **에셋 (`/Game/Furina/FP`):**
  - `Weapon/`: SK_AssaultRifle, 소총 모션 2개, 텍스처, MI
  - `Manny/`: 원본 모션 12개
  - `Anim/`: 푸리나 리타깃 12개, AM_Furina_FP_Fire / Reload
  - `BP_FurinaHUD`, `Input/IA_FurinaView`·`IA_FurinaFire`·`IA_FurinaReload`
- **적용 순서:**
  1. 에디터에서 `ue_fp_import.py`(가져오기 + 리타깃)를 실행합니다.
  2. 데이터 경로를 넣어 `ue_fp_measure.py`, `Tools/gen_fp_rig.py`를 실행합니다.
  3. `ue_build_cr.py`를 실행합니다.
  4. `Tools/gen_fp_abp_t3d.py`로 만든 노드를 ABP AnimGraph에 붙여넣고 `ue_fp_abp_connect.py`를 실행합니다.
  5. `ue_fp_character.py`를 실행합니다.
  6. `Tools/gen_fp_bp_t3d.py`로 만든 노드를 캐릭터 BP와 HUD 이벤트 그래프에 붙여넣습니다.
- **검증:** `ue_fp_probe.py`(부착·HUD·카메라)와 `ue_fp_timeline.py`(사격·재장전 커브, 손 위치)를 씁니다.
  - 양손은 총 기준으로 오차 0.1cm 이내에 있습니다.
  - 재장전 중 왼손은 총 기준 (4.6, 14.5, -0.2)에서 (0, 4, -9)로 이동했다가 돌아옵니다.
- **점프 중 총 단면 버그 수정:**
  - **원인:** 점프 모션이 머리를 앞으로 숙이게 해서, 머리에 붙은 1인칭 카메라가 앞으로 11cm, 아래로 19cm 움직였습니다. 총은 목 기준이라 그대로여서, 카메라와 총 사이가 4.7cm까지 가까워졌고 근접면이 총을 잘라 단면이 보였습니다.
  - **수정:** 총 기준점을 목에서 눈 위치(`Head × cam_head_local`, FPCamera와 같은 점)로 바꿨습니다(`g_off_eye` = 서 있을 때 같은 위치가 되는 오프셋). 조준 회전도 눈을 중심으로 돌고, 머리 조준은 팔 IK보다 먼저 실행됩니다.
  - **PIE 측정 (`ue_fp_clip_probe.py`):** 공중에서 카메라와 총의 최소 거리가 4.7cm에서 15.1cm로 늘었고, 달리기 점프는 19.8cm입니다.
- **달리기 총 기울이기:** 달리기 비율(`Run`, 걷기 120 → 달리기 600cm/s)에 비례해 적용됩니다. 총구가 안쪽(왼쪽)으로 30° 돌고, 총 윗면이 왼쪽으로 45° 기울며, 총구가 8° 내려갑니다. 총 전체는 허리 자세보다 왼쪽 2cm, 뒤 2cm, 아래 3cm로 옮겨져 가슴에 붙습니다(PUBG식 로우 레디). 정조준·견착 중에는 적용되지 않습니다. 3인칭에서도 같은 자세라 시점 전환이 이어집니다. 값은 `Tools/set_fp_poses.py`의 `SP_D`·`SP_Q`에 있습니다.
- **3인칭 강제:** 다음 경우에는 1인칭을 선택해 두었어도 3인칭으로 바뀝니다.
  - 레일 위(`Grind_Rail_Component_BP`의 `UsingRail?`)
  - 집라인(`UsingZipline?`)
  - 레일 점프 중(`RailJumpActive?`)
  - 공중에서 1200cm/s를 넘을 때(호밍 어택, 스프링, 점프대, 긴 낙하)
  - **유지·복귀:** 공중에서 강제된 3인칭은 착지할 때까지 유지됩니다. 착지하면 선택해 둔 시점으로 돌아갑니다. 일반 점프와 스프린트 점프(최고 약 920)는 1인칭이 유지됩니다.
  - **구현:**
    - V(`IA_FurinaViewToggle`)는 `FurinaFPWanted` 컴포넌트의 활성 상태를 '원하는 시점'으로 저장만 합니다.
    - `ReceiveControllerChanged`에서 시작한 0.05초 타이머(`FurinaViewUpdate`)가 원하는 시점과 강제 조건을 비교해 전환합니다.
    - 공중 유지는 '속도 + (1인칭이 아니면 10000) > 1200' 비교로 처리합니다.
    - 노드 생성기는 `Tools/gen_fp_view_t3d.py`와 `gen_fp_view_hold_t3d.py`이고, 설정은 `ue_fp_view_setup.py`입니다.
    - 예전 `IA_FurinaView`(직접 전환) 노드는 키 매핑을 해제해 동작하지 않습니다.
  - **PIE 측정:** 레일에 오르면 0.05초 안에 3인칭이 됩니다. 레일에서 뛰어내려 공중에 있는 동안은 3인칭이 유지되고, 착지하면 1인칭으로 돌아옵니다.
- **주의:** Python 스크립트에서 그래프 노드 객체를 전역 변수에 남기면, 이후 컴파일 때 에디터가 크래시합니다. 새 스크립트는 모두 함수 안에서 참조를 정리합니다.
- **백업:** `Backups/FirstPersonRifle_20261114/`

## 조준·예광탄·탄도 (2026-11-14)

- **우클릭 (`Scripts/Unreal/ue_fp_aim_setup.py`):**
  - `IA_FurinaADS`(Tap 0.2초)와 `IA_FurinaShoulder`(Hold 0.2초)가 같은 우클릭에 묶여 있습니다. 번들의 `Position_IA`(집라인 위아래)도 우클릭이라 집라인 위에서는 그대로 동작합니다.
  - **정조준(짧게):** 켜고 끕니다. 3인칭에서 켜면 1인칭으로 바뀌었다가, 끄면 3인칭으로 돌아옵니다(`FurinaADSRestoreTP`). 시야각은 85°에서 60°로 줄어듭니다.
  - **견착(길게):** 누르고 있는 동안 개머리판을 어깨에 붙이고 조준 방향을 바라봅니다. 놓으면 원래 회전 설정으로 돌아갑니다.
    - **3인칭 견착 카메라:** 카메라가 캐릭터 옆으로 `30 + 팔 길이 × 0.08`cm(기본 팔 길이 700에서 86cm), 위로 15cm 이동하고, 시야각이 90°에서 60°로 좁아집니다(1.5배 확대). 캐릭터 몸이 화면 중앙의 크로스헤어를 가리지 않게 하려는 것입니다. 보간 속도는 10입니다.
    - **방향:** 견착 전 카메라가 캐릭터의 어느 쪽에 있었는지로 정합니다(`FurinaShoulderLeft`). 카메라가 캐릭터 오른쪽 벡터 기준 20cm보다 더 왼쪽에 있으면 왼쪽 어깨, 그 외(정면 뒤 포함)에는 오른쪽 어깨입니다.
  - **이동 속도 (`Tools/gen_fp_aim_tick_t3d.py`, 캐릭터 Event Tick):**
    - 정조준 중에는 Shift와 관계없이 걷기 속도 120으로 고정됩니다.
    - 견착 중 걸으면 120이고, Shift를 누르면 달리기 600의 40%인 240입니다.
    - 조준을 풀면 그때 Shift 상태에 맞게 600 또는 120으로 돌려놓습니다(`FurinaSpeedCap` 플래그). Shift 판정은 `IsInputKeyDown(LeftShift)`입니다.
  - 상태는 캐릭터의 태그 컴포넌트 `FurinaADS`·`FurinaShoulder` 활성 여부에 저장됩니다. ABP는 이를 `AimADS`·`AimShoulder` 커브로 바꾸고(`ModifyCurve_AimState`), `CR_FurinaSecondary`가 허리 → 견착 → 정조준 자세로 부드럽게 보간합니다(AccumulateLerp 14/s).
  - **HUD:** 정조준 중에는 크로스헤어를 그리지 않습니다. 가늠자·가늠쇠가 조준점입니다. 정조준을 풀면 다시 나타납니다.
- **1인칭 총 자세 (`Scripts/Blender/rifle_geometry.py` → `Data/rifle_geometry.json`, `Tools/gen_fp_poses.py`·`set_fp_poses.py` → `Data/fp_rig.json`의 `poses`):**
  - 실제 총 메시 정점으로, 화면에 보이는 면적과 카메라 근접면에 잘리지 않는지를 계산해 자세를 골랐습니다. 팔 길이 안(38cm)에 있는 자세만 썼습니다.
  - **총 실제 크기 (2026-11-15):** 템플릿 총은 원조 AAC Honey Badger입니다. 위키백과 기준 개머리판을 편 길이가 740mm이고, 메시는 배율 1.0에서 74.8cm로 실물 크기입니다. 푸리나는 UE에서 약 165~172cm(모자 포함)라서, 예전 0.85배(63.6cm)는 실제 비율보다 작았습니다. 배율을 1.0으로 바꿨습니다(`gen_fp_rig.py`의 `SCALE`, `ue_fp_scale_setup.py`). 이전 값은 `Backups/FirstPersonRifle_20261114/fp_rig_scale085.json`에 있습니다.
  - 허리 자세는 눈 기준 (오른쪽 7, 앞 10, 아래 10cm)입니다. 실물 크기 총으로 화면 면적 13%, 가장 가까운 정점 7.4cm, 팔 도달 거리 38.4cm(팔 길이 39.2cm)입니다. 견착은 (오른쪽 4, 앞 10, 아래 11)입니다.
  - **3인칭 전용 자세:** 1인칭 카메라가 없을 때는 총을 얼굴에서 떼어 듭니다. 허리 자세에서 오른쪽 3, 아래 8cm(견착은 오른쪽 2, 아래 4cm)를 더합니다. `ABP_Furina`의 `ModifyCurve_ViewState`가 `ViewTP` 커브(FPCamera(태그 `FurinaFPCamera`)가 꺼져 있으면 1)를 만들고, CR이 이를 부드럽게 섞습니다. 정조준 중에는 적용하지 않습니다.
    - 눈과 가장 가까운 총 정점의 거리: 허리 7.4cm → 14.0cm, 견착 7.2cm → 10.8cm.
    - PIE에서 눈과 총 기준점 사이 거리는 1인칭 15.8cm, 3인칭 22.5cm였습니다.
  - **1인칭 달리기 흔들림:** 손 흔들림에 맞춰 달리기 루프(0.667초) 주기로 흔들립니다. 좌우 1.2cm(한 주기에 한 번), 상하 0.8cm(한 걸음마다), 롤 3°, 요 2°입니다. 달리기 휴대 가중치(`RunW`)에 비례하고, 정조준·견착 중에는 0입니다. 값은 `set_fp_poses.py`의 `BOB`에 있습니다.
  - 근접 클립면을 10cm에서 4cm로 줄였습니다(`Config/DefaultEngine.ini`의 `NearClipPlane=4.0`, 에디터 재시작 후 적용). 지금 세션에서는 콘솔 `r.SetNearClipPlane 4`로 적용합니다.
  - **정조준 가늠쇠 정렬:** PIE 화면에서 가늠자 구멍이 조준점보다 1.8° 위에 있었습니다. 총을 0.245cm 내리고 총구를 0.12° 들어, 가늠자 중심·가늠쇠 끝·조준점이 한 점에 맞게 고쳤습니다. 실물 크기로 바꿀 때는 내린 거리도 같은 비율로 키웠고(0.288cm), PIE에서 가늠쇠 끝이 화면 중앙에 오는 것을 다시 확인했습니다.
- **총기 확인과 실제 제원 (`Tools/gen_ballistics.py` → `Data/ballistics.json`):**
  - 템플릿의 `Credit.txt`에 따르면 총은 **AAC Honey Badger**(.300 AAC Blackout, 단총열 PDW)입니다.
  - **조사한 값:** 연사속도 약 800발/분. 단총열 초음속탄 약 2,100fps(640m/s). SIG 125gr 탄은 2,200fps에서 200야드에 1,759fps(G1 BC 0.338). 정밀도는 매치탄으로 2MOA 이하.
  - **게임 모델:** 125gr 초음속 예광탄, 640m/s, 2차 공기저항(v' = g − k|v|v, k를 SIG 속도 감소에 맞춤), 100m 영점.
    - 100야드 영점 기준 200야드 낙차가 −6.4인치로, SIG 발표값(−7.5인치)과 비슷합니다.
    - 100m 영점 낙차: 50m +3.4cm, 100m 0, 200m −31cm, 300m −101cm, 400m −221cm, 500m −405cm.
  - **자세 배율 (확산과 반동에 똑같이 곱함):** 비조준 ×1.10, 견착 ×1.05, 정조준 ×0.90.
  - **확산(반각):** 기본 0.15° × 자세 배율(비조준 0.165°, 견착 0.158°, 정조준 0.135°). 여기에 이동 속도 1cm/s마다 0.0015°가 더해집니다.
  - **반동 (`ballistics.json`의 `recoil`):**
    - **계산 근거:** 무게 4.5lb(2.04kg, 장전 시 약 2.5kg)에 125gr 탄과 장약 가스를 더하면 충격량 6.6N·s, 자유 반동 속도 2.64m/s, 반동 에너지 8.7J(6.4ft-lb)입니다. M4(5.56)의 1.47배입니다.
    - **한 발당 반동:** 게임 기준 M4 0.45°/발에 위 배율을 곱했습니다. 수직은 0.66° ±15%입니다. 수평은 −0.30°~+0.36°로 오른쪽으로 조금 치우칩니다. 둘 다 자세 배율을 곱합니다.
    - **적용:** 매 발 컨트롤러 회전(피치/요)에 더해집니다. 자동 복귀는 없어서 직접 마우스를 내려 제어합니다.
    - **PIE 측정:** 비조준 1초 연사(약 13발)로 시점이 위로 11°, 오른쪽으로 1.8° 올라갔습니다.
- **발사 (`Tools/gen_fp_bullet_t3d.py` → 캐릭터 BP·`BP_FurinaBullet` 그래프, `Scripts/Unreal/ue_fp_bullet_setup.py`):**
  - **입력:** `IA_FurinaFireRifle`(좌클릭)의 Started에서 0.075초 반복 타이머(`FurinaRifleShot`)를 겁니다. 첫 발은 다음 프레임에 나갑니다(InitialStartDelay). Completed/Canceled에서 타이머를 멈춥니다. 설정은 `ue_fp_recoil_setup.py`입니다.
  - **탄도:** 총구(소총 메시 (0, 48.5, 3.1))에서 조준점 방향에 영점 상향각 0.0746°를 더하고, 확산 원뿔을 적용해 `BP_FurinaBullet`을 생성합니다.
    - **조준선 기준 100m 영점 (2026-11-15):** 조준점은 조준선(화면 중앙 레이)이 100m 안에서 맞는 곳입니다. 아무것도 없으면 조준선 위 100m 지점입니다(예전에는 500m). 그래서 탄은 조준선 아래(총구 높이)에서 출발해 50m에서 조준선보다 약 3cm 위를 지나고, 100m에서 조준선과 만난 뒤 그 너머로 떨어집니다.
    - **PIE 단발 측정 (`ue_fp_zero_probe.py`, 반동 전 조준선 기준):** 11m −3.9cm, 50m +4.4cm, 100m +8.1cm, 200m −7cm, 400m −165cm. 정조준 확산(반각 0.135° = 100m에서 ±24cm) 안에서 모델(50m +3.4, 100m 0, 200m −31, 400m −221cm)과 맞습니다.
  - **`BP_FurinaBullet`:**
    - 구성: 반지름 1.5cm 구 충돌(BlockAllDynamic) + ProjectileMovement(640m/s, 중력 1, 속도 방향 회전) + 예광 실린더(`M_FurinaTracer`, 무광 주황 발광).
    - Tick마다 공기저항을 적용합니다.
    - 예광 줄기는 총구 1.5m 앞부터 탄까지 보이며, 최대 25m입니다. 두께는 1cm에 거리의 0.2%를 더합니다.
    - 맞으면 노란 디버그 구(5초)를 그리고, 물리 물체면 밀어낸 뒤 사라집니다. 수명은 4초입니다.
- **PIE 검증 (`ue_fp_bullet_probe.py`, 프레임별 탄 위치):** 쏜 탄의 궤적이 모델과 1% 안에서 맞습니다.
  - 469m: 낙차 −408.7cm(모델 −407.2), 속도 357m/s(모델 359)
  - 935m: −26.9m(모델 −26.8)
- **주의:** 시작 위치에서 +X 방향은 바닥 그라인드 레일(`Spline_Mesh_BP`)을 따라가는 방향이라, 그쪽으로 쏘면 탄이 레일에 바로 맞습니다.
- **도구:** `ue_fp_stance_probe.py`(이동 속도·카메라 오프셋·시야각·반동 프레임 기록), `ue_fp_flag.py`(PIE에서 태그 컴포넌트 켜기·끄기), `ue_pie_look.py`(PIE 시선 설정), `ue_fp_bullet_hitprobe.py`(탄 생성 직후 충돌 대상), `ue_probe_actor.py`

## 걷기 루프 이음매 수정 (2026-11-14)

- **증상:** 걷기 중 오른발을 앞으로 뻗을 때 버벅였습니다.
- **원인:** Unity 걷기 녹화에서 잘라 쓴 80~119 프레임 구간은 걸음 위상상 40프레임 주기와 맞지만, 실제 관절 각도가 주기마다 조금씩 달랐습니다. 이음매의 다리 각도 차이는 3.2°, 속도 차이는 2.3°였습니다. 그래서 오른발이 앞으로 나가는 도중 루프가 다시 시작되며 발목이 약 8cm 뒤로 튀었습니다.
- **수정:** `Tools/analyze_walk.py`로 모든 40프레임 구간의 이음매 오차를 비교했고, 92~131 프레임 구간이 0.0°로 가장 좋았습니다. `convert_motion.py Data walk 92 40 0`으로 다시 변환하고 `repair_walk_loop.py`로 골반 높이를 보정한 뒤, `ue_apply_walk_cycle.py`로 `AS_Furina_Walk`를 다시 썼습니다. 발소리 알림은 새 주기의 가장 앞으로 나간 발목 프레임(왼발 9 = 0.30초, 오른발 29 = 0.97초)으로 옮겼습니다.
- **검증:** PIE에서 걷는 동안 오른발의 앞쪽 이동에 되돌아감이 없었습니다. 백업은 `Backups/WalkSeamFix_20261114/`에 있습니다.

## 무릎과 걷기 발소리 수정 (2026-11-14)

- `CR_FurinaSecondary`의 양쪽 TwoBoneIK 폴은 **각 허벅지 위치 + 앞쪽 50 cm + 바깥쪽 6 cm**인 위치입니다. Furina 메시의 앞은 +Y, 왼쪽은 +X입니다. UE 5.8의 해당 노드는 `Direction`을 선택해도 내부 두 뼈 솔버에 위치처럼 전달하므로, 원점 기준 방향 벡터를 넣으면 무릎이 안으로 접힙니다. `Location`과 다리 기준 위치를 명시합니다.
- IK 가중치의 ×10 증폭을 제거했습니다. 걷기·뛰기 전환 초기에 IK가 갑자기 최대 강도로 켜지지 않습니다.
- `AS_Furina_Walk`의 `FurinaWalkSteps` 트랙에 0.0667 / 0.7333초의 발 접촉 알림을 넣었습니다. 1.333초 주기에 두 번이며, 재생 가중치가 0.5 이상일 때 발목에서 작은 발소리를 냅니다(볼륨 0.28, 피치 1.05).
- `Manny_AnimBlueprint`의 원래 `Footstep` 경로는 `FurinaWalk > 0.5`에서 건너뜁니다. 보이는 걷기 애니메이션의 소리와 숨긴 Manny 소리가 겹치지 않으며, 뛰기 소리와 공중 상태 검사는 기존 경로를 사용합니다.
- 제자리 적용: `Scripts/Unreal/ue_apply_character_fixes.py`. 백업은 `Backups/CharacterFixes_20261114/`에 있습니다. 다른 에디터 프로세스가 같은 에셋을 열고 있으면 파일 잠금 때문에 저장할 수 없습니다.
- 검증: `ue_validate_character_fixes.py`는 1,440프레임의 걷기·뛰기 전환, 이동 중 깜빡임, 다리 길이, 폴 위치의 이동 불변성을 검사합니다. 전후 결과는 `Data/character_fix_validation_before.json`, `Data/character_fix_validation_after.json`에 있습니다. `ue_verify_character_runtime.py`는 임시 PIE 검사 후 편집 모드로 돌아가며 레벨을 저장하지 않습니다.

## 오른발 전진 시 움찔함과 눈의 실제 감김 보완 (2026-11-14)

- 걷기 녹화의 첫 세 프레임에 지면 보정 과도응답이 포함되어, 루프 끝에서 골반 높이가 3.02cm 변했습니다. `Tools/repair_walk_loop.py <Data 경로>`로 안정된 프레임에서 주기적인 수직 골반 움직임을 복원했습니다. 최대 프레임 높이 변화는 0.64cm 이하이며 다른 관절 회전·발소리 알림은 유지합니다. 적용은 `ue_apply_walk_loop.py`입니다.
- 눈 감김 커브만 확인해서는 실제 렌더링 검증이 되지 않습니다. 얼굴 머티리얼 `M_Furina_Opaque`에 skeletal-mesh/morph 사용을 명시하고, `ABP_Furina`의 `BlueprintPostEvaluateAnimation`에서 `IdleBlink` 값을 소유 메시의 `SetMorphTarget`에 전달합니다. 적용은 `ue_apply_visible_blink.py`입니다.
- 검증 스크립트: `ue_validate_walk_blink_asset.py`, 별도 임시 렌더 세션의 `ue_diagnose_face_render.py`. 백업은 `Backups/WalkBlinkFix_20261114/`에 있습니다.

## 옷자락 조절 (`Scripts/Tools/gen_cr_params.py`)

- **lift**: 질주 시 뒤로 들리는 각도(°)
- **bob**: 발걸음 출렁임 세기
- **amp**: 물결 진폭(rad/본)
- **tempo**: 물결 속도

수정 후 `gen_cr_params.py <Data 경로>`를 실행하고, 이어서 에디터에서 `ue_build_cr.py`를 실행합니다.
Control Rig이 들어 올리는 회전은 컴포넌트 +X축 기준 음수 각도여야 자락이 뒤(-Y)로 갑니다. 처음 버전은 이 부호가 반대여서 자락이 몸에 붙었습니다.

## 다시 만들 때 순서

1. **모델:** `Scripts/Blender/blender_export_cm.py` → `FBX/Furina_cm.fbx`
2. **임포트:**
   - `Scripts/Unreal/ue_import.py`: 메시·텍스처·머티리얼
   - 이미 있으면 `ue_reimport.py`
3. **리타겟:**
   - `ue_retarget.py` → `ue_abp.py`(체인 이름 정리, ABP 생성)
   - `ue_ikfix.py`(다리 Limb 솔버) → `ue_ikops.py` → `ue_rtgfix.py`(Root Motion 끄기, Hips 보정)
4. **옛 idle:**
   1. Unity에서 `FurinaIdleRecorder.cs`로 `Data/unity_idle.json` 녹화
   2. `ue_refdump.py`
   3. `Tools/convert_idle.py <Data 경로>`
   4. `ue_make_idle.py`
5. **옷자락·머리카락:**
   - `Tools/gen_cr_params.py <Data 경로>`(세기 조절은 여기서) → `ue_build_cr.py`
   - 기존 에셋을 지우지 않고 그래프만 다시 짭니다.
6. **AnimGraph:**
   1. `Tools/gen_t3d2.py <Data 경로>` → `Data/abp_graph2.t3d` 내용을 ABP_Furina AnimGraph에 붙여넣기
   2. Control Rig 출력을 Output Pose에 연결
7. **캐릭터 BP:** `ue_character.py`
8. **검증 (PIE 중 실행):**
   - `ue_sample.py`(다리 길이·발 높이), `ue_sample2.py`(옷자락·머리 로컬 움직임)
   - 분석은 `Tools/analyze_sample.py`

## 주의

- 언리얼에서 열려 있는 Control Rig·애니메이션 에셋을 스크립트로 **삭제하지 마세요.** 패키지가 깨져 에디터가 크래시합니다. 현재 스크립트들은 제자리에서 다시 씁니다.
- `ue_ikoff.py`는 진단용(리타기터 IK 끄기)입니다. 지금은 IK가 켜진 상태(`ue_ikon.py`)가 정상입니다.

## 2026-11-15 소총 모델 교체 (Colt M4A1) · 탄창 20 / 예비 600

- **모델:** `Downloads/colt-m4a1-carbine/source/Colt_m4A1.fbx`의 `m4a1.001`(총 본체 + 장착된 STANAG 탄창)을 사용합니다. 별도 객체 `ammo`(낱발 탄)와 `mag_20rnd`(바닥에 누운 탄창)는 쓰지 않았습니다. 기존 AR15 FBX·보정값은 `FBX/M4/_old_ar15/`, `Data/fp_rig_ar15_backup.json`에 백업했습니다.
- **변환(`Scripts/Blender/build_colt_rifle.py`):** 총열축을 수평으로 맞춘 뒤(분석 `analyze_colt.py`/`analyze_colt_sights.py`), 뒷가늠자 구멍(리어 사이트 판의 틈, z 1.846~1.868)과 앞가늠쇠 끝을 잇는 조준선 기울기가 옛 총과 같아지도록(−0.23°) 한 번 더 돌렸습니다. 길이는 총구~개머리판 80cm(배율 11.106cm/단위), 뒷가늠자 구멍을 옛 값 (0, −11.757, 9.984)에 정확히 놓았습니다. 그러면 권총손잡이·탄창 위치도 옛 총과 몇 cm 안에서 맞습니다(탄창 y −5.1~0.8, 옛 −6.3~1.5).
  - `stanag_mag` 재질 면만 떼어 `SM_M4Mag`(정적, 원점=총 원점, 장착=항등), 나머지는 `SK_M4A1`(전 정점이 템플릿 무기 뼈대의 `Grip`에 100%)로 내보냈습니다. 탄창 정점은 1,040개, 본체 32,370개입니다.
  - 텍스처는 원본이 최대 58MB(4096)라 2048로 줄였습니다(`colt_textures.py` → `FBX/M4/ColtTex`). 메인 베이스컬러 원본이 1254×1254라 그대로입니다.
- **언리얼(`ue_colt_import.py`):** `/Game/Furina/M4/SK_M4A1`, `SM_M4Mag`를 덮어쓰고 재질 `M_Colt_Main / Furniture / Rear / Mag`(BaseColor·Metallic·Roughness·Normal(DirectX)·AO)를 만들어 슬롯 이름으로 붙였습니다. 옛 `M_M4_AR1~4`는 남아 있지만 쓰지 않습니다.
- **보정값 갱신(`ue_colt_calibrate.py`, 값은 `Data/colt_geometry.json`):** 총구 (0, 40.515, 3.383)(옛 4.849), 뒷가늠자 구멍 (0, −11.757, 9.984), 앞가늠쇠 (0, 23.381, 9.844)(옛 30.61, 조준 반경이 짧아짐), 탄피 배출구 (−2.2, −3.5, 4.5)(대략값, 모델의 실제 배출구를 재지는 않았습니다). `FPN_SightRear/Front`, `M4_FlashPoint`, `M4_CasePoint` 노드에 반영했습니다. 정조준 자세의 가로 오프셋은 뒷가늠자 x가 0.141 → 0이 된 만큼 0.0168로 바꿔 컨트롤 릭을 다시 만들었습니다(`fp_rig.json`).
- **탄창 낙하 콜리전:** `ue_mag_box_collision.py`를 다시 돌려 새 탄창 경계에 맞췄습니다.
- **탄창 20 / 예비 600:** `FurinaAmmo` 기본값 20, `FurinaReserve` 600, 재장전 여유 계산 `TFP_MagRoom`의 A를 20으로 바꿨습니다(재장전 채움은 `min(20 − 잔탄, 예비)`). HUD(`ue_hud_build.py`)는 점을 20칸으로(간격 0.132, 폭 0.09), 재장전 채움은 `ReloadP × 20`, 잔탄 부족(주황) 기준은 30칸 때의 8발에서 5발로, MPC 기본값은 20/600으로 바꿨습니다. HUD 실루엣도 새 총으로 다시 렌더했습니다(`render_m4_hud_silhouette.py`, 가로세로비 3.84).
- **PIE 확인:** 시작 20/600 → 6발 사격 14/600 → 재장전 뒤 20/594(`Data/ammo_2060_probe.json`). 재장전 1.5초 시점에 HUD 점이 절반(10칸) 찼습니다. 3인칭·1인칭·정조준 캡처로 총이 손에 쥐이고 조준 구멍이 화면 중앙에 오는 것까지 눈으로 봤습니다(`ue_colt_view_shots.py`).
- **미확인·한계:** (1) 정조준에서 이 가늠자는 구멍이 원뿔 모양으로 커서 화면 중앙을 많이 가리고, 구멍 안에서 앞가늠쇠가 또렷이 보이는지는 확인하지 못했습니다. (2) 정조준 연사 시 탄 방향 수치는 다시 재지 않았습니다. (3) 탄피 배출 위치와 총구 화염 위치는 육안 확인만 했습니다. (4) 장전 모션의 탄창 위치(`t_mag`)와 왼손 손잡이 위치는 옛 총 값을 그대로 썼고, 3인칭 캡처에서 크게 어긋나 보이진 않았습니다.

## 2026-11-15 총구 화염 개선 (Niagara 스파크 + 추가 발광 레이어)

- **Niagara로 시스템을 처음부터 만드는 건 이 에디터의 파이썬으로는 못 했습니다.** `unreal.Niagara*` 중 에미터 핸들·모듈·렌더러 입력을 만지는 API는 없고(`NiagaraSystem`에서 `emitter_handles` 등 접근 실패, `Data/niagara_probe*.json`), 새 시스템/에미터를 만들려면 Niagara 에디터를 손으로 조작해야 합니다. 그래서 가능한 범위로 구성했습니다.
- **Niagara 레이어(`ue_flash_niagara.py`):** 프로젝트에 이미 있는 `/Game/3DPlatformerGameBundle/NiagaraSystems/Sparks_FXS`를 발사할 때마다 총구 위치(`M4_FlashPoint`)·방향(`M4_FlashRotation`)에 `SpawnSystemAtLocation`(배율 0.07)으로 생성합니다. 캐릭터 BP의 `M4_FlashFinish` → `FNS_SparkSpawn` → `M4_CaseSpawn`으로 이어 붙였습니다. 엔진 템플릿 `DirectionalBurst`는 보이지 않았고 `SimpleExplosion`은 화면 전체가 하얗게 되어 쓰지 않았습니다(`ue_niagara_spawn_test.py`).
- **발광 레이어(`ue_flash_visual.py`):** `BP_M4Flash`에 총열 방향으로 십자 배치한 줄기 평면 2개(`M_MuzzleStreak`)와 사수를 향한 별 모양 원판(`M_MuzzleStar`)을 더했습니다. 둘 다 가산 합성 언릿 재질이고 HLSL로 뾰족한 별·끝이 가늘어지는 줄기·흰빛 노랑 중심에서 주황 가장자리로 가는 색을 만들며, 액터 위치를 시드로 써서 발마다 모양이 조금씩 달라집니다. 이전 세션이 만들어 둔 불투명 꽃잎 4개·코어 구·링(빨간 물방울과 흰 원판으로 보이던 것)과 옛 원뿔은 숨겼습니다(`hidden_in_game`, 컴포넌트는 BP에 남아 있음). 점광원은 그대로입니다.
- **확인:** PIE에서 발사와 같은 틱에 `HighResShot`으로 1인칭 비조준·정조준을 캡처해 별 모양 화염과 노란 스파크 줄기를 봤습니다. 3인칭 캡처는 화염이 거의 안 보였습니다.
- **한계:** 화염은 여전히 한 번에 나타나 45ms 뒤 사라지는 메시이고(시간에 따른 크기·밝기 변화 없음), 연기·열 일그러짐은 없습니다. 스파크의 색·개수·속도는 `Sparks_FXS` 원본 설정이라 Niagara 에디터에서만 바꿀 수 있습니다. 진짜 Niagara 시스템(연기·불꽃·화염 스프라이트)을 직접 만드는 작업은 에디터에서 손으로 하거나, GUI 조작으로 시도해야 합니다.

## 2026-11-16 Niagara Gunfire 에셋 적용 · 화염 투명도

- **Gunfire 에셋:** 새로 들어온 `Content/NiagaraExamples`(Niagara Examples 팩)의 `FX_Weapons/MuzzleFlashes/NS_MuzzleFlash`(플립북 불꽃·연기·스파크·탄피 에미터)를 총구 화염으로 씁니다. "Gunfire"라는 이름의 에셋은 찾지 못해서 이 팩의 총구 화염 시스템을 그것으로 봤습니다(다른 에셋이면 알려 주세요).
  - `ue_flash_gunfire.py`: 캐릭터 BP의 `FNS_SparkSpawn`(SpawnSystemAtLocation)이 이제 `NS_MuzzleFlash`를 생성합니다. 이 시스템은 +X로 발사하고 우리 소총은 +Y라서 회전은 `ComposeRotators(0,90,0 → M4_FlashRotation)`입니다(요 +90°가 맞는 방향, −90°는 카메라 쪽으로 화면을 덮음을 PIE로 확인). 이어서 `SetVariableFloat 'Global Scale' = 0.2`, `SetVariableBool 'Use Bullet Shell' = false`를 건 다음 `M4_CaseSpawn`으로 갑니다(탄피는 기존 `BP_223Case`의 물리 탄피를 그대로 씀).
  - 배율: 0.5에서는 불덩이가 정조준 시야를 반쯤 가렸고, 0.2에서 1인칭 비조준·정조준 모두 총구 옆 불꽃으로 보였습니다.
  - 이전에 쓰던 `Sparks_FXS` 호출은 이 노드가 대체했습니다.
- **화염 투명도 +40%:** "투명도를 40% 늘린다"를 더 투명하게(밝기 ×0.6)로 해석해, 직접 만든 가산 레이어(`M_MuzzleStreak`, `M_MuzzleStar`)의 세기를 0.6배로 낮췄습니다(`ue_flash_visual.py`). Niagara 쪽 불꽃은 이 값의 영향을 받지 않습니다(그 불꽃의 색·세기는 `User.Flash Base Color` 등 시스템 매개변수로 조절).
- **확인:** PIE에서 발사 프레임 캡처(`ue_flash_shots.py`)로 1인칭 비조준·정조준 화염을 봤고 3인칭은 화염이 거의 안 보였습니다. 연기·스파크 에미터가 따로 보이는지, 연사 시 부하는 확인하지 않았습니다.
- **알려진 잡음:** 이전 세션에서 중간에 실패한 테스트 스크립트의 틱 콜백(`ue_niagara_spawn_test.py`)이 PIE마다 로그에 오류를 반복해 찍습니다. 에디터를 재시작하면 사라지고 게임 동작에는 영향이 없습니다.

## 2026-11-16 총 쏠 때 파란 불 제거

- **원인:** `BP_M4Flash`의 점광원 `FlashLight` 색이 파란색(r 55, g 150, b 255)이었습니다. 첫 총구 화염 스크립트가 `unreal.Color(255, 130, 35, 255)`로 주황을 넣으려 했는데 `Color`의 생성자 인자 순서가 (b, g, r, a)라 파랑이 됩니다. 발사마다 소총과 주변이 파랗게 비쳤습니다.
- **수정(`ue_flash_light.py`):** r/g/b 필드로 직접 주황(255, 140, 45)을 넣고 저장했습니다(세기 1800 그대로). 확인(`ue_blue_probe.py`, `ue_fire_frames.py`) 때 파란 조명을 읽은 시점과 수정 스크립트가 "이전 값"으로 읽은 시점 사이에 값이 이미 주황으로 바뀌어 있었습니다(제가 바꾼 기록은 없음). 어느 쪽이든 지금 저장된 값은 주황이고, PIE에서 3인칭·1인칭·정조준 발사 9프레임에 파란 조명은 보이지 않았습니다.
- **참고:** 같은 `Color(...)` 호출 방식이 다른 스크립트에도 있으면 같은 문제가 생길 수 있습니다.

## 2026-11-16 눈에 보이는 총알 · M4A1 탄도(탄속·낙차·공기저항)

- **총알 모양:** `BP_FurinaBullet`의 `ProjectileVisual`(탄약 에셋에서 잘라 둔 `SM_223Projectile`, 실제 길이 약 1.3cm)을 20배(약 25cm)로 키우고 뜨겁게 빛나는 언릿 재질 `M_BulletGlow`(노랑-흰 빛)로 바꿨습니다. 탄 앞머리가 노란 총알 모양으로 보이고 뒤에 기존 주황 예광 줄기가 따라옵니다. 충돌 구는 그대로 반지름 0.285cm라 판정은 변하지 않습니다(`ue_bullet_visual.py`, 배율 인자).
  - 실제 속도(910m/s)에서는 한 프레임에 15m쯤 가서 눈으로 모양을 알아보기 어렵습니다. 확인은 게임 시간을 4%로 늦춘 상태(`slomo 0.04`)의 고해상도 캡처로 했고(`ue_bullet_slowmo.py`), 앞머리 노란 총알과 예광이 같이 날아가는 것을 봤습니다. 총알 형태(뾰족한 쪽이 앞인지)는 캡처에서 작아서 확실히 구분하지 못했습니다.
- **M4A1 탄속:** 910m/s 그대로입니다(M855A1, 14.5인치 M4A1 기준 약 905~910m/s, [위키 M4 carbine](https://en.wikipedia.com/wiki/M4A1)과 총기 포럼 크로노그래프 측정 2,950~2,970fps에 맞춤. M855는 약 880~884m/s).
- **공기저항:** 2차 항력(v' = g − k|v|v)의 k를 0.001426 → 0.001380 /m(`K2Node_FPB_Kv.B` = 1.38007535e-05 /cm)로 바꿔, 같은 탄속의 진공 낙차 대비 **500m에서 추가 낙차가 정확히 1.00m**가 되게 했습니다(이전 값은 1.05m).
  - 모델: 진공 낙차 1.48m → 공기저항 포함 2.48m, 500m 속도 456m/s, 비행시간 0.79초. 100m 0.065m, 200m 0.29m, 300m 0.72m, 400m 1.42m 낙차.
  - **PIE 측정(`Data/bullet_slowmo.json`, 12°·4° 위로 발사, 발사 방향선 기준 수직 낙차):** 500m에서 속도 454.9~455.6m/s, 비행시간 0.792초, 낙차 2.43~2.47m. 실효 k = 0.001384~0.001387 /m라 설정값과 같습니다. 확산이 방향을 무작위로 바꾸지만 속도와 방향선 대비 낙차는 영향이 없습니다.
- **총구 위치 버그 수정:** 총알이 나가는 점(캐릭터 BP `K2Node_FPF_Muzzle`)이 AR15 총구(0, 40.625, 4.849)로 남아 있었습니다. Colt 총구 (0, 40.515, 3.383)로 고쳤습니다. 탄이 나가는 높이가 1.5cm 내려갑니다.
- **50m 낙차 보정각:** `FPN_AimElev.B` 0.000307423 → 0.000307816 rad(새 k, 910m/s, 49.6m 기준). 저장된 `Data/ballistics.json`은 예전 Honey Badger(640m/s) 값이 남아 있어 갱신하지 않았습니다(코드는 이 파일을 더 읽지 않고 BP 노드 값을 씁니다). 예광 줄기 계산용 `K2Node_FPB_Flown.B`의 옛 640m/s(64008)는 90000으로 바꿨습니다.
- **한계:** 정조준 영점은 50m 그대로이고, 500m 보정은 하지 않았습니다. 바람·회전 편류 등은 없습니다. 총알 크기를 더 크게/작게 하려면 `py ue_bullet_visual.py <배율>`로 다시 돌리면 됩니다(PIE 중지).

## 2026-11-16 황동색 총알 · 도탄

- **황동색:** 총알 머리 `M_BulletGlow`는 방출색 (0.55, 0.45, 0.12), 예광 줄기 `M_FurinaTracer`는 (0.30, 0.25, 0.07)로 바꿨습니다(이전 주황·노랑-흰빛). 이 장면은 노출이 밝아 1 이상 값은 순수한 노랑으로 보여서 값을 낮췄고, 슬로모션 캡처에서 탁한 황금색(황동색 계열)으로 보였습니다. 실제 황동 질감(금속 반사)은 아니고 발광 단색입니다(`ue_bullet_rico.py`).
- **도탄 조건:** 입사각은 비행 방향과 **표면**이 이루는 각으로 봤습니다(수직 충돌이 90°). 즉 표면에 스치듯 맞는 20° 미만에서만 판정합니다. `asin(|v̂·HitNormal|) < 20°` ⇔ `|v̂·HitNormal| < 0.34202`일 때 난수 0~1이 0.4 미만이면 도탄합니다. 탄당 도탄은 최대 1번(`FurinaRico` 변수)이고 두 번째 충돌은 기존대로 소멸합니다.
- **도탄 동작(`BP_FurinaBullet`, 노드 `FRC_*`):** 도탄이면 탄을 없애지 않고 `FurinaRico = 1`로 바꾼 뒤 충돌 위치에 Niagara 스파크(`Sparks_FXS`, 배율 0.1)를 띄우고, `ProjectileMovement`의 내장 반사(`bShouldBounce`, 탄성 0.5, 마찰 0.3)로 튕깁니다. PIE 측정(8° 입사, 도탄 전 속도 약 902m/s): 수직 속도가 −102m/s에서 +51m/s, 수평 속도는 약 70%로 줄어(약 627m/s) 위로 4.7° 정도 날아갑니다. 나머지 충돌은 기존 경로(노란 디버그 구, 물리 물체 밀기, 소멸)입니다.
- **측정(로그 `RICO hit` 집계):** 입사각 20° 미만 충돌 22번 중 8번 도탄(36%, 기대 40%), 20° 이상 충돌 11번 중 0번. 표본이 작아 정확히 40%인지는 말할 수 없습니다.
- **알려진 한계:**
  - 도탄한 탄이 바로 앞의 낮은 구조물(레일·상자 등)이나 벽에 다시 맞으면 거기서 사라집니다(로그에서 확인). 도탄 후 벽 충돌은 두 번째 충돌이라 도탄 없이 소멸합니다.
  - 도탄 시 소리와 흔적(탄흔)은 없습니다.
  - 원래 정지·소멸 판정에 쓰던 디버그 노란 구는 도탄이 아닌 충돌에서 그대로 나옵니다.
  - 디버그용 `PrintString` 노드(`FRC_PrintHit`, `FRC_PrintTrue`, `FRC_Cat*`, `FRC_Str*`)는 그래프에 남겨 두었고 `bPrintToLog`를 꺼 둔 상태입니다. 다시 켜려면 `py ue_rico_print.py 1`(PIE 중지).
  - 몇몇 테스트(`ue_rico_test.py`)는 PIE에서 탄이 한 프레임 안에 사라져 변수 읽기로는 도탄을 세지 못했고, 위 로그 집계로 대신 확인했습니다.

## 2026-11-16 공기저항 기준치 정정: 500m에서 지름 1m 원 안에 무작위

- **정정:** "500m당 1m"를 추가 낙차로 잘못 해석해 바로 위 절에서 항력 계수를 바꿨는데, 의도는 **500m 기준 지름 1m 원 안에 탄이 무작위로 흩어지는 것**(탄 퍼짐)이었습니다. 항력 계수는 원래 값으로 되돌렸습니다(`K2Node_FPB_Kv.B` = 1.4261805540956367e-05 /cm, k = ln(988/920)/50 /m, 50m 보정각 `FPN_AimElev.B` = 0.000307423138019658). 이 값에서 500m 추가 낙차는 1.05m가 되지만 목표로 맞춘 값이 아니고, 바로 위 절의 "추가 낙차 1.00m" 설명은 폐기합니다. 탄속 910m/s, 총구 위치·총알 모양 변경은 그대로입니다.
- **탄 퍼짐(`ue_spread_500.py`):** 서서 정지한 채 정조준(ADS)으로 쏠 때 퍼짐 원뿔 반각이 `atan(0.5m / 500m) = 0.0573°`가 되게 했습니다. 원뿔 안 방향은 균일 분포(`RandomUnitVectorInConeInDegrees`)라 500m 표적에서는 반지름 0.5m 원 안에 균일하게 흩어집니다. 기본값 `K2Node_FPF_SprBase.B`를 0.15° → 0.063662°(정조준 배율 0.9를 곱하면 0.0573°)로 바꿨습니다(예전 정조준 퍼짐은 0.135°, 500m에서 지름 약 2.4m).
  - **그대로인 것:** 비조준 1.1배·견착 1.05배, 이동 가산(1cm/s당 0.0015°), 앉기·엎드리기 배율, 견착 1%·비조준 3% 조준 오차 원뿔.
  - 따라서 걸으면(120cm/s) 이동 가산 0.18°가 더해져 500m에서 지름 약 6m로 넓어집니다. 지름 1m는 "서서 정지한 정조준" 기준입니다. 비조준·견착·이동·앉기에서도 1m로 고정하려면 알려 주세요.
- **측정(`ue_spread_probe.py 20 ads`):** 정조준 20발, 발사 직전 실제 소총 변환으로 이상 방향(총구 → 조준선 50m 점)을 계산해 탄 생성 프레임의 속도 방향과 비교했습니다. 평균 오프셋 (−0.007°, +0.024°)(50m 보정각 0.0176°와 맞음). 평균 중심에서의 흩어짐: 평균 반지름 0.030°, 최대 0.052°(한계 0.0573°) → 500m에서 평균 0.26m, 최대 0.45m. 표본 20발이라 균일 원판의 이론 평균 반지름 0.038°(0.33m)보다 조금 작게 나왔고, 최대가 0.5m를 넘지는 않았습니다.
  - 예전에 쓰던 `ue_shoulder_err_probe.py ads`는 카메라 전방과 비교해서, 정조준 중 소총 반동 킥이 섞여(평균 오프셋 +1.4°, 흩어짐 0.6°) 퍼짐 측정에는 맞지 않았습니다.

## 2026-11-16 도탄 스파크 0.1초

- **원인:** 도탄 때 `SpawnSystemAtLocation`으로 띄운 `Sparks_FXS`는 시스템 자체 수명만큼 남았습니다(PIE 프로브에서 7초 넘게 남은 것 확인).
- **수정:** 작은 액터 `/Game/Furina/M4/BP_RicoSpark`(Niagara 컴포넌트 `Sparks_FXS`, 배율 0.1, `BeginPlay → SetLifeSpan(0.1)`)를 충돌 위치에 생성하는 것으로 바꿨습니다(`ue_rico_spark.py`, `ue_rico_spark_life.py`). 액터가 0.1초 뒤 사라지면서 파티클도 즉시 사라지고, 도탄한 탄이 바로 다음 충돌로 없어져도 스파크는 0.1초 뒤 정리됩니다. 총알 BP의 옛 `FRC_Spark` 노드는 연결을 끊은 채 그래프에 남아 있습니다(노드 삭제가 에디터를 죽이는 문제).
- **교훈:** 파이썬으로 클래스 기본값 `initial_life_span`을 바꿔 저장했는데 스폰된 인스턴스는 0이었습니다(저장 안 됨). 그래서 BP 안에서 `SetLifeSpan`을 호출하게 했습니다. 같은 방식으로 만든 `BP_M4Flash`의 수명(0.045초)도 같은 문제일 수 있어 확인하지 않았습니다.
- **확인(`ue_rico_spark_probe.py`):** 지면을 8°로 18발 쏴서 생긴 도탄 스파크 9개가 모두 정확히 0.1초 보였습니다.

## 2026-11-16 1인칭 왼손: 네 손가락이 핸드가드를 감싸게

- **증상:** 엄지는 괜찮은데 아래 네 손가락이 총 모양과 맞지 않았습니다.
- **측정(`ue_finger_probe.py`, 소총 좌표):** 손가락 뼈 위치를 정조준·견착·허리 자세에서 쟀습니다(손 모양은 자세와 관계없이 같고 소총 앞뒤 위치만 다름). 손가락 밑마디(관절 1)는 둥근 핸드가드(`colt_handguard_section.py`: 중심 x 0 / z 3.55, 반지름 2.84cm, y 5~19cm) 둘레에 있는데, 손가락이 총열 방향으로 쭉 뻗어 관절 2·3이 핸드가드 중심축에서 1.2~2.4cm 거리, 즉 **핸드가드 안을 뚫고** 있었습니다.
- **수정:** 각 손가락이 핸드가드 둘레(반지름 2.84 + 손가락 반지름 0.6 = 3.44cm 원)를 따라 왼쪽 → 아래 → 오른쪽으로 감싸도록 관절별 회전을 계산했습니다(`Scripts/Tools/fit_finger_curl.py --write` → `fp_rig.json`의 `fingers_l`: 뼈 로컬 축 + 각도, 관절 1 24~62°, 2 12~35°, 3 22~36°). `ue_build_cr.py`가 `CR_FurinaSecondary`에 손가락 12개마다 `GetTransform(Local) → QuaternionMul → SetRotation(Local, 가중치)`를 넣습니다. 가중치 = 1인칭 × 재장전 아님 × 집라인 아님이라 3인칭·재장전·집라인에는 영향이 없습니다. 엄지는 손대지 않았습니다. 강도는 `fingers_l_scale`로 조절합니다. 이전 값은 `Data/fp_rig_before_fingers.json`입니다.
- **같은 일을 `RigUnit_AddBoneTransform`으로 먼저 했으나** 손가락이 전혀 움직이지 않아(원인 불명) 위의 명시적 로컬 회전으로 바꿨습니다.
- **측정 결과(정조준, 예측과 일치):** 네 손가락의 관절 2·3·끝이 핸드가드 중심축에서 3.44~3.63cm로, 이전 1.2~2.5cm에서 표면 바깥으로 나왔습니다. 고해상도 캡처에서도 손가락이 핸드가드를 뚫지 않고 아래쪽 옆면에 붙습니다.
- **한계:** 손가락 반대편 끝은 핸드가드에 가려져 캡처로 확인하지 못했습니다. 손가락 밑마디를 크게 틀어(최대 62°) 손바닥 쪽 살이 약간 늘어나 보일 수 있습니다. 화면 확인은 허리 자세만 했고 정조준·견착에서는 측정값만 확인했습니다. 손 모양은 푸리나 손 크기 기준이라 핸드가드가 굵게(지름 5.7cm) 모델링된 만큼 손가락이 완전히 감싸지는 못하고 아래~오른쪽 아래까지만 닿습니다.
- **도구:** `ue_finger_probe.py`, `ue_fp_hand_shot.py`, `ue_cr_dump.py`, `ue_rigunit_find.py`, `Scripts/Blender/colt_handguard_section.py`.

## 2026-11-16 Underground Tunnel 맵에 푸리나 배치 + 고품질 Colt + GitHub 분할 푸시
- **시작 맵:** `Config/DefaultEngine.ini`의 `GameDefaultMap`/`EditorStartupMap`을 `/Game/UndergroundTunnel/Maps/Demonstration`으로 바꿨습니다(백업 `DefaultEngine.ini.bak_before_tunnel`). 이 프로젝트에는 GameMode가 없어 ExampleLevel처럼 캐릭터 액터의 Auto Possess Player 0으로 조작합니다.
- **푸리나 배치(`ue_place_furina.py`):** 에디터 월드에서는 라인 트레이스가 아무것도 맞히지 못해 `py ue_place_furina.py replace x y z [yaw]`(직접 좌표)를 추가했습니다. 현재 `Furina_Player`는 (-3100, -110, -150)에 있고 선로 위 바닥(z≈-241)으로 내려앉습니다. 레벨을 저장했습니다.
- **터널에서 사격이 막히던 문제(`ue_clear_rail_beginplay.py`):** `Grind_Rail_Component_BP`의 `UsingRail?`가 첫 프레임부터 true였습니다(레일이 없는 곳에서는 컴포넌트 틱이 꺼져 있어 리셋되지 않음). 그래서 `FurinaSpecial`이 켜져 1인칭 전환과 사격이 막혔습니다. `ThirdPersonCharacter_BP`의 BeginPlay(근접 클립 명령 뒤)에 `UsingRail? = false`를 넣었습니다. 컴포넌트가 먼저 BeginPlay를 하므로 이 값이 남고, 실제 레일 탑승은 이후 true로 바뀌어 그대로 동작합니다. 프로브: `ue_rail_start_probe.py`(PIE 시작부터 샘플링), `ue_pie_state_probe.py`, `ue_zip_series_probe.py`.
- **터널 PIE 확인:** 스폰, W 이동, HUD 20/600, 발사 6발 후 14발, 재장전 후 20/594(`ue_ammo_2060_probe.py`)를 확인했습니다. 마우스 클릭 사격은 자동화 입력으로 안 들어가 이전처럼 `FurinaRifleShot` 호출로 확인했습니다. 도탄, 화염, 손가락 감싸기는 이 레벨에서 다시 확인하지 않았습니다.
- **고품질 Colt(`ue_colt_import_hq.py`) 임포트 완료:** `SK_M4A1`/`SM_M4Mag`를 새 FBX로 덮어쓰고 4096 원본 텍스처 20장(`T_Colt_*`)으로 머티리얼 4개를 다시 만들었습니다(`ue_colt_mat_probe.py`: 5채널 연결, 슬롯 이름 일치). 결과는 `Data/colt_import_hq.json`. 터널에서 1인칭 캡처는 총이 거의 검게 보입니다(금속성 + 터널에 반사원이 없는 어두운 조명). 새 탄창으로 재장전·손 위치는 아직 눈으로 확인하지 않았습니다.
- **GitHub:** 5.3 GB 터널 콘텐츠를 1.2 GB 이하 커밋 단위로 나눠 push했습니다(`push_in_chunks.py`, `push_map_chunks.py`; schannel, 인증서 검증 켬). origin/main = f0335126. 이후 작업(고품질 Colt, 레벨 배치, BP 수정, README)은 아직 커밋/푸시하지 않았습니다. 노트북은 `git pull` 뒤에 위 변경을 받으면 됩니다.

## 2026-11-17 Lyra 사격장 맵으로 시작 맵 교체 + 총알 Lyra 호환 히트판정(피해량 0)

- **동굴 맵 삭제:** `Content/UndergroundTunnel`(5.2 GB) 전체를 프로젝트에서 지웠습니다(git 기록에는 남아 있어 `git restore`로 복구 가능). 기본 맵은 먼저 `ExampleLevel`로 되돌렸다가 아래 Lyra 맵으로 바꿨습니다.
- **Lyra 사격장 가져오기(`Scripts/Tools/lyra_dep_closure.py`, `Scripts/Unreal/lyra_export_range.py`, `ue_lyra_range_build.py`):**
  - Lyra의 `L_FiringRange_WP`는 월드 파티션 맵이고 월드 설정이 C++ 클래스 `LyraWorldSettings`라 이 BP 전용 프로젝트에서는 월드 파티션이 비활성(액터 0개)으로 열립니다(`Saved/Logs`에서 `LyraWorldSettings ... 로드에 실패`). 그래서 맵을 그대로 쓰지 않고 Lyra 에디터(`LyraStarterGame`, UE 5.8, `-ExecutePythonScript -nullrhi`)로 액터 321개의 클래스/트랜스폼/메시/머티리얼/폴더를 `Data/lyra_range_actors.json`으로 내보낸 뒤 이 프로젝트에서 일반 레벨 `/Game/LyraRange/L_FiringRange`로 다시 만들었습니다.
  - 가져온 것: StaticMeshActor 258개(SM_ModuleA_090 214개, 기본 큐브 41개, 계단 2개, 난간 1개), TextRenderActor 15개, 조명(해/스카이/안개/스카이 아트모스피어). 메시와 머티리얼 누락 0(`Data/lyra_range_build.json`).
  - 가져오지 않은 것: Lyra 전용 액터(LyraPlayerStart 8, 텔레포트 7, 런처 4, 무기 스포너 3, 에임 어시스트 타깃 2, 패드류), BlockingVolume 9, Landscape, VolumetricCloud, NavMesh. 땅이 없어서 가장 낮은 바닥 아래(z −160)에 큰 받침 `FallCatchFloor`를 두었습니다.
  - 에셋은 콘텐츠 전용 플러그인으로 복사했습니다: `Plugins/ShooterMaps`(메시, 원본 맵 파일, 외부 액터 — 경로 `/ShooterMaps/...` 유지), `Plugins/LyraExampleContent`(Lyra 격자 머티리얼 MI_MS_* 와 의존 텍스처 19개, 22 MB), `Content/PhysicsMaterials/PM_Concrete`. 합계 약 26 MB. 플러그인은 에디터를 재시작해야 마운트됩니다.
  - 푸리나는 Lyra의 PlayerStart1 위치(170, −1045, 높이 ~880, 요 −90)에 `Furina_Player`로 배치했습니다(`ue_place_furina.py replace 170 -1045 880 -90`). `DefaultEngine.ini`의 `GameDefaultMap`/`EditorStartupMap`을 `/Game/LyraRange/L_FiringRange`로 바꿨습니다.
  - PIE: 푸리나가 위층 바닥에 서고 HUD 20/600, 레일 상태 false, 발사 시 탄약이 줄고 재장전 후 20/597(`ue_pie_state_probe.py`, `ue_ammo_2060_probe.py`). "라이팅을 다시 빌드해야 합니다" 메시지가 뜨며 빌드는 하지 않았습니다.
- **총알 Lyra 호환 히트판정(`ue_bullet_hit_gas.py`, BP_FurinaBullet 노드 `FHG_*`):**
  - Lyra의 피해는 대상의 AbilitySystemComponent에 게임플레이 이펙트(`SetByCaller.Damage` 크기)를 적용하는 방식입니다. 이를 따라 이 프로젝트에서 엔진 플러그인 `GameplayAbilities`를 켰습니다(`abc.uproject`, 에디터 재시작 필요). 태그 `SetByCaller.Damage`(Lyra와 같은 이름)와 `Furina.Hit.Bullet`은 `Config/DefaultGameplayTags.ini`에 등록했습니다.
  - `BP_FurinaBullet` 변수: **`FurinaDamage`(float, 기본 0.0 = 피해량)**, **`FurinaDamageEffect`(GameplayEffect 클래스, 기본 비움)**. 둘 다 인스턴스 편집 가능입니다.
  - 동작: 도탄이 아닌 일반 적중 경로(`FRC_Branch`의 else → `Mark` 사이)에서 `Other`의 ASC를 찾아(`GetAbilitySystemComponent`) ASC와 이펙트 클래스가 모두 유효하면 `MakeOutgoingSpec(FurinaDamageEffect, 1, 컨텍스트)` → `AssignTagSetByCallerMagnitude(SetByCaller.Damage, FurinaDamage)` → 스펙의 컨텍스트에 `HitResult` 추가 → `BP_ApplyGameplayEffectSpecToSelf`. Lyra의 `LyraHealthComponent` 자해 피해 코드와 같은 패턴입니다. 유효하지 않으면 건너뛰고 기존 동작(디버그 구, 물리 밀기, 소멸)으로 갑니다. 도탄된 첫 충돌은 피해를 주지 않습니다.
  - **지금 이 프로젝트에서는 `FurinaDamageEffect`가 비어 있어 아무 일도 하지 않습니다.** Lyra에서는 `/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller`(Lyra의 `DamageGameplayEffect_SetByCaller` 기본값)를 이 변수에 지정하고 `FurinaDamage`에 피해량을 넣으면 됩니다.
  - 검증(`ue_bullet_hit_test.py`): ASC를 붙인 큐브 표적(임시 BP)을 푸리나 앞 6 m에 두고 임시 무한 지속 GE를 이 변수에 지정한 채 `FurinaRifleShot` 3발을 쐈더니 표적 ASC에 이펙트가 3개 적용됐습니다(`Data/bullet_hit_test.json`). 검증 뒤 임시 GE/표적/변수 기본값은 `ue_bullet_hit_test_cleanup.py`로 모두 제거했습니다. 본 프로젝트에는 Lyra의 `LyraHealthSet`이 없어서 실제 체력 감소는 확인하지 못했습니다.
  - 한계: 총알은 `BlockAllDynamic` 구체라 Lyra 캐릭터의 캡슐/메시 충돌 채널(`Lyra_TraceChannel_Weapon`, 팀/부위별 배율)은 쓰지 않습니다. 부위(헤드샷) 배율과 팀 판정은 아직 없습니다. 피해량과 이 값들을 받으면 추가합니다.
- **GitHub:** 아직 커밋/푸시하지 않았습니다(동굴 맵 삭제 687개 포함).

## 2026-11-17 푸리나를 Lyra Starter Game 프로젝트로 이전 (이 저장소의 기준 프로젝트)

- **기준 프로젝트가 바뀌었습니다.** 이제 작업과 git은 `Downloads/test/test/abc`(= Lyra Starter Game UE 5.8, C++ `LyraGame` 포함, 프로젝트 파일 `LyraStarterGame.uproject`)에서 합니다. 이전 BP 전용 프로젝트는 `Downloads/abc_before_lyra`에 백업으로 남겼고 더 이상 갱신하지 않습니다(옛 기록은 위 섹션들, git 히스토리에도 있음). 이 README의 위쪽 내용 중 `/Game/...` 경로와 `Scripts/Unreal/*.py`는 그대로 Lyra 프로젝트에서 쓸 수 있습니다(스크립트 안의 출력 경로만 abc를 가리키는 것이 많아 새로 만든 `lyra_*.py`는 Lyra 쪽 `FurinaSource/Data`를 씁니다).
- **복사한 콘텐츠(`Scripts/Tools/abc_dep_closure.py`로 의존 폐포 계산, 661개 1.2 GB):** `Content/Furina`, `3DPlatformerGameBundle`(푸리나 폰 `Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP` 와 컴포넌트·애니메이션), `TFPMovement`, `Free_Crawl_Animation`, `NiagaraExamples` 일부. Lyra의 폴더 이름과 겹치는 것이 없어 같은 `/Game/...` 경로로 복사했습니다. Saori는 제외.
- **플레이어를 푸리나로 (`lyra_furina_setup.py`, `lyra_furina_experience.py`, `lyra_fix_pawn.py`, `lyra_pawn_autopossess.py`; Lyra 에디터 `-ExecutePythonScript -nullrhi` 로 실행):**
  - `/Game/Furina/Lyra/HeroData_Furina`: Lyra의 `HeroData_ShooterGame`을 복제하고 `PawnClass`만 푸리나 폰(`.../Blueprints/ThirdPersonCharacter_BP`)으로 바꿨습니다. (처음에 `JumpPadCharacterBP/` 변종을 잘못 지정했다가 고쳤습니다. 푸리나 폰은 폴더 바로 아래의 것입니다.)
  - `/Game/System/Experiences/B_Furina_Experience`: `B_ShooterGame_Elimination`을 복제하고 `DefaultPawnData`를 위 PawnData로 바꿨습니다(Lyra가 스캔하는 `/Game/System/Experiences` 에 있어야 `FPrimaryAssetId`로 찾습니다). 사격장 맵 월드 설정의 `DefaultGameplayExperience`는 Python에서 "인스턴스에서 편집 불가"라 건드리지 않고, `Config/DefaultEditorPerProjectUserSettings.ini` 의 `[/Script/LyraGame.LyraDeveloperSettings] ExperienceOverride=LyraExperienceDefinition:B_Furina_Experience` 로 **에디터 PIE에서만** 푸리나 Experience를 쓰게 했습니다. 패키지 빌드용으로는 맵의 월드 설정에서 직접 지정해야 합니다.
  - 푸리나 폰 BP의 기본값 `AutoPossessPlayer`를 Player0 → Disabled로 바꿨습니다. 이전 BP 전용 프로젝트는 레벨에 놓인 폰(인스턴스 값 Player0)이 쓰이지만 Lyra에서는 게임 모드가 폰을 스폰하는데, Player0 상태에서는 폰이 컨트롤러 없이 남아 카메라가 벽 속에서 시작했습니다(`lyra_pie_pawns.py`로 폰/컨트롤러 확인). 바꾼 뒤 플레이어가 자동으로 푸리나 폰을 조종합니다.
  - 봇: Elimination의 봇도 같은 PawnData라 푸리나 폰으로 스폰되고, Lyra 봇 AI가 ASC 없는 폰에 `InputTag.Weapon.Reload` 이벤트를 보내 로그에 오류가 쌓입니다. PIE 봇 수를 0으로 두었습니다(`bOverrideBotCount=True`, `OverrideNumPlayerBotsToSpawn=0`; 에디터를 다시 열어야 적용).
  - 총알 BP의 `FurinaDamageEffect`는 Lyra의 `/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller`로 지정했고 `FurinaDamage`는 0입니다.
- **PIE 확인(Lyra 에디터, `L_FiringRange_WP`):** 푸리나가 위층에서 시작해 이동, HUD 20/600, 1·3인칭, 사격과 재장전이 동작합니다(`lyra_pie_probe.py`계열, `lyra_reload_probe.py`). Lyra의 팀 점수판, 텔레포터, 점프대, 무기 스포너, 조준 보조 표적 같은 Lyra 요소가 그대로 있습니다. 첫 실행은 셰이더 컴파일로 느려서 게임 시간이 실시간보다 느리게 흐릅니다(스크립트는 게임 시간으로 잽니다).
  - **미확인:** 푸리나 폰에는 Lyra의 ASC/체력(`LyraPawnExtensionComponent`)이 없어서, 푸리나 총알이 Lyra 영웅 캐릭터(`LyraHealthSet`)의 체력을 실제로 깎는지는 확인하지 못했습니다(현재 맵에는 `LyraHealthComponent`가 달린 액터가 없습니다). BP 전용 프로젝트에서 ASC를 붙인 임시 표적으로 이펙트 적용 3/3은 확인했습니다. 푸리나 본인의 체력/팀/피격도 아직 없습니다.

## 2026-11-17 재장전: M4 애니메이션 팩의 Reload 반영 (3초 유지, 탄창 교체 사이에 허리춤 구간 추가)

- **원본:** `Downloads/m4-fps-weapon-animations-pack-v1/source/M4.fbx`(총 모델은 쓰지 않음). 55개 본(양팔 손가락 포함) + 총/탄창1·2/볼트 본, 액션 Reload(프레임 1~110), Reload_Empty(111~225), Fire, Draw, Holster, Idle(30 fps). `Scripts/Blender/inspect_m4_pack.py` → `Data/m4_pack_inspect.json`.
- **학습(`Scripts/Blender/m4_reload_extract.py` → `Data/m4_reload_extract.json`):** Reload의 왼손/오른손/탄창1·2 본을 총(Main_j) 기준 좌표(푸리나 규칙: X=왼쪽, Y=앞, Z=위, 총 길이 80 cm 기준 배율)로 프레임별 추출했습니다. 오른손은 내내 고정(그립), 총은 거의 기울지 않고, 왼손만 움직입니다.
  - 팩의 Reload는 한 탄창을 뽑았다가 곧바로 같은 자리에 다시 끼우는 약 2.5초 동작입니다: f7~13 왼손이 탄창으로 이동, f13~26 잡고 대기, f27~34 아래로 뽑음(탄창이 약 8 cm 내려옴), f34~43 손이 뒤로, f43~64 탄창을 다시 위로 끼움, f64~82 핸드가드로 복귀.
- **푸리나용 재구성(`Scripts/Tools/build_reload_curves.py` → `Data/reload_curves_new.json`):** 총 3.0초. 새 탄창을 허리춤에서 꺼내는 구간(0.70초)을 뽑기와 끼우기 사이에 넣었습니다. 푸리나 팔이 짧아 이동량은 기존과 같이 0.9배입니다.

  | 구간 | 시간(초) | 내용 | 원본 프레임 |
  |---|---|---|---|
  | 대기 | 0.00–0.05 | | |
  | 잡기까지 | 0.05–0.68 | 왼손이 탄창으로 | f7→26 |
  | 뽑기 | 0.68–1.01 | 탄창을 잡고(0.71 `MagState`=1) 아래로 뽑아 놓음(1.01 → 2, 낙하) | f26→36 |
  | 허리춤 | 1.01–1.71 | 허리춤으로 0.25 이동 → 0.20 새 탄창 꺼냄(1.36 → 1, 손에 쥠) → 0.25 올림 | 새 구간 |
  | 끼우기 | 1.71–2.40 | 새 탄창을 총으로 가져가 끼움(2.34 → 0, 장착) | f43→64 |
  | 복귀 | 2.40–3.00 | 왼손이 핸드가드로 | f64→82 |

  허리춤 점은 기존 템플릿 재장전의 새 탄창 자세(총 기준 델타 (16.4, −36.9, −32.8) cm)입니다. 팩 구간 속도는 0.99배입니다(합계 2.25초에 맞춤).
- **적용(`lyra_reload_apply.py`):** `AS_Furina_FP_Reload`/`AM_Furina_FP_Reload`(1·3인칭 공용)의 `ReloadLX/LY/LZ`와 `MagState`를 교체했습니다. AS의 기존 곡선 이름은 소문자(`reloadlx` 등)라 처음에는 옛 키가 남아 95개가 아니라 156개가 되었고(대소문자 구분 때문), 대소문자 무시로 지우고 다시 넣어 두 애셋 모두 키 95/95·MagState 10/10, 오차 0임을 확인했습니다(`lyra_reload_verify.py`). `FurinaMag` 처리(`FurinaMagUpdate`)와 재장전 3초 타이머는 그대로입니다.
- **Lyra PIE 측정(`lyra_reload_probe.py`, 게임 시간, 6발 사격 후 재장전):** 탄약이 14에서 20으로 차는 시점이 3인칭 3.10초, 1인칭 3.02초(샘플 간격 약 0.4초 안). `MagState`가 0 → 2(1.07초) → 1(1.49초) → 0(2.7초 이전)로 바뀌고, 왼손목의 총 기준 변위가 설계 곡선과 맞습니다(잡기 (6.1, −15.5, −7.0), 허리춤 (16.3, −36.8, −31.9)).
  - **미확인:** 1인칭 화면에서는 왼손이 프레임 아래로 나가서 손 모양을 눈으로 확인하지 못했고, 3인칭 스크린샷은 캐릭터 뒷모습이라 손이 가려집니다. 손가락 모양(팩의 손가락 애니메이션)은 푸리나에 손가락 본이 없어 반영하지 않았습니다. 총이 재장전 중 기울지는 않습니다(팩도 거의 안 기웁니다).

- **Lyra에서 키 입력이 전혀 안 먹던 문제 (`lyra_input_dump.py`, `lyra_fix_input.py`):** 푸리나 폰은 `BeginPlay`에서 `GetController → Cast To PlayerController → EnhancedInputLocalPlayerSubsystem → AddMappingContext`(기본 IMC와 `IMC_FurinaStance`, 우선순위 100)로 입력 매핑을 추가합니다. 이전 BP 전용 프로젝트는 레벨에 놓인 폰이라 `BeginPlay` 전에 조종이 연결됐지만, Lyra는 폰을 스폰해 `BeginPlay`가 돈 뒤에 possess 하므로 그 시점의 컨트롤러가 비어 캐스트가 실패하고 이동·시점·사격·재장전·조준·앉기 키 매핑이 전부 빠졌습니다. 캐스트의 입력을 `GetPlayerController(0)`(노드 `FIN_GetPC0`)로 바꿔 고쳤습니다. Lyra PIE에서 W 누름 2초 후 푸리나가 앞으로 달려가고 V(시점 전환)와 클릭 사격이 반응하는 것을 확인했습니다.
  - 주의: 다른 에디터가 같은 프로젝트를 열어 둔 상태에서 `-ExecutePythonScript` 헤드리스 에디터로 저장하면 저장이 실패합니다(`save_loaded_asset`이 False). 에디터가 열려 있으면 그 에디터의 Cmd 상자에서 `py <파일> keep`(스크립트가 `keep`이면 종료하지 않음)으로 실행하세요.
  - 미확인: 총알 BP(`BP_FurinaBullet`)가 맞은 뒤 `Hit_OtherComp`/`Bullet` 접근 None 런타임 오류가 PIE 로그에 남습니다(이전부터 있던 것으로 이번에 조사하지 않았습니다).

## 2026-11-17 Lyra 1인칭/견착 사격 수정 모음 (마우스 반전, 가득 찬 탄창 재장전, 총알 충돌, 최적화)

- **마우스 상하 반전 + 감도 (`lyra_look_dump.py`, `lyra_fix_look.py`):** 푸리나 폰의 `Get Look Rate`는 이전 프로젝트의 레거시 입력 배율(`bEnableLegacyInputScales`, 요 +2.5 / 피치 −2.5)을 전제로 만들어져 있었습니다. Lyra는 `DefaultGame.ini`에서 `InputYawScale=1.0`, `InputPitchScale=1.0`이라 상하가 뒤집히고 감도가 2.5분의 1이 됩니다. 프로젝트 설정(Lyra 영웅들이 의존)은 건드리지 않고 함수의 상수를 바꿨습니다: 상하 선택(`K2Node_CallFunction_10`) A(반전 켬) −1 → +2.5, B(반전 끔) +1 → −2.5, 좌우(`K2Node_CallFunction_0` B) 1.0 → 2.5. Tab(InvertLookUp?)은 그대로 동작합니다.
- **가득 찬 탄창에서도 재장전되던 버그 (`lyra_fix_reload_full.py`):** 재장전 허용 조건 `M4_NotFull`(잔탄 < N)의 N이 예전 30발 탄창 값(30)으로 남아 있었습니다(탄창을 20발로 바꿀 때 `TFP_MagRoom`의 20만 바꿨음). 20/20이면 `20 < 30`이 참이라 재장전이 시작됐습니다. N을 20으로 고쳤습니다.
- **총알이 총구/코앞에 박힌다는 신고 (`lyra_fp_bullet_probe*.py`, `lyra_shoulder_probe.py`, `lyra_slowmo_probe.py`, `lyra_fx_collision_dump.py`, `lyra_bullet_resp_dump.py`, `lyra_shot_nodes_dump.py`):**
  - **재현하지 못했습니다.** 1인칭 연사 12발과 TP / 견착 / 1인칭 / 1인칭 정조준 각 3발(글로벌 타임 딜레이션 0.01 슬로모션으로 매 프레임 추적)에서 총알이 총구 앞(150 cm 이내)에서 멈춘 경우가 없었습니다. 정면에 가까운 장애물(예: 140 cm 앞의 기둥)이 있으면 당연히 그 앞에서 멈춥니다. 12발 중 4발이 스폰 프레임에 사라진 것은 낮은 프레임에서 한 틱(최대 약 30 m)에 벽에 닿아서였습니다.
  - 조사로 확인한 것: 조준점은 카메라에서 쏜 Visibility 라인 트레이스의 첫 맞는 점이고(자신 무시, 없으면 100 m), 총알은 `Muzzle(소총 로컬 (0, 40.5, 3.4)) → 조준점`으로 날아갑니다. 총알 `Bullet` 구는 Visibility와 Camera 채널을 Block하고 있었습니다(PhysicsBody만 무시). 탄피/버린 탄창은 PhysicsBody 물리 바디, 총구 화염은 충돌 없음.
  - **가능한 원인을 막는 방향으로 고쳤습니다**(`lyra_fix_shots.py`): (1) 총알의 Visibility/Camera 응답을 Ignore로 바꿔 날아가는 총알이 다음 조준선이나 카메라 붐에 걸리지 않게 했습니다. (2) 총구 가드: 발사 때 카메라 → 총구 선분(Visibility, 자신 무시)이 막혀 있으면(총구가 벽 반대편에 걸친 경우) 총알을 카메라 위치에서 생성합니다(노드 `FSG_Trace`, `FSG_Select`). 수정 후 같은 슬로모션 시험에서 견착/1인칭/정조준 모두 총알이 약 8000 cm를 날아갔습니다(TP의 140 cm는 앞 기둥에 맞은 것).
  - 아직 확실하지 않습니다. 재현 조건(어느 벽/물체 앞인지, 이동 중인지, 연사 몇 번째인지)을 알려 주면 다시 봅니다. PIE 로그의 `Hit_OtherComp ... Bullet 유효하지 않습니다` 경고는 같은 프레임에 이미 파괴된 총알에 Hit 이벤트가 한 번 더 들어와 나는 것이며(14회), 무해합니다.
- **최적화(적용한 것만):**
  - 총알 BP의 적중 경로에서 디버그 `PrintString` 2개(`FRC_PrintHit`, `FRC_PrintTrue`)를 실행 경로에서 뺐습니다. 맞을 때마다 문자열 약 20개를 이어 붙여 화면에 출력하던 디버그 출력입니다(노드는 남아 있으나 연결되지 않습니다). 조준점/도탄 로직은 그대로입니다.
  - `FurinaMagUpdate` 타이머를 0.016초에서 0.033초로 줄였습니다(`MagState` 전환 폭 0.06초라 충분).
  - **측정하지 않았습니다.** 프레임 수 비교는 하지 않았고, 이 개발 PC의 Lyra PIE는 셰이더 컴파일 등으로 원래 15~30 fps라서 이 두 가지의 효과는 작을 것입니다. 큰 비용은 Lyra의 렌더링 설정(Lumen/가상 섀도 맵 등)입니다.
- **1인칭 재장전 모션이 반영되지 않았다는 신고:** 확인하지 못했습니다. 1인칭 화면에서는 재장전 동안 왼손이 카메라 아래로 나가 소총만 보이므로(총 기준으로 −37 cm 뒤, −33 cm 아래) 변화가 보이지 않을 수 있습니다. 곡선과 `MagState` 값은 1인칭에서도 측정과 일치했습니다(위 재장전 섹션).

## 2026-11-17 연사 총알이 총구에서 사라지는 버그 수정 + 견착 카메라 낮춤

- **원인 확인 (`lyra_samefame_probe.py`, 글로벌 타임 딜레이션 0.01 슬로모션에서 총알을 매 틱 추적):** 발사 타이머(`FurinaRifleShot`)는 `bMaxOncePerFrame=false`라서 프레임이 느리면(이 PC의 Lyra PIE는 15~30 fps) 한 프레임 안에서 여러 번 실행됩니다. 그러면 같은 총구 위치에 총알이 동시에 여러 발 생깁니다. 총알의 오브젝트 타입이 `WorldDynamic`이고 `WorldDynamic`을 Block 하므로 총알끼리 서로 막아서 첫 틱에 사라졌습니다. 프레임당 1발 4그룹은 4발 모두 약 2800 cm를 날아갔고, 프레임당 3발 그룹은 3발 중 0발·1발만 관측(나머지는 생성 즉시 소멸)되거나 약 1100 cm에서 멈췄습니다. 20발 연사에서 몇 발이 총구에서 막히던 증상과 맞습니다.
- **수정(`lyra_bullet_objtype.py`):** `BP_FurinaBullet`의 `Bullet` 구 오브젝트 타입을 `WorldDynamic` → `PhysicsBody`로 바꿨습니다. 총알은 `PhysicsBody` 응답이 이미 Ignore라서 총알끼리(그리고 탄피/버린 탄창과) 충돌하지 않고 벽/액터/폰은 그대로 맞춥니다(응답 Block 유지). 수정 뒤 같은 시험에서 프레임당 3발 그룹 4개 모두 3발이 약 2800 cm를 날아갔습니다(프레임당 1발과 같음). 위 `lyra_fix_shots.py`의 (Visibility/Camera 무시, 총구 가드)와 함께 적용됩니다.
- **견착 카메라 높이(`lyra_shoulder_cam_lower.py`):** 노드 `K2Node_FPT_TgtZ`(`CameraBoom.TargetOffset.Z` 선택, 견착 3인칭일 때 값) 30 → 20 cm로 10 cm 낮췄습니다. 더 낮추거나 되돌리려면 이 노드 A 값을 바꾸면 됩니다.

## 2026-11-17 푸리나를 Lyra 영웅으로 (체력·팀·어빌리티), Lyra 무기 제거, 봇 활성화

목표: 기존 Lyra 총 대신 나만의 총을 쓰고, 맵을 넓혀 AI 봇과 게임한다. 봇은 지금은 기본 Lyra 마네킹이고, 적 3D 디자인은 나중에 임포트한다. 애니메이션은 되도록 프로젝트에 있는 것을 재사용한다.

- **푸리나 폰을 `LyraCharacter` 자식으로 (`lyra_furina_reparent.py`):** 원본을 `/Game/Furina/Backups/ThirdPersonCharacter_BP_PreLyraHero`로 백업한 뒤 부모를 `LyraCharacter`로 바꿨습니다. Lyra의 `CameraComponent`는 `auto_activate`를 꺼서 푸리나의 카메라 붐을 그대로 씁니다. 컴파일은 경고만 있습니다.
- **`LyraHeroComponent` 추가 (`lyra_furina_add_hero.py`):** `ULyraPawnExtensionComponent::InitializeAbilitySystem`은 `LyraHeroComponent`만 호출합니다(LyraHeroComponent.cpp:164). 없으면 폰이 ASC에 연결되지 않아 체력이 0/0이었습니다. 추가 후 PIE에서 체력 100/100, `DamageSelfDestruct` → 사망 → 새 푸리나 폰으로 리스폰(100/100)을 확인했습니다(`lyra_hero_probe.py`, `Data/lyra_hero_probe.json`). 팀 ID는 파이썬으로 노출되지 않아 확인하지 못했습니다.
- **어빌리티 세트 (`lyra_furina_hero_setup.py`):** `AbilitySet_ShooterHero`를 `/Game/Furina/Lyra/AbilitySet_Furina`로 복제하고 무기 계열(`GA_QuickbarSlots/ADS/Grenade/DropWeapon/Melee`)을 뺐습니다. 11개 중 6개(Jump, Death, Dash, Emote, SpawnEffect, Reset)가 남았습니다. `HeroData_Furina`는 이 세트를 씁니다.
- **경험(Experience):** `B_Furina_Experience`에서 `LAS_ShooterGame_StandardComponents/StandardHUD/SharedInput` 액션 세트를 뺐습니다(무기 HUD·퀵바·공용 입력). GameFeatureAction 내부 구조체는 파이썬으로 읽을 수 없어 항목별 편집 대신 세트째 뺐습니다.
- **게임 모드:** `B_LyraGameMode`가 `GetDefaultPawnClassForController`를 덮어써서 사람 플레이어는 푸리나 폰, 나머지(봇)는 PawnData의 Lyra 마네킹을 받습니다.
- **맵 (`lyra_map_bots_setup.py`):** `L_FiringRange_WP`의 무기 스포너/인벤토리 패드 액터 4개를 지웠습니다. PIE 봇 수 0 오버라이드는 해제해서 봇이 3명 나옵니다. 봇은 무기가 없어서 쏘지 못합니다(행동 트리가 무기 어빌리티를 씁니다). 내 총을 만든 뒤 연결해야 합니다.
- **Lyra 무기 콘텐츠는 삭제하지 않았습니다.** 게임플레이에서만 빠졌고 파일은 그대로입니다. 내 총이 대체한 뒤 참조를 확인하고 지웁니다.
- **히어로 추가 뒤 사격이 안 되던 문제 (`lyra_input_probe.py`, `lyra_call_shot.py`, `lyra_lmb_scan.py`, `lyra_ia_dump.py`):** 이동·시점·`V`는 되는데 좌클릭 사격만 안 나갔습니다(잔탄 20 고정). 컨트롤러는 좌클릭을 받고 있었고(`is_input_key_down`), 이벤트를 직접 호출하면(`call_method('FurinaRifleShot')`) 20 → 19로 줄어서 사격 로직은 정상이었습니다. `LyraGame/Character/LyraHeroComponent.cpp:244`의 `ClearAllMappings()`가 푸리나 BP가 `BeginPlay`에서 넣은 매핑을 지우고 `DefaultInputMappings`만 다시 넣습니다. 그리고 `/Game/Input/Mappings/IMC_Default`가 좌클릭을 `IA_Weapon_Fire`(consume_input=True)로 가로채고 있었습니다.
  - `lyra_furina_hero_imc.py`: 푸리나 폰의 히어로 컴포넌트 `DefaultInputMappings`에 `Default_IMC`(우선순위 0)와 `IMC_FurinaStance`(100)를 등록했습니다.
  - `lyra_fix_lmb_consume.py`: `Direction_IA`(좌클릭, 레일 방향)의 `consume_input`을 껐습니다.
  - `lyra_fix_imc_consume.py`: `IA_Weapon_Fire`, `IA_Weapon_Fire_Auto`, `IA_Weapon_Reload`의 `consume_input`을 껐습니다(무기는 이미 빠졌습니다). 이동·점프·앉기·대시·시점은 처음에 같이 껐다가 푸리나 BP와 이중 처리될 수 있어 다시 켰습니다(기본값 True).
  - 결과: PIE에서 좌클릭 연사로 20 → 0, `R`로 재장전해서 20발이 채워졌습니다. 어느 수정이 결정적이었는지는 하나씩 떼어 검증하지 않았습니다(셋 다 적용된 상태에서만 확인).
- **테스트 팁:** 이 PC의 PIE는 프레임이 낮아서 `key` 탭(눌렀다 바로 뗌)은 한 프레임 안에 끝나 입력이 안 잡힙니다. `hold_key`로 0.4초 이상 누르면 잡힙니다.
- **PIE 로그 소음:** 사망/리스폰 순간 `BP_FurinaHUD`의 `Branch`(GetOwningPawn None)와 `Homing_Attack_Component_BP`(`Reticle_Widget_WBP` 캐스트 None) 런타임 오류가 남습니다. 리스폰 중 폰이 없는 짧은 시간의 접근이고, 이번에 고치지 않았습니다.
- **다음 일:** (1) 내 총을 데이터 에셋으로(피해량·연사·탄창·반동, M4 첫 번째), (2) 봇이 그 총을 쏘게 연결, (3) 맵 확장(월드 파티션), (4) 사망/피격 모션은 기존 애니메이션 재사용, (5) 다른 UE 프로젝트로 내보내는 구성(`Scripts/Tools/build_export_manifest.py`는 작성만 했고 실행하지 않았습니다), (6) GitHub 푸시.

## 2026-11-17 견착·정조준·2번 무기(권총) 복구 + 봇 모션 복구

- **증상:** Lyra 영웅으로 바꾼 뒤 우클릭 정조준/견착과 2번 무기(P220 권총)가 안 됐습니다.
- **원인 (`lyra_rmb_scan.py`):** `/ShooterCore/Input/Mappings/IMC_ShooterGame`이 활성이고, 거기의 `IA_ADS`(우클릭), `IA_QuickSlot1/2`(1·2번)가 `consume_input=True`라서 같은 키에 묶인 푸리나의 `IA_FurinaADS/Shoulder/Weapon1/Weapon2`를 가로챘습니다. 사격이 안 되던 것(`IMC_Default`의 `IA_Weapon_Fire`)과 같은 종류입니다.
- **수정 (`lyra_fix_shootergame_consume.py`):** `IMC_ShooterGame`의 액션 10개(`IA_ShowScoreboard, IA_ADS, IA_Grenade, IA_Emote, IA_QuickSlot1/2/3, IA_Melee, IA_QuickSlot_CycleBackward/Forward`)의 `consume_input`을 껐습니다. `IA_Melee`(C), `IA_Emote`(B), `IA_Grenade`(Q)도 푸리나의 앉기·발사모드·레일 전환 키와 겹쳐 있었습니다. Lyra 무기는 게임플레이에서 이미 빠졌습니다.
- **확인:** PIE에서 `2`를 0.4초 눌러 P220 8/96 SEMI가 나오는 것과, 우클릭 탭으로 1인칭 정조준이 켜지는 것을 봤습니다. **견착(우클릭 길게)은 도구에 길게 누르기가 없어 직접 확인하지 못했습니다**(같은 입력 경로입니다).
- **봇 모션 (`lyra_bot_anim.py`, `lyra_bots_unarmed_layers.py`):** 봇은 `ABP_Mannequin_Base`로 이동(속도 184~600)은 하지만 A포즈로 미끄러졌습니다. Lyra 마네킹의 이동·대기 모션은 무기 인스턴스(`B_WeaponInstance_Base`)가 장착 때 거는 애님 레이어에서 오는데, 무기를 뺐더니 레이어가 없었습니다. `B_Hero_ShooterMannequin`(ShooterCore 플러그인)의 `BeginPlay`에 `Mesh → LinkAnimClassLayers(ABP_UnarmedAnimLayers)`를 추가해 기존 Lyra Unarmed 애니메이션을 재사용합니다(새 애니메이션 없음). PIE에서 봇이 달리기 모션으로 움직이는 것을 확인했습니다. 총을 든 자세(조준·사격 모션)는 내 총을 연결할 때 정합니다.

## 2026-11-17 Shift를 원래 달리기로 복구

- **원인:** `AbilitySet_Furina`에 Lyra 대시(`GA_Hero_Dash`)가 남아 있었고, `IA_Ability_Dash`(LeftShift, `consume_input=True`)가 Shift를 가로채 푸리나의 `IA_FurinaSprint`가 막혔습니다.
- **수정 (`lyra_sprint_restore.py`):** `AbilitySet_Furina`에서 대시 어빌리티를 뺐습니다(6개 → 5개: Jump, Death, Emote, SpawnEffect, Reset). `IA_Ability_Dash`의 `consume_input`도 껐습니다.
- **확인 (`lyra_input_probe.py`):** W만 누르면 속도 120, Shift+W는 138 → 346 → 362 → 600으로 올라갑니다(이 PC의 PIE 속도 단위 기준 5배).

## 2026-11-17 앉기 이동속도 복구 (액터 틱이 꺼져 있던 문제)

- **증상:** 앉아서 걷는 속도가 원래와 달랐습니다. PIE에서 재 보니 앉아서 걸으면 300cm/s였고(`MaxWalkSpeedCrouched`가 CMC 기본값 300 그대로), README의 설계값은 앉기 걷기 90 / Shift 360입니다.
- **원인 (`lyra_tick_api.py`, `lyra_fix_tick.py`):** 푸리나 폰의 틱 설정이 `bCanEverTick=True`, `bStartWithTickEnabled=False`였습니다. `ALyraCharacter` 생성자가 틱을 끄고 시작하기 때문에 `LyraCharacter`로 부모를 바꾼 뒤 BP의 `Event Tick`이 돌지 않았습니다. 앉기/조준/견착 속도 제한(`K2Node_FPT_CapSpeed`, `CapSpeedC`로 `MaxWalkSpeed`·`MaxWalkSpeedCrouched`를 설정)과 그 밖의 틱 로직이 전부 멈춰 있었습니다.
- **수정:** `primary_actor_tick`의 `bStartWithTickEnabled`를 True로 켜고 컴파일·저장했습니다.
- **확인 (`lyra_input_probe.py`):** 앉으면 `MaxWalkSpeed`/`MaxWalkSpeedCrouched`가 둘 다 90으로 잡히고 앉아서 걷는 속도가 300 → 약 70~90(이 PC의 낮은 프레임 때문에 흔들림)으로 내려왔습니다.
- **남은 것:** Shift를 누른 채 앉아 걸어도 90입니다(설계는 360). 속도 로직이 `Sprint?` 판정에 `IsInputKeyDown`을 쓰는데 그 노드의 `Key` 핀 기본값이 `(`로 깨져 있습니다. Lyra 이전 백업 BP에도 똑같이 깨져 있어서(`lyra_sprint_key_pin.py`) 이번 이동 때문에 생긴 것이 아니라 이전부터 있던 문제로 보입니다. 아직 고치지 않았습니다.
- **비슷한 증상 후보:** 같은 틱 로직을 쓰는 서서 조준/견착 속도 제한(60/120)과 견착 카메라 높이도 틱이 꺼져 있는 동안 멈춰 있었을 수 있습니다. 이번 수정으로 같이 돌아오지만 따로 측정하지는 않았습니다.

## 2026-11-18 견착 진입 2배 느리게, 앉기 3배 느리게

"2배/3배 늘려"를 **전환이 걸리는 시간을 늘린다(느리게)**는 뜻으로 확인했습니다. 처음에는 빠르게로 잘못 해석해 한 번 올렸다가(14→28 등) 바로잡았고, 아래는 **원래 값 기준**의 최종 값입니다. 자세로 들어가는 전환 속도만 바꿨고 앉아서 걷는 이동 속도(90)와 견착 중 이동 속도(60/120)는 그대로입니다. (`lyra_shoulder_crouch_speed.py`, 결과 `Data/lyra_shoulder_crouch_speed.json`)

| 대상 | 위치 | 원래 → 지금 |
|---|---|---|
| 견착 자세(소총 허리 → 견착) | `CR_FurinaSecondary` `ShW.Blend` | 14 → 7 (1/2) |
| 3인칭 견착 카메라 옆 오프셋 | 폰 `K2Node_FPT_NewOff` `InterpSpeed` | 10 → 5 (1/2) |
| 3인칭 견착 카메라 FOV | 폰 `K2Node_FPT_NewFov` `InterpSpeed` | 10 → 5 (1/2) |
| 앉기 자세(골반·발 IK) | `CR_FurinaSecondary` `CrouchW.Blend` | 9 → 3 (1/3) |
| 앉기 이동 블렌드(서기↔앉기) | `ABP_Furina` `TFPCrouchSmooth` `InterpSpeed` | 10 → 3.3333 (1/3) |

- 5곳 모두 컴파일·저장 확인했습니다. `ue_build_cr.py` 기본값도 `poses.shoulder_blend`=7, `cr_params.crouch_blend`=3으로 맞췄습니다.
- PIE에서 실제 전환 시간은 재지 않았습니다. 견착(우클릭 길게)은 도구로 길게 누르기를 못 해서 PIE에서 확인하지 못했습니다.
- 캡슐 높이(96 → 58)는 엔진이 즉시 바꾸므로 그대로입니다. 3인칭 카메라 FOV 보간 노드는 견착 말고 다른 상태에서도 같이 쓰일 수 있어 함께 느려질 수 있습니다.

## 2026-11-18 최적화 (렌더 설정) — 설정은 바꿨지만 최종 효과는 아직 재지 않았습니다

- **병목 확인 (`lyra_perf_csv.py`, `Scripts/Tools/csv_perf_summary.py`):** PIE에서 20초 CSV 프로파일을 잰 결과 평균 프레임 86ms(약 11.6fps), 이 중 GPU 80ms, 게임 스레드 12ms였습니다. 게임 스레드는 GPU를 기다리는 시간이 대부분이고 `TickActors` 0.7ms, `Animation` 0.8ms라서 **블루프린트/애니메이션이 아니라 GPU 렌더링이 병목**입니다. 그래픽카드는 RTX 2060이고 프로젝트 설정은 `sg.*` 전부 Epic, Lumen GI + **하드웨어 레이트레이싱** + **가상 섀도맵**(VSM)이었습니다.
- **설정 비교 (`lyra_perf_ab.py`, 실시간 dt, 런타임 cvar 전환):** 측정이 많이 흔들렸습니다(봇이 움직이고 cvar를 바꿀 때마다 셰이더/BVH 재생성 히치가 생기며, 같은 기본값이 13~38fps로 나왔습니다). 그래서 항목별 효과를 정확한 배수로 말할 수는 없습니다. 눈에 띈 것: HWRT 끄기 + VSM 끄기 + 화면 75%를 합친 구간이 마지막 기본값 구간(25fps)보다 크게 빨랐습니다(59fps).
- **적용 (`Config/DefaultEngine.ini`):** `r.Lumen.HardwareRayTracing=False`, `r.RayTracing=False`, `r.Shadow.Virtual.Enable=0`. 화면 비율(75%)과 `sg.*` 품질은 화질 영향이 커서 바꾸지 않았습니다. **`r.RayTracing`은 에디터 재시작이 있어야 적용되므로 저장 후의 fps는 아직 재지 못했습니다.**
- **화질 변화:** HWRT 끄면 Lumen이 소프트웨어 트레이싱으로, VSM 끄면 일반 섀도맵으로 바뀌어 그림자/반사가 조금 달라집니다. 되돌리려면 위 세 줄을 `True/True/1`로 바꾸면 됩니다.
- **하지 않은 것:** 로그의 `BP_FurinaHUD` / `Homing_Attack_Component_BP` / `ABP_Furina`의 None 접근 오류 스팸(PIE 한 번에 수천 줄)은 CPU 병목이 아니어서 고치지 않았습니다. 텍스처 풀이 6GB 카드에서 "비디오 메모리 초과(약 400MB)"를 내던 것은 레이트레이싱을 끄면 줄어들 것으로 예상하지만 확인하지 않았습니다.

## 2026-11-18 3인칭 소총 개머리판이 몸을 뚫는 문제 — 해결하지 못했습니다

- **측정 (`lyra_stock_probe.py`):** 3인칭 서 있을 때 개머리판 끝이 폰 로컬 (7, 7.5, 37)이고 가슴 뼈대(`spine_05`)가 (4~5, 0.5, 40.6)이라, 개머리판은 가슴 중심에서 앞으로 약 2cm, 오른쪽으로 7cm 지점에 있습니다(몸 안쪽). 몸 충돌체(피직스 에셋)가 없어서 몸 표면까지의 거리는 잴 수 없었고 위치만 비교했습니다.
- **총을 앞으로 옮기는 방법은 막힙니다 (`Scripts/Tools/tp_stock_shift.py`, `lyra_tp_stock_apply.py`):** 3인칭 총 오프셋(`TpD`)과 왼손 뒤로 빼는 양(`LBack`)을 앞으로 +4cm, +10cm로 바꿔도 개머리판은 +1.6cm에서 멈췄고 양팔 길이(어깨→손 53cm)는 변하지 않았습니다. 팔이 이미 거의 다 펴져서 소총이 더 앞으로 못 나갑니다. 정확히는 팔 도달 거리에서 막힌다고 보지만 CR 안의 어느 노드가 막는지는 확인하지 못했습니다.
- **총을 돌리는 방법도 실패했습니다 (`lyra_tp_cant.py`):** 총구를 몸 안쪽으로 10° 돌려 개머리판을 바깥으로 빼려고 CR에 회전 노드(`TpCantAng`, `TpCantQ`, `GRotC`)를 넣었지만, 손만 1~2cm 움직이고 개머리판 위치는 그대로였습니다(총 메시는 `GRotR`이 아닌 다른 경로의 회전을 쓰는 것으로 보입니다).
- **원상 복구했습니다:** `TpD`/`LBack`은 원래 값(-0.85/6.07/-14.51, -4.35/6.07/-12.01, 9.6)으로 되돌렸고 `fp_rig.json`도 원래대로입니다. 회전 노드는 각도 0(항등)으로 남아 있어 동작에는 영향이 없습니다(필요 없으면 `CR_FurinaSecondary`에서 삭제하면 됩니다).
- **남은 방법:** (1) 개머리판 모델을 Blender에서 몇 cm 줄이기(눈에 띄는 변화가 적고 팔 포즈를 안 건드림), (2) 팔이 닿는 거리를 늘리는 CR 변경(팔 늘어남/어깨 위치), (3) 개머리판을 어깨 앞쪽에 대는 대신 허리 옆에 낮게 드는 자세로 변경.

## 2026-11-18 1인칭 낙하 중 3인칭 전환 수정 + GPU 부하 재측정

- **낙하 중 3인칭 전환 (`lyra_fall_view_trace.py`, `lyra_fix_fall_view.py`, `lyra_fall_probe.py`):** 푸리나 폰의 시점 타이머(`K2Node_FPV_Upd`, 0.05초)가 `Forced = (레일 | 집라인 | 레일 점프) OR AirFast`로 3인칭을 강제하고 있었습니다. `AirFast = 공중 AND (속도 + (3인칭이면 +10000) > 1200)`이라 낙하 속도(3D 속도)가 1200cm/s를 넘으면 3인칭이 되고, 3인칭이 되면 +10000 보정 때문에 착지할 때까지 유지됐습니다. `K2Node_FPV_Forced.B`에서 `AirFast` 연결을 끊고 false로 뒀습니다(레일/집라인/레일 점프 강제 3인칭은 그대로). PIE에서 8000cm 위에서 떨어뜨리면 속도 3500cm/s까지 `FPCamera`가 계속 활성(1인칭 유지)이었습니다. 수정 전 상태를 같은 방법으로 재현해 보지는 않았고, 사용자가 실제로 고쳐졌다고 확인했습니다.
- **에디터 재시작 후 GPU 측정 (`lyra_perf_gpu.py`, CSV 프로파일, 단계마다 워밍업 25초 후 12초):** `DefaultEngine.ini` 변경(하드웨어 RT/RT/VSM 끔)이 적용된 상태에서 평균 44.6fps(GPU 중앙값 19.8ms)였습니다. 변경 전 11.6fps(GPU 80ms)와 비교하면 크게 빨라졌지만, 변경 전 측정은 셰이더 컴파일 구간이 섞여 있어 정확한 배수는 아닙니다. 누적 단계: `sg.*Quality 2`(그림자/GI/반사/후처리/이펙트) 65fps(GPU 12.7ms), 여기에 화면 80% 60fps, 70% 75.6fps. **아직 프로젝트 설정에 반영하지 않았습니다**(런타임 cvar로만 측정). 게임 스레드는 모든 단계에서 중앙값 10ms 안팎이라 65fps 이상에서는 CPU 쪽(봇 3명, 애니메이션 등)이 다음 병목입니다.

## 2026-11-18 봇 비용 측정, 소총 색, 3인칭 재장전 손-탄창 정렬 (진행 중)

- **봇 비용 (`lyra_bot_cost.py`):** 봇 3명이 있을 때 67.9fps, 없앴을 때 67.1fps로 차이가 없었습니다. 다만 이 비교는 유효하지 않습니다. 봇을 지워도 AI 스포너가 다시 만들어서 삭제 후에도 3명이었고, 측정 순간 봇 속도가 0(가만히 서 있음)이었습니다. 게임 스레드 항목은 `UI` 3.2ms, `Animation` 1.0ms, `TickActors` 0.5ms였습니다. 봇이 지금 움직이지 않는 이유(무기를 뺀 뒤 행동 트리가 무기 어빌리티를 못 써서 멈춘 것으로 추정)는 확인하지 못했습니다.
- **소총 회색 (`lyra_m4_material_check.json`, `FBX/M4/ColtTex`):** 텍스처가 빠진 것은 아닙니다. `SK_M4A1`(본체·가구·뒤가늠자)과 `SM_M4Mag`의 머티리얼 4개 모두 BaseColor/Normal/Metallic/Roughness/AO 다섯 장이 연결돼 있습니다. 회색으로 보이는 이유는 원본 텍스처 값입니다: BaseColor 평균이 본체 59, 가구(핸드가드·개머리판) 52, 가늠자 50, 탄창 67(0~255, 어두운 회색)이고 Metallic 평균이 본체 219, 가늠자 224, 탄창 196, 가구 118이라 낮 햇빛 아래에서 은회색 금속처럼 반사됩니다. 실제 M4의 개머리판/핸드가드는 검은 폴리머라 Metallic이 0에 가까워야 합니다. 아직 바꾸지 않았습니다.
- **재장전 손-탄창 측정 (`lyra_reload_view.py`, `lyra_reload_mag_probe.py`):** 3인칭 옆모습 캡처(폰을 90°/-90° 돌려 카메라가 옆을 보게 함, 슬로모 0.15, `HighResShot 3`)와 총 기준 좌표 측정으로 확인했습니다. 손바닥 중심은 왼손목과 `MiddleFinger1_L`의 중간으로 잡았고, 원래 상태에서 탄창을 잡는 순간 손바닥이 탄창 중심에서 총 기준 왼쪽 약 8.4cm, 뒤쪽 약 9cm 떨어진 곳이었습니다. 뒤쪽 9cm는 3인칭에서 왼팔 도달을 위해 손목을 9.6cm 뒤로 당겨 놓은 값(`LBack`)이 재장전 곡선(`ReloadLX/Y/Z`)에 그대로 더해지기 때문이고, 왼쪽 쏠림은 곡선이 Honey Badger 팩 탄창 위치 기준이라서입니다.
  - `CR_FurinaSecondary`에 재장전 보정 노드(`RlEnvRaw`, `RlEnv`, `RlEnvTp`, `RlDelta`, `RLV2`)를 넣었습니다. 가중치는 `clamp(ReloadLX/6, 0, 1) × TpW`(손이 탄창으로 가며 0 → 1, 쥐는 동안 1, 핸드가드로 돌아가면 0, 1인칭 영향 없음)이고 보정 벡터는 `RlDelta.Value`입니다.
  - **현재 저장된 값 (-4.8, -2.0, +2.1)은 중간 값입니다.** 재측정하니 좌우(X)는 3.6cm 차이로 맞았지만, Y(앞뒤)는 손바닥이 탄창 중심보다 9.2cm 뒤입니다. 보정값 Y를 +7.2로 바꿔야 맞습니다(`lyra_reload_palm_fix.py keep -4.8 7.2 2.1`). 에디터에서 PIE가 돌고 있어 저장이 안 돼 아직 적용하지 못했습니다.
  - 앞서 넣은 `LBackW`/`NotReloadL`(재장전 중 `LBack` 페이드)은 쥘 때와 끼울 때 값이 달라 끼우는 순간 탄창이 9cm 튀어서 끄고(`NotReloadL.TargetMaximum=1`) 노드만 남겼습니다. 탄창은 잡는 순간의 손목 기준 오프셋으로 손에 붙기 때문에, 보정은 쥐는 동안 일정해야 장착 위치와 맞습니다.
- **아직 하지 않은 것:** (1) 소총에 꽂힌 탄창의 아귀(삽입구) 정렬: 탄창 메시는 원점이 총과 같아 장착 위치가 원래 항등이라 눈에 띄는 어긋남을 측정으로 확인하지 못했습니다. 정렬이 틀리다면 어느 방향으로 어긋나 보이는지 알려 주세요. (2) 개머리판: 왼쪽 어깨를 살짝 빼고 오른쪽을 넣는 상체 비틀기(스파인 yaw)는 CR에서 시작하지 못했습니다.

## 2026-11-18 인게임 소총이 뭉개져 보이는 이유

- **가장 큰 원인은 제가 남겨 둔 측정용 설정이었습니다.** `lyra_perf_gpu.py`가 마지막 단계에서 `r.ScreenPercentage 70`과 `sg.ShadowQuality/GlobalIlluminationQuality/ReflectionQuality/PostProcessQuality/EffectsQuality 2`를 런타임으로 걸었고, 되돌리지 않았습니다. 콘솔 변수는 PIE를 멈춰도 에디터가 켜져 있는 동안 유지되므로 사용자가 플레이하는 내내 70% 해상도로 그린 뒤 늘려서 흐릿했습니다(`lyra_cvar_now.py`로 확인). `lyra_cvar_reset.py`로 100%/sg 3으로 되돌렸고, `lyra_perf_gpu.py`는 끝날 때 자동으로 되돌리게 고쳤습니다. 에디터를 다시 켜도 초기화됩니다.
- **텍스처 설정은 문제가 아닙니다 (`lyra_m4_tex_check.py`):** 20장 중 19장이 4096×4096(뒤가늠자 5장은 원본이 2048), `never_stream=True`(스트리밍으로 해상도가 떨어지지 않음), 압축/sRGB 정상입니다.
- **다만 한 장은 원본부터 저해상도입니다:** 본체(리시버·총열) BaseColor `T_Colt_Main_BaseColor`가 1254×1254입니다. 다운로드한 `Downloads/colt-m4a1-carbine/textures/colt_m4_main_BaseColor_gfl.png`가 처음부터 1254×1254(Normal/Metallic/Roughness/AO는 4096)이고 UE에는 그대로 들어갔습니다. 앞서 올린 참고 사진은 이보다 높은 해상도의 베이스컬러로 렌더한 것으로 보입니다. 이 한 장만 키우려면 원본 제공처에서 4096짜리를 받거나 업스케일(디테일은 늘지 않고 경계만 부드러워짐)해야 합니다.
- **그 밖의 흐림 요인:** 안티앨리어싱이 TSR(`r.AntiAliasingMethod=4`)이라 움직일 때 약간 부드럽게 보이고, 화면 비율이 100%여도 3인칭/1인칭 모두 `r.MotionBlur`가 켜져 있습니다(`r.DefaultFeature.MotionBlur=1`). 바꾸지 않았습니다.

## 2026-11-18 재장전 손 정렬 마무리, 탄창 기울기 점검, 3인칭 상체 비틀기, 소총 선명도

- **재장전 손-탄창 정렬(`lyra_reload_palm_fix.py`, 최종 보정 (-4.8, +7.2, +2.1)):** 3인칭 재장전 중 왼손 손바닥(손목과 `MiddleFinger1_L`의 중간)을 탄창 쪽으로 옮겼습니다. 측정(`lyra_reload_mag_probe.py`, 슬로모 0.15): 잡는 순간 탄창 중심 − 손바닥 = 총 기준 (-3.6, 0.0, +0.5)cm, 쥐는 동안 (-4.4, +0.2, +2.3)cm로 일정했습니다(원래는 앞뒤로 약 9cm, 좌우로 약 8cm 어긋나 있었음). 가중치는 `clamp(ReloadLX/6,0,1) × TpW`라서 1인칭은 그대로입니다. 쥐는 동안 오프셋이 일정해서 끼울 때 탄창이 튀지 않습니다.
- **탄창이 기울어 꽂혔다는 신고(`lyra_mag_rest_probe.py`, `lyra_reload_mag_probe.py`, `mag_fit.json`):** 변환 값으로는 기울기를 찾지 못했습니다. 소총 컴포넌트 대비 탄창 회전이 서 있는 자세와 재장전 전 구간에서 (0,0,0)이고, 몸통 메시가 스키닝된 `Grip` 뼈대도 항등입니다(뼈대 `Magazine`이 있지만 메시는 `Grip` 100%). 모델 자체(Blender로 FBX 확인)도 탄창이 수직이고 삽입구 안에 7~8cm 들어가 아래로 약 4cm만 나옵니다. 3인칭 서 있을 때 총이 대각선(휴식 자세)이라 탄창이 비스듬해 보였을 가능성이 큽니다. 육안으로 확정하지는 못했습니다.
- **3인칭 상체 비틀기(`lyra_torso_twist.py`, 14°):** `CR_FurinaSecondary`에서 머리 조준(`HeadAim`) 바로 앞에 `Spine`을 수직축으로 -14°(오른쪽 어깨 앞, 왼쪽 뒤) 돌리는 노드(`TwAng`, `TwQ`, `TwXf`, `TwRot`, `TwSet`)를 넣었습니다. 처음에는 뼈 이름을 Manny식(`spine_03`)으로 써서 아무 효과가 없었고, CR 계층의 이름(`Spine`)으로 고쳐서 동작했습니다. 가중치는 `TpW`(3인칭, 정조준이면 0)입니다. PIE 측정(`lyra_stock_probe.py`): 오른쪽 어깨(`Right-arm`)가 왼쪽(`Left-arm`)보다 앞으로 4.6cm 나와 있고 개머리판 끝이 앞으로 6.6 → 10.9cm(+4.3cm) 이동했습니다. **눈으로는 확인하지 못했습니다.** 자동 캡처에서 3인칭 카메라가 아래에서 올려다보는 각도가 되거나 1인칭으로 시작해서 옆모습을 얻지 못했습니다. 각도는 스크립트의 `DEG`(기본 14)로 바꾸고 다시 실행하면 됩니다(0이면 끔).
- **소총 선명도(`Config/DefaultEngine.ini` `[SystemSettings]`):** `r.MaxAnisotropy=16`, `r.Streaming.PoolSize=2500`을 추가했습니다(에디터 재시작 후 적용). 텍스처 풀이 기본 1000MB라 RTX 2060 6GB에서 "Video memory exhausted"가 계속 떠서 다른 텍스처가 낮은 밉으로 떨어질 수 있었습니다. 앞서 말씀드린 `T_Colt_Main_BaseColor`(1254×1254)는 원본이 작아서 그대로입니다.
- **PIE 중 Cmd 창 사용 주의:** PIE에서 마우스가 캡처돼 있을 때 Cmd 창을 클릭하면 시점이 돌아가 캡처/측정이 틀어집니다. Play 전에 `lyra_auto_check.py keep <태그>`로 무장해 두면 폰이 생기고 12초 뒤에 `lyra_stock_probe.py`와 `lyra_idle_view.py`가 입력 없이 실행됩니다.

## 2026-11-18 탄창이 삽입구 옆면 밖으로 튀어나와 회색 판처럼 보이던 문제 수정

- **증상:** 소총 탄창 부근에 회색 판이 비스듬히 튀어나와 보임(3인칭과 1인칭 모두). 이 부분은 재장전 때 뽑는 바로 그 탄창이었습니다. 앞서 저는 권총 부품(`FurinaPistolFrame/Slide`)을 의심했지만 소총 상태에서 둘 다 보이지 않음(`visible=False`)을 `lyra_pistol_vis.py`로 확인했습니다.
- **원인(`FBX/M4/SM_M4Mag.fbx`와 `SK_M4A1.fbx`를 Blender로 옆/앞에서 렌더한 `Data/mag_side.png`, `mag_front.png`와 높이별 단면 `mag_fit2.json`):** 탄창 x 범위가 [-1.18, 1.84]cm, 삽입구 하우징(리시버 아래 탄창 틀)이 [-1.5, 1.5]cm라서 탄창이 +X(왼쪽)로 약 0.33cm 치우쳐 있었습니다. 그래서 하우징 높이 구간(z -4 ~ 3.4)의 탄창 옆면이 하우징 바깥으로 나와 리시버 측면을 덮었고, 이것이 "삽입구 아래 작게 있어야 하는데 은색 판이 크게 튀어나옴"으로 보였습니다. 탄창과 총 사이의 회전은 처음부터 0°였습니다(`lyra_reload_mag_probe.py`, `lyra_mag_rest_probe.py`).
- **수정(`lyra_mag_fit_mesh.py`):** `SM_M4Mag` 정점(7024개)을 직접 편집했습니다. 모든 정점 x를 -0.33cm 옮겨 탄창 중심을 총 중심선에 맞추고, 하우징 안쪽 구간(z > -4)은 x 폭을 0.8배로 좁혔습니다(z -4.5 ~ -3.5에서 1 → 0.8로 부드럽게). 하우징 밖으로 나온 아래쪽 모양은 그대로입니다. 결과 x 범위는 [-1.51, 1.34]cm이고 하우징 높이 구간에서는 [-1.0, 1.0] 안쪽입니다. 원본은 `/Game/Furina/Backups/SM_M4Mag_pre_fit`에 복제했지만, 처음 실행 때는 복제본을 디스크에 저장하지 않아 에디터를 닫으면 사라졌습니다(그래서 저장소에는 백업 파일이 없습니다). 원본이 필요하면 `FBX/M4/SM_M4Mag.fbx`를 다시 임포트하면 됩니다. 스크립트는 이제 백업을 디스크에 저장하도록 고쳤지만, 현재 에셋은 이미 편집된 상태이므로 다시 실행하려면 먼저 FBX를 다시 임포트해 원본으로 되돌린 뒤 실행해야 누적되지 않습니다.
- **확인:** 3인칭 왼쪽 옆 고해상도 캡처에서 리시버 옆에 튀어나온 회색 판이 사라졌습니다. 1인칭은 제 쪽에서 같은 각도로 캡처하지 못해 직접 확인하지 못했습니다. 재장전 중 손-탄창 정렬은 탄창 중심이 0.33cm 이동한 것 외에는 변하지 않습니다.

## M4 금속성 맞추기 + 탄창 기울기 점검 (2026-11-18)

- **금속성(`lyra_m4_metal_match.py`):** `M_Colt_Main`/`M_Colt_Furniture`/`M_Colt_Mag`/`M_Colt_Rear`의 Metallic 텍스처 값 t를 `Lerp(0.35, 0.55, t)`로 다시 매핑했습니다(노드 설명 `MetalMatch_Lerp`). 원래 총몸 약 0.9, 탄창 약 0.78, 개머리판·핸드가드 중앙값 약 0.54였던 것이 각각 약 0.54, 0.50, 0.45가 되어 서로 비슷해지고 전체가 어두워집니다. 되돌리려면 `py <파일> keep revert`(Lerp 0~1 = 원래 값). 인게임에서 눈으로 확인하지는 못했습니다.
- **탄창 기울기:** 측정으로는 기울기를 찾지 못했습니다. 탄창 컴포넌트는 소총 대비 회전 0°·이동 0이고(`lyra_mag_rest_probe.json`, 재장전 중에도 `mag_rot` 0), 메시 단면(`Data/mag_fit2.json`)의 앞뒤 중심선도 바닥에서 윗부분까지 약 0.1cm만 달라 수직입니다. 사용자가 본 어긋남이 어떤 상황(자세, 재장전 후, 시점)인지 확인이 필요합니다.
- **카메라 캡처 시도(`lyra_mag_cam.py`):** PIE 월드에는 액터 생성 API가 없어 기존 큐브를 임시 카메라로 쓰려 했지만 시점이 소총 옆으로 오지 않아 쓸 만한 이미지를 얻지 못했습니다(`Data/magcam_*.png`는 의미 없는 화면).

### 탄창 하부 시각화 (`lyra_mag_view.py`, 2026-11-18)

- 에디터 월드 높은 곳에 `SK_M4A1` + `SM_M4Mag`를 인게임과 같은 변환(회전 0, 이동 0)으로 세우고 엔진 머티리얼 그대로 여러 각도에서 찍었습니다(`Data/magview_*.png`, 모음 `magview_sheet.png`). 탄창 옆면은 수직이고 좌우 중심도 삽입구와 맞습니다.
- Blender로 잰 결과(`lip.py` 계열 측정): 삽입구 아래 테두리(총몸)는 앞쪽 z -2.97에서 뒤쪽 z -4.07로 약 8~9° 내려가고, 탄창 바닥도 앞 -7.1에서 뒤 -7.85로 약 8° 내려가 둘이 평행합니다. 즉 옆면은 수직인데 위·아래 경계만 8° 기운 평행사변형처럼 보이는 것이 모델 원래 모양입니다.
- `lyra_mag_level.py`로 탄창 바닥을 수평으로 펴 봤지만(약 3.8° 보정), 평행 관계를 깨뜨리는 것이라 `revert` 인자로 되돌렸습니다(백업 `/Game/Furina/Backups/SM_M4Mag_pre_level`은 디스크에 저장됨). 현재 메시는 `lyra_mag_fit_mesh.py` 적용 직후 상태입니다.

### 탄창 요(수직축) 회전 8.7° 수정 (`lyra_mag_unyaw.py`, 2026-11-18) — 실제 원인

- **원인:** 원본 `SM_M4Mag.fbx` 탄창이 수직축 둘레로 약 8.7° 돌아간 채 만들어져 있었습니다. 높이별 단면 PCA에서 모든 높이(-8 ~ 3cm)가 7.7~9.7° 돌아가 있고, 삽입구(총몸)는 좌우 대칭이었습니다. 옆에서 보면 티가 안 나고 아래나 비스듬히 보면 바닥판이 총과 어긋나 보입니다. 위에서 "기울기 못 찾음"이라고 적었던 것은 옆/앞/뒤 축 방향만 보고 회전축을 수직축으로 확인하지 않은 제 실수입니다. 이전의 "좌우 0.33cm 치우침"도 이 회전 때문이었습니다.
- **수정:** 디스크 백업 `/Game/Furina/Backups/SM_M4Mag_pre_level`(= `lyra_mag_fit_mesh.py` 적용본)에서 그 수정을 역산해 원본 정점을 복원하고(원본 x 범위 [-1.18, 1.84] 그대로 복원 확인), 탄창 중심 둘레로 -8.66° 돌린 뒤 위쪽 구간 좌우 중심을 x=0으로 맞췄습니다. 폭 0.8배 축소(`lyra_mag_fit_mesh.py`)는 더 이상 쓰지 않습니다. 결과: 높이별 남은 요 ±1° 이내, 삽입구 안 x 범위 [-1.1, 1.1](하우징 ±1.53 안쪽), 저장 True.
- **확인:** 에디터 월드 렌더(`lyra_mag_view.py`)의 아래쪽 시점에서 바닥판이 삽입구와 평행해졌습니다(`Data/magview_unyaw_compare.png`). PIE(실제 손에 든 상태)와 재장전 중 모습은 아직 보지 않았습니다.

### 오른손 권총손잡이 쥐기: 소총을 손에 대해 앞으로 7.3cm (`lyra_grip_shift.py`, `lyra_grip_shift_bp.py`, 2026-11-18)

- **측정:** 오른손 손가락 뿌리(`IndexFinger1_R`/`MiddleFinger1_R`)가 소총 기준 y≈-3.8(탄창 뒤·방아쇠 앞)에 있었고, 권총손잡이 앞면은 y≈-11.5(z -5.5, Blender로 SK_M4A1 단면 측정)라서 손이 손잡이보다 약 7.3cm 앞을 쥐고 있었습니다.
- **수정:** 소총을 오른손목 기준으로 총 앞방향 +7.3cm 옮겼습니다. 오른손은 제자리, 총이 앞으로 나가 손잡이가 손바닥에 들어옵니다. 왼손 목표(`LHandOff.A/B`, 총 기준 y 12.6 → 19.9)도 같이 7.3cm 앞으로 옮겨 총의 같은 자리를 잡습니다.
  - 소총 상대 위치는 BP 템플릿만이 아니라 권총↔소총 전환 노드가 매 틱 리터럴로 다시 넣고 있어서(`P2_MkVec_b425cf20` X, `P2_LitD_9e7e301`(Y), `P2_LitD_124d465`/`P2_LitD_200c0416`(Z)) 그 값도 바꿨습니다(-1.95/-10.60/-6.35 → -2.19/-17.90/-6.50).
  - 원래 값은 `Data/lyra_grip_shift_orig.json`. 되돌리려면 `lyra_grip_shift.py 0` → `lyra_grip_shift_bp.py`.
- **PIE 확인(`lyra_grip_probe.py`):** 오른손목이 소총 기준 y -18.1(손잡이 뒤), 손가락 뿌리 y -11.0~-12.2(손잡이 앞면)로 손잡이를 감쌉니다. 왼손목은 3인칭 y 3.0, 1인칭 y 12.6으로 변경 전과 같은 총 위치를 잡습니다. 왼팔은 37cm(어깨 당김 한계)로, 왼쪽 쇄골이 오른쪽보다 3인칭 2.2cm·1인칭 1.1cm 늘어나 있습니다(기존 어깨 당김 `LShOver`가 받는 중).
- 상체 비틀기는 사용자가 지금 대기 자세가 좋다고 해서 14°(오른쪽 어깨 앞) 그대로 두었습니다. `lyra_torso_twist.py`는 `Data/twist_deg.txt`가 있으면 그 각도를 씁니다(현재 파일 없음).

### 3인칭 사격 자세: 개머리판을 오른쪽 어깨에 (`lyra_fire_pose_fix.py`, 2026-11-18)

- **측정(`lyra_fire_pose_probe.py`, 잔탄 0에서 `FurinaRifleShot`을 반복 호출해 반동 없는 사격 자세 유지, 폰 로컬 x 앞/y 오른쪽/z 위):** 개머리판 끝이 (-0.2, 2.9, 26.9)로 몸 중심선 가슴 안쪽에 박혀 있었고, 오른쪽 어깨 관절(1.7, 9.1, 29.5)과 떨어져 있었습니다.
- **수정(사격 가중치 `FireWN = FireW × NotAim`에서만 동작, 대기·견착·정조준 자세는 그대로):**
  - 총 위치: `TpD2 = TpD + FIRE_D × FireWN` (`FIRE_D` = 조준 좌표 (1.6, 3.1, 0.6)cm).
  - 상체: `TwAng.B = rad(-14°) + rad(20°) × FireWN`. 사격 중에는 왼쪽 어깨 앞·오른쪽 어깨 뒤로 순 6° 비틉니다. 대기 자세는 기존 14°(오른쪽 어깨 앞) 그대로입니다.
  - 값은 `Data/fire_pose_fix.json`(`{"d":[x,y,z],"tw":deg}`)으로 바꾸고 스크립트를 다시 돌리면 됩니다.
- **결과:** 개머리판 끝 (3.5, 7.9, 27.4)으로 오른쪽 어깨 관절(-1.6, 9.9, 29.5)의 앞 5cm·안쪽 2cm·아래 2cm, 즉 어깨 앞면에 닿습니다. 왼쪽 쇄골 늘어남은 1cm 이하(9.8 vs 오른쪽 8.9cm)입니다. 옆모습 비교: `Data/fire_pose_compare.png`.
- **미확인:** 연사 반동(`RifleKick`) 중 모습, 걷거나 앉은 상태의 사격 자세는 따로 보지 않았습니다.

### 3인칭 왼팔: 늘리지 않고 어깨를 기울이기 + 고개 들기/내리기에 개머리판 고정 (`lyra_left_clav_reach.py`, `lyra_butt_pivot.py`, 2026-11-18)

- **문제:** 위를 보며 쏠 때 왼팔이 너무 길어 보였습니다. 원인은 두 가지였습니다.
  1. 왼손이 총에 안 닿으면 CR이 왼쪽 어깨 관절(`Left-arm`)을 목표 쪽으로 평행이동(`LShSet`)해서, 쇄골이 늘어나 팔이 길어 보였습니다.
  2. 총이 눈 위치를 축으로 피치 회전해서, 위로 35° 보면 개머리판이 어깨 앞 5cm → 16cm로 밀려나고 왼손 목표도 같이 멀어졌습니다.
- **수정 1 (`lyra_left_clav_reach.py`):** `LShSet` 가중치를 0으로 끄고, 같은 목표를 향해 `Left-shoulder`(쇄골)를 뿌리 기준으로 회전시키는 노드(`ClXf`…`ClSet`, 실행 순서 `LShSet → ClSet → RLArmIK`)를 넣었습니다. 쇄골 길이는 그대로이고 어깨가 앞/위로 기울어집니다. 매 프레임 왼손 목표로 계산하므로 조준 피치에 실시간으로 따라갑니다. `GAIN` 2.6, 최대 45°. 되돌리기: `py lyra_left_clav_reach.py revert`.
- **수정 2 (`lyra_butt_pivot.py`):** 3인칭(`TpW`)에서 `GPos`에 `(I − AimQ)·(GOffB + 개머리판)`을 더한 `GPos2`를 써서, 피치를 바꿔도 개머리판이 어깨에 머물고 총이 개머리판을 축으로 돕니다. 1인칭·정조준 조준선은 그대로입니다. 되돌리기: `py lyra_butt_pivot.py revert`.
- **측정(사격 자세, `lyra_fire_pose_probe.py <태그에 up/down>`):**
  - 위 35°: 개머리판 (1.3, 7.9, 29.7), 어깨 관절 바로 앞. 왼손목이 총 기준 (3.2, 3.0, 2.0)으로 정확히 잡는 자리. 쇄골 8.9cm(늘어나지 않음). 비교: `Data/aim_up_compare.png`.
  - 아래 30°: 개머리판 (5.2, 7.9, 24.8). 왼손은 팔이 다 펴져서 잡는 자리보다 핸드가드를 따라 약 4.9cm 뒤를 잡습니다(옆으로 1.4cm). 쇄골은 늘어나지 않습니다.

### 1인칭 재장전 손-탄창 + 1인칭 팔꿈치 흔들림 (`lyra_fp_reload_sway.py`, 2026-11-18)

- **재장전 측정(`lyra_reload_mag_probe.py fp`, 총 기준 X왼쪽/Y앞/Z위):** 1인칭에서 탄창을 쥐는 순간(MagState 0.5) 손바닥 중심이 탄창 중심에서 (+9.5, +2.3, -4.2)cm, 즉 탄창 왼쪽 허공에 있었습니다. 탄창은 쥐는 순간 위치 그대로 손에 붙기 때문에(KeepWorld) 뽑기·끼우기 내내 손에서 떨어져 보였습니다. 3인칭 보정(`RlDelta`, × `TpW`)은 1인칭에 적용되지 않았습니다.
- **수정:** 1인칭 전용 `RlDeltaFp = (-6.0, -2.3, +1.5) × RlEnv × (1 − TpW)`를 왼손 목표에 더합니다(`RLV3 = RLV2 + RlDeltaFp → LHandOff3.B`).
- **결과:** 쥐는 순간 손바닥이 탄창 중심에서 (+3.5, 0.0, -2.6), 즉 탄창 왼쪽 면 아래쪽을 쥐고, 뽑기~끼우기 동안 그대로 유지됩니다. 놓는 순간 탄창이 장착 위치보다 약 1.6cm 높아서 그만큼 제자리로 붙습니다(수정 전에도 비슷했습니다).
- **팔꿈치 흔들림:** 양팔 IK 폴 벡터에 느린 사인파(`SwT`/`SwS1`/`SwS2`, 크기 `SwAmp.B` 0.15, 가중치 1 − `ViewTP` 커브 = 1인칭에서만)를 더했습니다. 측정(`lyra_sway_probe.py`, 8초): 오른 팔꿈치 1.5cm, 왼 팔꿈치 1.0cm 움직이고 오른손은 0cm로 고정입니다. 왼손은 핸드가드를 따라 0.9cm 미끄러집니다(왼팔이 거의 다 펴진 상태라 팔꿈치 방향이 바뀌면 도달 거리가 조금 달라짐).

### 1인칭 재장전: 탄창 바닥을 잡고 축 방향으로 곧게 뽑기/끼우기 (`lyra_fp_mag_base_grab.py` ~ `grab7.py`, 2026-11-18)

- **문제:** 1인칭 재장전에서 탄창을 옆면으로 잡고, 아래로 빼면서 동시에 왼쪽으로 4~6cm 움직여 탄창 윗부분이 삽입구 안에 있는 동안 옆벽을 뚫고 나왔습니다(끼울 때도 옆에서 들어옴).
- **수정(모두 1인칭 가중치 `RlFpW`에서만, 3인칭은 그대로):**
  1. 손 방향: 재장전 중 왼손 회전에 총 앞축 90°를 더해 손바닥을 위로(`RlRotA/RlRotQ0/RlRotQ → RLHRot.B`).
  2. 잡는 위치: `RlDeltaFp`를 (-9.55, -2.3, -2.95)로 해서 손바닥이 탄창 바닥판 바로 아래(약 0.9cm)에 오게. 잡는 자리 `P_G` = 총 기준점 좌표 (0.42, 1.9, -9.33).
  3. 붙는 순간 고정: MagState 0.02~0.98(쥐는 중/놓는 중)에는 왼손 목표를 `P_G`에 고정하고, 바로 켜지고 천천히 꺼지게(`RgWin/RgWinS/RgWinM/RgW/RgFrz`). 탄창이 설계한 간격(손바닥-탄창 중심 6.2cm)으로 붙습니다.
  4. 부드럽게: `RgSm`(AccumulateVectorLerp, Blend 30).
  5. 곧게 빼기: 높이는 원래 경로를 따르고, 옆 이동을 내려온 거리로 제한합니다. 9cm(탄창이 삽입구를 다 빠지는 거리) 내려오기 전에는 축에서 0.15cm 이상 못 벗어나고, 그 뒤 8cm 동안 옆으로 따라갑니다(`RcDesc/RcRlim/RcSc/RcXY/RcP2`). 이 제한은 붙은 뒤부터 놓을 때까지 켜집니다(`RcStep/RcStepS/RcHold3`, 쥐는 순간에는 고정 목표 기준 거리 `RcRmix`).
  - 중간 시도(높이를 강제로 누르기)는 탄창이 한 프레임에 10cm 떨어지거나 붙기 전에 손이 내려가 버려서 위 방식으로 바꿨습니다(`grab2`~`grab6` 노드 일부는 연결이 끊긴 채 남아 있음).
- **측정(`lyra_reload_mag_probe.py fp`, 슬로모 0.15):** 탄창 윗부분이 삽입구 안에 있는 동안 축에서 0.43cm(삽입구 여유) 넘게 벗어난 샘플 0개. 탄창이 장착 위치보다 위로 올라간 샘플 0개. 뽑을 때 (0.28, -2.0) 축을 따라 -2.5 → -10.6cm로 곧게 내려간 뒤 옆으로 갑니다. 끼울 때는 아래에서 축을 맞춘 뒤 올라가 장착 위치 (-0.07, -1.93, -2.23)에서 끝납니다.
- **미확인:** 1인칭 화면으로 직접 보지는 않았습니다(숫자로만 확인). 손바닥을 위로 돌린 손 모양이 자연스러운지는 화면으로 확인이 필요합니다.

### 1인칭 재장전: 손바닥으로 탄창 바닥 받치기 + 손가락 모양 (`lyra_fp_reload_palm.py`, 2026-11-18)

- **측정(`lyra_reload_mag_probe.py fp`, 손바닥 법선 = cross(손가락 방향, 검지-소지)):** 쥐는 동안 손바닥이 총 기준 (0.75, -0.08, 0.66), 즉 위에서 49° 왼쪽으로 누워 있어 손 옆면이 탄창 바닥에 닿았습니다(이전 수정의 손목 회전 +90°가 과했음). 손가락은 재장전 애니메이션 값 그대로라 2번 관절 굽힘이 검지 39° / 중지 39° / 약지 59° / **소지 104°**로 소지가 꺾여 있었습니다.
- **수정(1인칭 재장전 중에만, 가중치 `RlEnvFp`):**
  1. 손목 회전 `RlRotA.B` 90° → 41.3° (손바닥 법선이 정확히 위를 향하는 값).
  2. 손가락 IK(`FgIndexIK`~`FgLittleIK`, 실행 순서 `RLArmIK →` 4개 `→ Fing_IndexFinger1_L…`): 검지·중지·약지·소지를 손바닥 앞방향으로 펴고 손바닥 쪽으로 18/20/22/26°만 굽힙니다(3번 관절은 2배 굽힘). 목표는 `1번 관절 + u·L1 + (u를 n쪽으로 θ 굽힌 방향)·L2`이고 `u`, `n`은 총 회전(`GRotR`)에서 구한 서로 수직인 단위벡터입니다(처음에 수직이 아니어서 목표가 팔 길이를 넘어 손가락이 쭉 펴졌던 것을 고쳤습니다). 값은 `Data/fp_reload_palm.json`으로 바꿉니다. 엄지는 애니메이션 그대로입니다.
- **측정 결과:** 쥐는 동안 손바닥 법선 (0.0, -0.08, 1.0)(정확히 위), 2번 관절 굽힘 18.1 / 20.1 / 21.9 / 26.3°, 손바닥 중심이 탄창 바닥판보다 0.9cm 아래, 손가락 끝은 총 앞쪽 y 3.4~6.2cm. 탄창이 삽입구 안에서 벽 여유(0.43cm)를 넘은 샘플은 0개로 이전과 같습니다. 대기 자세 손가락(40/58/52/32°)은 그대로입니다.
- **미확인:** 화면으로 손 모양을 직접 확인하지는 못했습니다. 1인칭 카메라를 아래로 숙여 찍어도 재장전 손이 총 몸체에 가려 보이지 않았습니다. 손가락 모양이 자연스러운지는 직접 확인이 필요하고, 굽힘 각도는 `fp_reload_palm.json`의 `bend`, 손바닥 기울기는 `rot_deg`로 조정합니다.

### 모든 스테이지에 푸리나 메커니즘 적용 + 키 중복은 푸리나 우선 (`lyra_all_stages_furina.py`, `lyra_furina_key_priority.py`, 2026-11-18)

- **상황:** 사람 플레이어 폰은 `B_LyraGameMode`의 `GetDefaultPawnClassForController` 오버라이드 때문에 이미 모든 맵에서 푸리나입니다. 하지만 스테이지마다 경험(Experience)이 Lyra 마네킹용 PawnData(`HeroData_ShooterGame` 등)와 무기용 액션 세트(퀵바·HUD·공용 입력)를 그대로 쓰고 있었고, 푸리나 전용 설정은 PIE 경험 오버라이드(`B_Furina_Experience`)로만 적용되고 있었습니다.
- **수정(`lyra_all_stages_furina.py`):** 각 스테이지 경험의 `DefaultPawnData`를 `HeroData_Furina`로 바꾸고, 액션 세트에서 `LAS_ShooterGame_StandardComponents`, `LAS_ShooterGame_StandardHUD`, `LAS_ShooterGame_SharedInput`(Lyra 공용 입력 = 키 중복의 원인), `LAS_InventoryTest`를 뺐습니다(`B_Furina_Experience`와 같은 방식). 대상:

| 경험 | 쓰는 스테이지 |
|---|---|
| `B_ShooterGame_Elimination` | `L_Expanse` |
| `B_LyraShooterGame_ControlPoints` | `L_Convolution_Blockout`, `L_ShooterGym` |
| `B_ShooterGame_Perf` | `L_ShooterPerf` |
| `B_TestInventoryExperience` | Explorer 테스트 맵 3개 |
| `B_LyraDefaultExperience` | `L_DefaultEditorOverview` |
| `B_TopDownArenaExperience`, `B_TopDownArena_Multiplayer_Experience` | Exploder 2종 |

  `B_LyraFrontEnd_Experience`(메뉴, 폰 없음)는 제외했습니다. 원래 값은 `Data/lyra_all_stages_orig.json`이고 `py lyra_all_stages_furina.py revert`로 되돌립니다. 봇(마네킹)은 이전처럼 무기 없이 서 있습니다.
- **키 중복은 푸리나 우선(`lyra_furina_key_priority.py`):**
  1. 푸리나 IMC(`Default_IMC`, `IMC_FurinaStance`) 우선순위를 0/100 → 1000/1100으로 올렸습니다(폰의 `LyraHeroComponent` DefaultInputMappings와 EventGraph `AddMappingContext` 노드 둘 다).
  2. 푸리나가 쓰는 키를 같이 쓰는 Lyra IMC(`IMC_Default`, `IMC_ADS_Speed`, `IMC_ShooterGame`, `IMC_ShooterGame_KBM`, `IMC_InventoryTest`)의 입력 액션을 `consume_input=False`로 바꿨습니다. 이번에 바뀐 것: `IA_Move`, `IA_Jump`, `IA_Crouch`, `IA_Look_Mouse`, `IA_Look_Stick`, `IA_Interact`.
  3. 위 1에서 `SharedInput`이 빠져 `IMC_ShooterGame` 등은 스테이지에서 더 이상 추가되지 않습니다.
- **스테이지 순회 확인(`lyra_stage_sweep.py`, 맵을 열고 그 스테이지의 실제 경험으로 PIE → 점검 → 종료 자동 반복):** 8개 스테이지(`L_DefaultEditorOverview`, `L_ShooterGym`, `L_ShooterPerf`, `L_Convolution_Blockout`, `L_Expanse_Blockout`, `L_InventoryTestMap`, `L_TopDownArenaGym`, `L_TopDown_LocalMultiplayer`) 모두 플레이어 폰이 푸리나, 체력 100/100, 소총·탄창 컴포넌트 있음, 사격 이벤트로 잔탄 20 → 19. 슈터 맵의 봇은 마네킹 3~11명으로 나옵니다.
- **입력 확인(`lyra_input_probe.py`, 키 입력 직접):** `B_ShooterGame_Elimination` 경험에서 W로 이동(속도 120), 좌클릭 유지로 연사(20 → 6), R로 재장전(잔탄 20, 예비 600 → 586). 다른 스테이지의 키 입력은 사격 이벤트 호출까지만 보았습니다(`L_Expanse`, `L_FiringRange_WP` 본 맵은 열지 않았고 Blockout 맵과 같은 경험으로 확인).
- **PIE 경험 오버라이드**는 확인 뒤 `B_Furina_Experience`로 되돌렸습니다(`lyra_set_experience_override.py <이름|none>`으로 바꿀 수 있음). `Config`의 값은 건드리지 않았습니다.

## 메인 화면 포탈로 스테이지에 들어가면 마우스로 시점이 안 돌아가던 문제 (2026-11-18)

- **재현(`lyra_look_probe.py`, 마지막 인자 `portal`):** PIE에서 `B_TeleportToUserFacingExperience` 위치로 폰을 옮겨 포탈을 작동시키면(Convolution으로 이동) 마우스를 움직여도 컨트롤 회전이 그대로였습니다. 콘솔 `ServerTravel`로 같은 맵에 가면 정상이라 포탈에만 있는 문제입니다. 포탈 없이 직접 시작한 Elimination, 기본 오버뷰, TopDownArena는 마우스 회전과 우클릭 정조준이 정상이었습니다(`Data/lyra_look_probe.json`).
- **원인(`Saved/Logs`):** 포탈이 메뉴 레이어에 `W_NonInteractiveSpinner`를 띄울 때 CommonUI가 입력 모드를 Menu로 바꿉니다(뷰포트 마우스 캡처 없음, 커서 표시). 새 스테이지에서 게임 입력으로 되돌리는 곳이 없었습니다. 로그에 `Menu`, `NoCapture`, `bShowMouseCursor False -> True`만 있고 다시 `Game`으로 바뀌는 줄이 없었습니다.
- **시도했다가 되돌린 것(`lyra_stage_layout_fix.py`):** `LAS_ShooterGame_StandardHUD`의 `W_ShooterHUDLayout` 레이아웃 요청을 경험 5개에 복사했지만 레이아웃이 올라오지 않아 효과가 없었고, `/Game` 경험이 플러그인 콘텐츠를 참조한다는 에셋 검사 오류만 늘었습니다. `revert`로 모두 비웠습니다.
- **수정(`lyra_portal_input_fix.py`):** `ThirdPersonCharacter_BP`의 `ReceiveControllerChanged` 끝에 `GetPlayerController(0)` → `SetInputMode_GameOnly` → `bShowMouseCursor = false`를 넣었습니다(노드 `FPN_PIGet`, `FPN_PIGame`, `FPN_PICursor`). 플레이어가 폰을 잡을 때 게임 입력으로 복구합니다.
- **확인:** 같은 포탈 경로에서 로그에 `NoCapture -> CapturePermanently`, `bShowMouseCursor True -> False`가 폰을 잡은 직후에 찍혔고, 마우스를 움직이자 컨트롤 yaw가 바뀌었습니다. 포탈 중 Convolution(ControlPoints) 한 곳만 확인했습니다.

## 비조준·견착 사격 시 한 발당 화면 흔들림 (2026-11-18)

- **에셋(`lyra_fire_shake.py`, 갱신은 `lyra_shake_asset.py [강도]`):** `/Game/Furina/CameraShakes/CS_FurinaShot`(CameraShakeBase 블루프린트, `WaveOscillatorCameraShakePattern`). 길이 0.18초(들어오기 0.015, 나가기 0.12), 회전 진동 피치 0.55° 34Hz, 요 0.40° 27Hz, 롤 0.50° 31Hz. 위치 흔들림은 끄고(`location_amplitude_multiplier` 0) 회전만 씁니다. 강도 인자는 진폭 배율(기본 1.0, 0이면 흔들림 없음).
- **그래프:** `ThirdPersonCharacter_BP`의 `FurinaRifleShot` 체인에서 `M4_SetFurinaAmmo`(발사가 성립해 탄약이 줄어든 직후) 다음에 `NOT FurinaADS.IsActive` 분기(`FPN_ShkNot`, `FPN_ShkBr`)를 넣고, 참이면 `PlayerCameraManager.StartCameraShake`(`FPN_ShkStart`, 스케일 1.0)를 호출합니다. 정조준 중에는 흔들지 않고 비조준과 견착에서는 흔듭니다. 총이 M4든 P220이든 같은 위치를 지나므로 둘 다 흔들립니다.
- **한 번 틀렸던 점:** `new_object`로 만든 패턴은 `rotation_amplitude_multiplier`가 0이라 처음에는 흔들림이 0이었습니다(`lyra_shake_ref_dump.py`로 번들 셰이크와 비교해 발견). 1.0으로 올리고 위치 진폭 배율을 0으로 했습니다.
- **PIE 측정(`lyra_shake_pie_probe.py`, 오버뷰 맵, 발사 후 0.7초간 카메라 회전 − 컨트롤 회전의 최대 절대값, 피치/요/롤):** 비조준 0.55°/0.19°/0.48°, 견착 0.49°/0.38°/0.48°, 정조준 0/0/0. 발사 이벤트를 직접 호출해 측정했고(마우스 클릭 사격은 자동화로 못 넣음), 발당 값은 시작 위상이 무작위라 매번 조금 다릅니다. 눈으로 보지는 못했습니다.

## 분석: Downloads/fps-animated-carbine (긴급 재장전 레퍼런스, 2026-11-19)

- **파일:** `source/arms@carbine.fbx`(Cinema 4D에서 내보낸 팔+카라빈, 텍스처 11장). 30fps, 프레임 0~222(7.4초) 한 줄 타임라인에 동작 여러 개가 이어져 있고 마커는 없습니다. 팔 리그 `Null`(뼈 48개: `L_arm`/`R_arm`, 팔꿈치, 손목, 손가락, 폴 타깃 2개)과 부품 객체(`clip`, `bolt`, `handle`, `boltcatch`, `release`, `lid`, `trigger`)가 각각 애니메이션을 가집니다. 도구: `Scripts/Blender/inspect_carbine_fbx.py`, `sample_carbine_anim.py`, `render_carbine_frames.py`(결과 `Data/carbine_fbx_inspect.json`, `carbine_anim_samples.json`, `Scratch/carbine_sheet_*_side.png`). 거리 단위는 총 길이를 약 74cm로 가정한 참고 환산이라 정확하지 않습니다.
- **구간 분해(부품 움직임과 옆면 렌더로 확인):**
  - 0~8 대기, 8~20 총 올림.
  - **20~64 긴급(빈 탄창) 재장전:** 노리쇠가 뒤에 걸려 있다가(프레임 22~24에 노리쇠가 뒤로 이동, 이후 52까지 유지) 왼손이 탄창을 아래로 뽑고(24~32, 총 기준 약 28cm), 새 탄창을 들고(34) 삽입(36~46), 왼손이 총 위로 넘어가 노리쇠 멈치를 치고(50~54) 노리쇠가 앞으로 돌아옵니다(54~56). 왼손이 손잡이로 복귀(58~64). 오른손은 권총손잡이에 고정입니다(손목이 약 0.01cm 움직임).
  - **70~110 전술(탄창 남은) 재장전:** 같은 탄창 교체 동작(뽑기 84~92, 삽입 96~104)이고 노리쇠는 앞에 있는 채로 유지됩니다. 마지막에 손잡이로 복귀.
  - 110~126 장전손잡이 당김(약 16프레임), 132~148 큰 회전 동작(점검/기타로 추정, 눈으로 확인하지 않음), 156~168 장전손잡이 한 번 더, 176~204 대기 호흡, 204~222 큰 회전 후 안정(꺼내기로 추정).
- **한계:** 라이선스 문서는 폴더에 없습니다. 모션을 이 프로젝트에 반영하기 전에 출처의 이용 조건을 확인해야 합니다. 반영은 하지 않았습니다.

## 긴급(빈 탄창) 재장전 + 노리쇠 후퇴 + 총 모델 개조 (2026-11-19)

- **모델 개조(`Scripts/Blender/build_colt_rifle_bolt.py`):** Colt 본체 메시는 내부 부품까지 모델링돼 있습니다(`analyze_colt_parts.py`/`render_colt_parts.py`로 연결 성분을 색으로 구분해 확인). 노리쇠 캐리어(1,038면)와 그 안쪽 부품(100면) 성분을 찾아 `SM_M4Bolt`(정적 메시, 원점 = 소총 원점이라 장착 위치 항등)로 분리하고, `SK_M4A1`에서는 뺐습니다(본체 정점 32,370 → 31,797). 총 길이 80cm와 변환은 이전 `build_colt_rifle_hq.py`와 같습니다. 이전 FBX는 `Backups_bolt/`, 이전 `SK_M4A1`은 `/Game/Furina/Backups/SK_M4A1_pre_bolt`에 있습니다. 가져오기: `lyra_bolt_import.py`. Blender 렌더(`check_bolt_split.py`)에서 노리쇠를 뒤로 7cm 옮기면 배출구에서 뒤로 빠지는 것을 확인했습니다.
- **애니메이션 분석(`fps-animated-carbine/source/arms@carbine.fbx`):** 프레임 9~69(30fps, 60프레임 간격 = 2.0초)를 리샘플 없이 1:1로 씁니다(`sample_carbine_anim.py`로 프레임별 추출 → `Scripts/Tools/build_empty_reload_curves.py` → `Data/empty_reload_curves.json`). 왼손목의 총 기준 이동만 가져오고(손목 회전, 손가락, 총의 기울기는 가져오지 않음) 푸리나에 맞춰 SC 0.973배, 탄창을 쥐는 순간의 변위를 기존 재장전의 잡기 값과 맞추는 보정(`CORR`)을 더했습니다. 노리쇠는 푸리나에서는 처음부터 뒤에 걸려 있으므로 원본에서 노리쇠가 뒤로 가는 프레임(22~24)은 쓰지 않고, 멈치를 치는 52~56에서 `BoltBack` 1 → 0으로 풀립니다.
  - 이벤트(초): 탄창 쥠 0.47, 낙하 0.73, 새 탄창 0.83, 장착 1.23, 노리쇠 멈치 1.43~1.57, 복귀 1.9~2.0.
- **애니메이션 자산(`lyra_empty_reload_apply.py`, `lyra_empty_reload_len.py`):** `AS_Furina_FP_ReloadEmpty`/`AM_Furina_FP_ReloadEmpty`(기존 재장전 자산의 복제, 뼈 애니메이션은 그대로 쓰고 CR이 손을 곡선으로 덮어씀). 곡선 `ReloadLX/LY/LZ`, `MagState`, 새 곡선 `BoltBack`을 넣고 몽타주 구간을 2.0초로 잘랐으며 `RifleReload` 곡선도 2.0초에 끝납니다. 몽타주 길이 속성은 파이썬으로 못 바꿔 3.13초로 표시되지만 구간이 2.0초라 PIE에서 재장전이 2.0초에 끝났습니다.
- **블루프린트(`lyra_bolt_graph.py`, 노드 `FBX_*`, `FBT_*`):**
  - 컴포넌트 `FurinaBolt`(부모 `FurinaRifle`), 실수 변수 `FurinaBoltKick`·`FurinaBoltHold`.
  - `FurinaMagUpdate`(0.016초 타이머) 맨 앞: 걸림 목표(재장전 중이면 `BoltBack` 곡선, 아니면 잔탄 0이면 1) → `FInterpTo` 속도 35, 위치 = max(걸림, sin(π(1−발사 킥))) × −7cm. 한 발마다 `FurinaBoltKick`이 1로 올라가 약 0.06초 동안 뒤로 갔다 돌아오고, 잔탄이 0이 되면 뒤에 걸립니다. 권총 장착 중에는 숨깁니다.
  - `FurinaRifleShot`의 `M4_SetFurinaAmmo` 바로 뒤에서 킥을 올립니다(카메라 셰이크 분기보다 앞).
  - 재장전 요청: 소총이고 잔탄 0이면 `AM_Furina_FP_ReloadEmpty`와 타이머 2.0초, 아니면 기존(3.0초).
- **PIE 측정(`lyra_empty_reload_probe.py`, 발사/재장전 이벤트 호출, 슬로모 0.15):** 단발 5발에서 노리쇠 상대 Y가 0 → −6.96cm → 0으로 왕복, 잔탄 0에서 −7.0으로 걸림. 긴급 재장전은 `MagState` 0 → 1(0.49) → 2(0.73) → 1(0.84) → 0(1.23), `BoltBack` 1 → 0(1.5~1.7)으로 노리쇠가 풀리고 2.0초 직후 잔탄 20. 잔탄이 남은 재장전은 3.0초이고 노리쇠는 움직이지 않습니다. 옆면 캡처(`Data/empty_reload_side*`)에서 왼손이 탄창 → 아래 → 새 탄창 → 총 위로 오는 것과 배출구 안 캐리어가 걸림 상태와 전진 상태에서 다른 것을 확인했습니다.
- **미확인:** 1인칭 화면(손이 총에 가려 보임), 총을 바꿀 때(권총 장착 중 노리쇠 숨김), 달리기·앉기 중 긴급 재장전, 1인칭 탄창 잡기 보정 노드(grab 계열)가 새 곡선에서도 벽을 뚫지 않는지는 수치로 확인하지 않았습니다. 왼손 회전과 손가락은 원본을 가져오지 않아 노리쇠 멈치를 칠 때 손 모양은 기존 재장전 값 그대로입니다.
- **에디터 크래시 원인과 재발 방지:** 블루프린트 편집 스크립트가 에디터를 여러 번 죽였습니다. 로그로 확인한 원인은 지운 노드와 같은 이름으로 새 노드의 `rename`을 하면 `Renaming an object on top of an existing object`로 치명 오류가 나는 것이었습니다(지운 노드가 GC되기 전까지 이름이 남음). 또 `get_basic_type_by_name('float')`은 정수 변수를 만들어 노드가 정수로 굳었습니다(`'real'`을 써야 함). 스크립트가 파이썬 전역에 블루프린트/노드 객체를 남겨 두면 이후 GC에서 죽는 문제도 있어 스크립트 끝에서 전역을 비웁니다. 규칙: 노드를 지웠다면 새 이름 접두사를 쓸 것(`FBT_` → `FBX_`).

## 긴급 재장전에 피카티니 레일 뒤쪽 장전손잡이 당기기 추가 (2026-11-19)

- **증상:** 긴급 재장전이 노리쇠 멈치 치기로 끝나고 장전손잡이는 당기지 않았습니다. 1인칭에서는 손이 래치에 닿지도 않았습니다(PIE 측정: 검지 끝이 래치보다 앞 8cm, 아래 4cm).
- **모델(`build_colt_rifle_bolt.py`):** 장전손잡이(844면, 길이 16.4cm, 뒤쪽 끝 T 래치)를 본체에서 빼서 `SM_M4Handle`로 분리했습니다(렌더로 확인: `render_colt_parts.py -- <성분번호...>`). 본체 정점 31,797 → 31,373. 이전 상태는 `Backups_bolt/SK_M4A1_bolt_only.fbx`, `/Game/Furina/Backups/SK_M4A1_pre_handle`.
- **곡선(`Scripts/Tools/build_empty_reload_curves_v2.py`, v1은 `Data/empty_reload_curves_v1.json`):** 프레임 0~36은 v1과 같고(탄창 뽑기/교체/삽입, 장착 k37 = 1.23초), 37~45에서 장착 자세 → 장전손잡이 잡는 자세 `W_G = (6.5, -22.3, 4.9)`(검지 끝이 래치 왼쪽 윗면에 오도록), 45~47 당김(`HandleBack` 0 → 1, 손도 5.9cm 뒤로), 47~51 유지, 52 놓음(`HandleBack` 1 → 0.4, `BoltBack` 1 → 0.35), 53 완전히 앞으로, 53~60 손이 기본 위치로 복귀합니다. 이동 경로의 곡선 성분은 원본 FBX f105~115 의 왼손목 경로를 따르고, 시각은 원본 장전손잡이 구간(f114~124)에서 가져왔습니다. 손목 목표 → 곡선 변위는 `변위 = 목표 - (-1.91, 9.83, 4.28)`(PIE 측정 회귀, rms 0.14~0.40cm).
- **블루프린트(`lyra_handle_graph.py comp` / `tick`):** 컴포넌트 `FurinaHandle`(부모 `FurinaRifle`), `FurinaMagUpdate` 틱 끝에 `HandleBack` × −5.9cm 를 상대 Y 로, 권총 장착 중에는 숨김(노드 `FBH_*`). 곡선 `HandleBack`/`HandleFp`는 `lyra_empty_reload_apply.py`로 `AS/AM_Furina_FP_ReloadEmpty`에 들어 있습니다.
- **1인칭 어긋남의 원인과 수정(`lyra_cr_add_curve.py`, `lyra_fp_handle_fade.py`, `lyra_fp_handle_offset.py`):** 1인칭에서는 재장전 중 `RlEnvFp`가 왼손 목표에 탄창 바닥 잡기용 상수 오프셋(`RlDeltaFp`)을 더하고 손을 손바닥이 위로 오게 돌립니다. 이것이 손잡이 구간에서 손목을 (−4.5, +3.9, −5.3)cm 어긋나게 했습니다. 곡선 `HandleFp`(손잡이 구간에서 1)를 읽어 `RlEnvFp.B`를 `RlFpW × (1 − HandleFp)`로 바꿔 그 구간의 1인칭 탄창 보정을 껐습니다(노드 `RlHC`, `RlHInv`, `RlFpW2`). 이때 컨트롤 릭의 `GetCurveValue`는 릭 계층에 등록된 곡선만 읽으므로 `HandleFp`를 릭 곡선으로 등록해야 했습니다(처음에는 등록 안 해서 효과가 없었음). 보정을 끈 뒤에도 남는 (+4.3, +4.2, −2.4)cm 는 손잡이 구간에만 1인칭 가중치로 (−4.3, −4.2, +2.4)를 더해 맞췄습니다(`RlEnvH`, `RlEnvFpH`, `RlDeltaFpH`, `RLV4`).
- **PIE 측정(`lyra_empty_reload_probe.py`, 이벤트 호출):** 1인칭 당김 구간 왼손목 (6.7, −27~−28.5, 4.8~4.9), 검지 끝 (2.7~3.0, −20~−21.3, 7.0)으로 래치(x ±2.5, 뒤쪽 끝 −21.6, 윗면 z 6.4) 위에 닿고 3인칭 값과 같습니다. `FurinaHandle` 상대 Y 0 → −5.9 → 0, 노리쇠 −7.0 → 약 0(걸림이 손잡이 놓는 시점에 풀림), 완료 후 잔탄 20, 일반 재장전은 3.0초.
- **캡처:** 3인칭 옆면(`Data/empty_reload_hL2_*`)에서 손이 총 뒤쪽 위(뒤가늠자 뒤, 완충관 위)로 올라가 당기는 것을 봤습니다. 1인칭(`Data/empty_reload_hFP5_*`)에서는 손을 뻗어 총 뒤쪽 위에서 잡는 것까지 화면에 보이고, 당긴 상태(래치가 뒤로 5.9cm)에서는 손과 손잡이가 카메라 뒤로 넘어가 화면에서 사라집니다(카메라가 총 바로 뒤에 있음).
- **미확인:** 손바닥·손가락 모양은 이 구간에서 기본 손 모양 그대로라 래치를 잡는 모양이 아닙니다. 달리기·앉기 중 긴급 재장전, 권총 교체 중 손잡이 숨김은 확인하지 않았습니다.
- **에디터 크래시 규칙(추가):** 블루프린트를 편집하는 스크립트는 에디터를 새로 시작할 때마다 한 번만 돌립니다. 같은 세션에서 두 번째로 돌리면 파이썬 노드 래퍼가 정리되면서 에디터가 죽는 경우가 반복됐습니다(컨트롤 릭/애니메이션 에셋 스크립트는 연속으로 돌려도 문제없었음).

## 엄지 까딱 수정, 1인칭 총 앞으로, 전술 재장전 되돌림, HUD 재장전 시간 (2026-11-19)

- **전술(잔탄 있음) 재장전은 옛 방식으로 되돌림:** 처음에는 전술 재장전에도 장전손잡이 당기기를 넣어 3.69초로 늘렸다가(`build_tactical_reload_curves.py`, `lyra_tactical_reload_apply.py`, `lyra_tactical_bp.py`) "잔탄이 있으면 손잡이를 안 당기는 옛 전술 재장전을 쓰고 긴급 재장전은 잔탄 0일 때만"이라는 요청으로 되돌렸습니다(`lyra_tactical_revert.py`: `AS/AM_Furina_FP_Reload` 곡선을 `reload_curves_new.json` 원본과 `RifleReload` [0,0.35:1,2.6:1,3.0:0]으로, 손잡이 곡선 3개는 삭제 / `lyra_tactical_bp.py revert`: 재생 속도 1.0, 타이머 3.0초). 손잡이 당기는 전술 곡선은 `Data/tactical_reload_curves.json`, 이전 자산 사본은 `/Game/Furina/Backups/*_pre_tactical`에 있습니다. 긴급 재장전 분기는 `FurinaAmmo <= 0`이고 권총이 아닐 때만입니다.
  - PIE 측정(`lyra_empty_reload_probe.py`): 잔탄 17 → 재장전 3.0초, `FurinaHandle`·`FurinaBolt` 이동 0. 잔탄 0 → 2.0초, 노리쇠 −7.0cm 걸림 후 손잡이 당김.
- **엄지 까딱(`lyra_thumb_probe.py`, `lyra_thumb_hold.py`):** 손목 기준 엄지 방향을 재장전 구간에서 쟀더니, 템플릿 재장전 애니메이션이 탄창 장착 직후(2.3~2.5초) 엄지를 손목 기준 최대 58° 돌렸다가 0.06초 만에 평상시 자세로 45° 끊어 되돌렸습니다(그 뒤 2.54초부터는 고정). CR은 엄지를 건드리지 않았습니다. 수정: 재장전 중(가중치 `ReloadSm`) `Thumb0/1/2_L`의 로컬 회전을 평상시 값(`Data/thumb_rest.json`, PIE에서 읽은 부모 본 기준 회전)으로 고정하는 `SetRotation` 3개(`ThSet0~2`, `RLArmIK` 바로 뒤)를 넣었습니다. 결과: 재장전 내내 엄지가 손목에 대해 고정이고 2.78~3.03초에 손목이 풀리는 것을 따라 부드럽게만 움직이며 끊김이 없습니다(1·3인칭). 긴급 재장전에도 같은 효과.
- **1인칭 총을 앞으로(`lyra_fp_gun_forward.py 4`):** `OffHS.A`(허리 자세 총 위치, 눈 기준)의 Y를 10 → 14cm로 4cm 앞으로 뺐습니다(견착 `OffHS.B`, 정조준 `OffAim.B`는 그대로). 이 자세는 왼팔 도달이 38.4/39.2cm로 이미 한계라 왼손이 핸드가드를 따라 4cm 뒤로 미끄러지게 했습니다(`FpBk1~3`, `FpBack`, `AllLeftBack2` → `LBackV.Y`, 가중치 = 1인칭 × 정조준 아님 × 견착 아님 × 재장전 아님, 재장전 중 손 경로는 총 기준이라 그대로). 오른손은 권총손잡이에 IK로 붙어 총을 따라옵니다. 3인칭 총 위치는 `OffHS + TpD`로 정해지므로 `TpD.A.Y`를 6.0748 − 4로 줄여 그대로 뒀고, 3인칭 캡처 전후가 같은 것을 확인했습니다. 1인칭 캡처(`Data/fp_gun_forward_compare.png`)에서 총이 앞으로 가 뒷가늠자가 화면 오른쪽 아래에 크게 보입니다.
- **HUD 재장전 점 시간(`lyra_hud_reload_duration.py`):** `BP_FurinaHUD`가 경과 시간 ÷ 고정 3.0초로 점을 채워서 긴급 재장전(2.0초)에서는 끝까지 안 차고 전술이 길어지면 일찍 찼습니다. `ReloadP = clamp(경과 ÷ max(경과 + 남은 시간, 0.01))`로 바꿔 실제 재장전 시간에 맞춥니다(PIE: 긴급 0.2/0.43/0.63/0.85가 시간에 비례, 일반 재장전 3.0초에 비례).
- **미확인:** 1인칭에서 총 앞으로(허리 자세)의 앉기·달리기·견착 자세, 손 위치를 화면으로 본 것은 잠금 상태 캡처 한 장뿐입니다. 견착(우클릭 길게)은 총 위치를 바꾸지 않았습니다.

## 1인칭 권총 적용 (Armpist.fbx 분석 반영, 1인칭 전용)
- ABP_Furina: `ModifyCurve_ViewState` 에 곡선 `PistolOn`(= FurinaPistolOn 활성) 추가 (`Scripts/Unreal/lyra_abp_pistol_curve.py`). CR 에 곡선 등록(`lyra_cr_add_curve.py PistolOn`).
- 양손 파지: CR `PistGrip` = Lerp(소총 왼손 목표 LHandOff3, 권총 지지 위치, `PistW` = PistolOn x RlFpW). 지지 위치 FBX 환산값 (-0.1,-18.8,-12.8) 이 실제 손목에서 (-0.1,-18.8,-12.8) 로 측정되도록 목표값은 (-0.1,-11.5,-12.8) (`lyra_cr_pistol_grip.py`).
- 총 위치: 소총용 허리 위치 그대로면 손이 카메라 뒤로 가서 보이지 않음 -> 권총일 때만 눈 기준 오프셋 (X+1.5, Y+16, Z+1.5) (`lyra_cr_pistol_gunoff.py`, 노드 PistGOff/PistGAdd, OffAim.A 앞). FBX 는 프레임이 카메라 앞 약 42 cm.
- 슬라이드 후퇴/탄피: 이미 있던 슬라이드 시스템 그대로 사용 (새로 만들지 않음). 발사 반동도 기존 FurinaRifleShot/RifleKick 그대로.
- 재장전: FBX `FPS_Pistol_Reload_easy` 왼손(프레임 무게중심 기준, 0프레임 대비) 경로를 `Furina_Pistol_Reload`(2.0초)에 곡선 PRX/PRY/PRZ 로 기록(시간 1.317초 -> 2.0초), CR 이 PistGrip 지지 위치에 더함 (`Scripts/Blender/extract_pistol_reload_hand.py`, `lyra_pistol_reload_curves.py`, `lyra_cr_pistol_reload.py`). 백업 `/Game/Furina/Backups/Furina_Pistol_Reload_pre_fp`.
  왼손 경로: 왼쪽 +24 cm, 뒤 -50 cm(탄창 집기) 까지 갔다가 복귀 - PIE 측정 확인(`Data/lyra_pistol_reload_probe_r2.json`).
- 3인칭은 권총일 때 CR Alpha 0 이라 변화 없음. 미적용/한계: 권총 탄창 메시 이동, 빈 탄창(Reload_full) 전용 동작·슬라이드 놓기, 달리기/앉기 변형, 걷기 흔들림(Walk) 별도 반영.

### 1인칭 권총 보정 2 (손-총 분리 + 거리)
- 원인: `FurinaRifle` 은 `FurinaMesh` 의 `Right-wrist` 소켓에 붙어 손-총 관계가 고정이다. P220 프레임 경계가 소총 컴포넌트 기준 Y -8.5~10.8 인데 오른손 손가락 끝이 Y -7~-13 이어서 손잡이 뒤 3~5 cm 에 떠 있었다(FBX 의 손 위치는 FBX 프레임 기준이라 P220 모델과 어긋남). CR 로 손만 옮기면 총도 같이 따라와서 소용없다.
- 수정(`Scripts/Unreal/lyra_pistol_fp_offset_bp.py`, ThirdPersonCharacter_BP): FurinaMagUpdate 의 권총 분기에서 `FurinaPistolFrame` 상대 위치 = VLerp((0,-4.27,0.63), (0,-13.77,0.63), IsActive(FurinaFPWanted)) -> 1인칭일 때만 9.5 cm 손 쪽으로. 3인칭은 그대로. 측정 `lyra_pistol_grip_probe_g11.json`: 프레임 Y -18.0~1.3.
- 거리: 권총 눈 기준 오프셋 (X+1.5, Y+18, Z+3) (`lyra_cr_pistol_gunoff.py`). 손 CR 보정(`lyra_cr_pistol_rhand.py`)은 dY=0 으로 둠(총이 손에 붙어 있어 효과 없음).

## 소총 재장전 시간 (2026-11-19)
- 전술 재장전(잔탄>0, 손잡이 안 당김) 3.3초: 몽타주 속도 3.133/3.3 = 0.9494, 타이머 P2_SelF_5ce19d38 소총값 3.3.
- 빈 탄창 재장전(잔탄 0, 손잡이 당김) 3.0초: 몽타주(FBT_EmptyMontage) 속도 2.0/3.0 = 0.6667, 타이머 FBT_TimeSel.A = 3.0.
- 스크립트 `Scripts/Unreal/lyra_rifle_reload_times.py [전술초 빈탄창초]`(새 에디터에서 한 번). 권총(2.3초)은 그대로. HUD 점은 실제 시간 기준이라 자동 반영.
- PIE 측정(`Data/lyra_empty_reload_probe_t33.json`): 전술 3.309초(탄창 17->20), 빈 탄창 약 3.06초(0->20), 전술 재장전 중 노리쇠 움직임 없음.

## 재장전 손가락/엄지 수정 (2026-11-19)
- 측정: `Scripts/Unreal/lyra_reload_finger_probe.py` (재장전 중 왼손 손가락/엄지의 부모 기준 로컬 회전을 매 틱 기록) -> `Data/lyra_reload_finger_probe_f1.json`(수정 전), `_d1.json`(수정 후).
- 엄지 꿈틀: 빈 탄창 재장전 끝(약 2.9~3.4초)에 엄지 2마디가 최대 46도 움직였다가 돌아왔다. 엄지 고정(ThSet0-2)의 가중치가 ReloadSm(재장전 곡선 0 이 되면 풀림)이라 몽타주 블렌드 아웃 포즈로 풀렸기 때문. -> `ThW = Max(ReloadSm, RlFpW x (1 - PistW))`: 1인칭 소총은 엄지를 항상 고정. 수정 후 측정에서 엄지 편차 0.0/1.5/0.0 도(재장전 전 구간).
- 손잡이 당기러 갈 때 손가락 튐: HandleFp 곡선이 0.12초에 0->1 로 올라가 손가락이 0.06초에 28~32도 튐 -> `RlHSm`(AccumulateLerp, Blend 6)로 부드럽게 (`lyra_cr_reload_finger_fix.py [Blend]`). Blend 10 에서 측정 18~21도/0.06초로 감소, 현재 6.
- 미해결/관찰: 손잡이 접근 중 손이 카메라 바로 앞을 지나 흰 장갑 등이 화면을 크게 가리는 구간이 있음(손 위치 자체). 전술 재장전 끝에서 손가락이 0.15초 사이 약 85도 감기는 것은 손이 핸드가드로 돌아오는 자연스러운 감기(ReloadSm 감쇠).
- 진단용 디버그 곡선 연결(`lyra_cr_dbg_wire.py on|off`)은 off 로 원복함.

### 소총 전술 재장전 2.5초로 단축 (2026-11-19)
- 전술 재장전(잔탄>0): 3.3초 -> 2.5초 (`lyra_rifle_reload_times.py 2.5 3.0`: 몽타주 속도 3.133/2.5 = 1.2532, 타이머 2.5). 빈 탄창 재장전은 3.0초 그대로, 권총(2.3초) 그대로.
- PIE 로 다시 측정하지는 않음(값만 변경, 컴파일/저장 확인).

### 1인칭 권총 왼손 아귀 보정 (2026-11-19)
- 진단: Armpist.fbx 의 총 크기는 P220(프레임 길이 19.8 vs 19.3, 높이 14.3 vs 13.7)과 거의 같고 오른손은 이미 프레임에 맞았지만, 왼손이 프레임 아래로 1.5~6 cm 떠 있었다(`Scripts/Blender/pistol_fbx_bounds.py` -> `Data/pistol_fbx_bounds.json`, 손 뼈 위치를 총 프레임 경계와 비교; `Data/plot_fit.py <태그>` 로 측면/위/뒤 도식 `pistol_fit_plot_<태그>.png`).
- 수정: 왼손 지지 목표(PistBAdd.A) (-0.1,-11.5,-12.8) -> (3.0,-8.7,-8.3) (`lyra_cr_pistol_reload.py 3.0 -8.7 -8.3`). 측정 손목 (3.0,-16.0,-8.3): 프레임 왼쪽 옆, 손잡이 아래쪽 모서리 높이. 손가락 끝이 손잡이 앞(Y -8~-10)을 가로질러 오른손 손가락 앞을 감싼다(`lyra_pistol_grip_probe_g14.json`).
- 확인 못 한 것: 손 회전/손가락 굽힘 모양 세부는 도식과 1인칭 캡처로만 봤다(근접 카메라 촬영은 FP 카메라가 팔 메시의 부모라 불가).

### 1인칭 권총 손가락 관통 수정 (2026-11-19)
- 증상: 손이 총 손잡이를 뚫음(사용자 캡처). 원인: 오른손 손가락 자세는 소총 권총손잡이 감싸기 자세로 고정이고, P220 손잡이는 더 얇고 방향이 달라 손가락 관절 점이 메시 안쪽으로 들어갔다.
- 측정: P220 메시를 FBX 로 내보내(`lyra_export_p220_mesh.py`) Blender 에서 손 뼈를 따라 점을 뿌려 부호 있는 거리 계산(`Scripts/Blender/pistol_hand_penetration*.py`). 관통 점수 7.7(가운데손가락 1.07 cm 안쪽) -> 0.
- 해법: 총을 손에 대해 이동 (1.0,-6.5,0.5) cm + 회전(X -3°, Y(총구축) 30°). 총의 보이는 위치/각도는 그대로 두려고 손(=소총 컴포넌트)을 반대로 굴림:
  CR `PistQw/GRotP`(GRotR x Q) 를 오른손 위치/회전(RRHOff, RRHRot)에만 적용, 손목 위치 보정 `PistRV.B`(`lyra_cr_pistol_roll.py`, 상수 `Data/pistol_roll_constants.json`)
  BP: FurinaPistolFrame 상대 위치/회전 = (3.35,-20.03,0.59) / (P -2.6, Y 91.5, R -30.0) 을 1인칭에서만 (`lyra_pistol_fp_roll_bp.py`).  3인칭은 (0,-4.27,0.63)/(0,90,0) 그대로.
- 검증(PIE `lyra_pistol_grip_probe_g15.json`): 소총 컴포넌트 회전이 설계한 Q 와 일치(30.15도), 프레임 경계가 예측과 0.5 cm 이내. 왼손은 0.45 -> 0 으로 미세 조정(왼손 목표 (2.82,-8.66,-8.98)).
- 미확인: 인게임 육안 확인은 못 함(근접 외부 카메라 불가). 재장전/발사 중 관통, 걷기/앉기는 재측정 안 함.

### 1인칭 권총 파지 직접 제작 (2026-11-19, "파지는 직접 만들어봐")
- 이전 방식(소총용 애니메이션 손가락 자세에 총만 맞춤)은 실제 스킨 두께(손가락 반경 0.5~0.9 cm, `furina_hand_radius.py`)를 쓰면 어떤 위치에서도 관통이 남았다(`pistol_hand_penetration_roll2.py`).
- 해법: 손가락 굽힘을 직접 만든다. `Scripts/Blender/pistol_finger_author.py`: 손가락 사슬(MCP/PIP/DIP/끝)을 평면 FK 로 마디별 증분(Δ MCP, Δ PIP, Δ DIP) 굽혀 P220 메시(관통: 근위 0.8/중위 0.65/말단 0.5 cm, 접촉: DIP/끝이 표면+0.25 이내)로 점수화, 격자 탐색.
  굽힘 축은 손가락 법선(소총 컴포넌트 좌표)을 월드 -> 뼈 로컬로 변환(월드 변환 빠뜨리면 효과가 작아짐 - 고침). 결과 `Data/pistol_finger_author_g17.json`.
- CR(`lyra_cr_pistol_fingers.py g17 [R|L|RL]`): 뼈별 `PgG_/PgQ_/PgM_/PgS_` 노드 = 로컬 회전 x FromAxisAndAngle(축, Δ), 가중치 PistW. 오른손 10개 + 왼손 8개 뼈(Δ=0 인 뼈 제외). 노드 하나당 추가가 매우 느려(1~2분/뼈) 손 단위로 나눠 실행.
- 검증(`Scripts/Blender/pistol_finger_check.py g19`, PIE `lyra_pistol_grip_probe_g19.json`): 관통 오른손/왼손 모두 0, 접촉 간격 오른손 0, 왼손 0.3~0.4 cm.  수정 전(g17) 가운데/약지 관통 1.3/1.6 cm.
- 한계: 손가락 사이 벌어짐(외전)과 손바닥 스킨은 모델링하지 않음. 육안 최종 확인은 사용자 화면에서.

## 3인칭 등 매기 소총 / 허리 홀스터 권총 (2026-11-19, 1단계)
- 추가 컴포넌트(ThirdPersonCharacter_BP): `FurinaSlingM4`(SkeletalMesh SK_M4A1, 소켓 Spine), `FurinaHolsterFrame`(SM_P220_Frame, 소켓 Hips) + 자식 `FurinaHolsterSlide`. (`Scripts/Unreal/lyra_gear_comps.py`)
- 위치: PIE 뼈 월드 변환(`lyra_bone_probe.py` -> `Data/lyra_bone_probe_b1.json`)으로 소켓 상대 위치/회전을 계산(`Data/gear_place_v1.json`, 소총: 등에 대각선 총구 위·오른쪽, 조준경 뒤쪽 / 권총: 오른쪽 허리 총구 아래, 가늠자 앞쪽).
- 로직(`lyra_gear_graph.py`): FurinaMagUpdate 타이머 맨 앞에서 1회 AttachToComponent(KeepRelative) 후 매 틱 가시성 = 소총 등 매기: 권총 장착 AND 1인칭 아님 / 홀스터 권총: 소총 장착 AND 1인칭 아님.
- 확인(`lyra_tp_gear_probe.py t1`, `Data/tpgear_t1_*`): 소켓 부착 정상(Spine/Hips), 소총 상태에서 오른쪽 허리에 권총, 권총 상태에서 등에 소총이 대각선으로 보임. 세부 위치(허리 높이, 각도)는 육안으로 더 다듬을 여지 있음. 1인칭 가시성은 로직상 숨김이지만 이번에는 따로 캡처 확인 안 함.
- 아직 안 한 것(다음 단계 계획): (a) 교체 모션 - 스왑 위상 곡선(컴포넌트 스케일로 ABP 에 전달)과 TP CR 에서 오른손 경로(홀스터 <-> 어깨 뒤 <-> 준비 자세), 상체(Spine/Chest/클래비클) 회전, 소총 등 이동/권총 손 이동 타이밍, 교체 시간 연장 (b) 3인칭 권총 달리기(소총 달리기 참고) + 권총 준비 자세의 상체 관절 적극 사용 (c) 뽑기/집어넣기 모션 세부.

## 1인칭 권총 손-총 거리 정밀 보정 + 손가락 꿈틀거림 제거 (2026-11-19)
### 옆면 캡처 도구 (FP 카메라가 팔의 부모라 외부 카메라가 안 되던 문제 해결)
- `Scripts/Unreal/lyra_pistol_side_probe.py [태그]`: 레벨의 기존 액터(AtmosphericFog)를 `set_mobility(MOVABLE)` 후 `set_view_target_with_blend` 로 임시 카메라로 쓴다(PIE 에서 CameraActor 스폰 API 는 없음). 매 틱 총 프레임 중심을 따라가며 월드 기준 왼쪽/오른쪽/위/뒤 에서 촬영(총이 시선 방향에 따라 움직이므로 컨트롤 yaw 고정). 
  캡처 `Data/pside_<태그><세트>_<뷰>.png`, 기록 `Data/lyra_pistol_side_probe_<태그>.json`(카메라/뼈 월드 좌표). `Data/side_sets_<태그>.json` 에 `[{"tag":"a","vars":{BP변수:값},"views":["left","right"]}, ...]` 를 두면 한 번의 PIE 에서 후보를 연속 비교.
- `Data/side_overlay.py <태그>`: 기록된 카메라(FOV 90, 롤 0)로 뼈 위치를 투영해 이미지 위에 표시(빨강 오른손, 초록 왼손, 노랑 프레임 중심) -> `_ov.png`.  (UE 는 왼손 좌표계: 오른쪽 벡터 = cross(up, fwd))
### 손-총 거리
- 옆면 캡처 결과(`pside_s6_*`): 이전 수치 모델(Blender 부호 거리)과 달리 실제 화면에서는 권총이 양손보다 약 5~6 cm 위, 4~5 cm 앞쪽에 떠 있었고 손은 총 아래에서 펼쳐져 있었다 (관통 0 이라는 수치가 실제 스킨과 어긋났음).
- BP 변수화: `Scripts/Unreal/lyra_pistol_fp_vars_bp.py` (FBP_VLerp/FBP_RLerp 의 FP 값 -> 실수 변수 FurinaPFLocX/Y/Z, FurinaPFRotP/Y/R) + `lyra_bp_vars_editable.py`(인스턴스 편집 가능) -> PIE 파이썬에서 `set_editor_property` 로 런타임 조절 가능.
- 후보 비교(`pside_s11*`): a (소총 컴포넌트 기준 FP 프레임 위치 (0.99,-12.94,-4.35); 월드 기준 이전 위치에서 뒤 1.9 cm, 아래 3.9 cm) 가 가장 좋음 - 오른손이 그립 뒷면~옆면을 감싸고 검지가 방아쇠울에 닿으며 왼손이 그립 왼쪽 아래를 받친다. 이전 값 (3.345,-20.027,0.589) 대비 총이 손 쪽으로 이동. 회전은 그대로 (P -2.598, Y 91.501, R -30.034).
### 손가락 꿈틀거림
- 측정: `Scripts/Unreal/lyra_pistol_twitch_probe.py [태그]` (FP 권총에서 대기/시선 이동/걷기/빠른 걷기/점프/발사/재장전 구간별 손가락 32개 뼈의 부모 기준 로컬 회전 변화량·속도, 대기 자세 상수 `consts`).
  수정 전(w5): 재장전 중 최대 82도/900도초(오른손 검지2 등), 대기 중에도 왼손 1.7도 떨림.
- 원인: 손가락 증분(PgS_*)이 애니메이션 포즈 위에 얹히는 구조라 재장전 몽타주 손가락 동작/상태 전환 때 그대로 움직였다.
- 수정: `Scripts/Unreal/lyra_cr_pistol_lock.py <태그> [R|L|RL]`: 뼈마다 `PgK_<뼈>` = SetRotation(Local, 상수 쿼터니언, Weight=PistW, 자식 전파) 32개를 SetHairFlow 앞에 추가 (권총 모드에서는 대기 자세로 완전 고정; 소총 모드는 PistW=0 이라 변화 없음).
  수정 후(w6/w8/w9): 대기/걷기/점프/재장전 변화 0.02도 이내, 발사 0.4도. 남은 것: 권총 전환 직후 0.07초 동안 소총 자세 -> 권총 자세 스냅(교체 중이라 눈에 안 띔).
- 참고: 측정에서 Thumb3_R/L 이 40도 움직인 것은 스켈레톤에 없는 이름(부모 None)이라 메시 컴포넌트 회전을 읽은 착시였음. 실험 중 CR 계층에 Thumb3_R/L 뼈(`lyra_cr_add_bone.py`)와 PgK_Thumb3_* 노드를 추가했으나 불필요(무해). 
- 한계: 재장전 중 왼손 손가락도 대기 자세로 고정되어 탄창을 잡는 순간 손가락 변화가 없음(꿈틀거림 제거 우선).
- 최종 확인(`pside_s12_*`, `pside_before_after.png`: 왼쪽 열 수정 전, 오른쪽 열 수정 후 / 위 오른쪽 뷰, 아래 왼쪽 뷰): BP 기본값 FurinaPFLocX/Y/Z = (0.99,-12.94,-4.35) 로 확정(저장됨). 양손이 그립을 쥔 모습 확인.

## 오른손 권총 파지 꽉 쥐기 (2026-11-19, 백그라운드 작업)
- 실측 분석(`Scripts/Blender/pistol_contact_real.py`, UE 변환을 그대로 사용): 수정 전 오른손은 중지/약지/새끼가 메시 표면 0~0.3 cm 로 닿아 있었지만 **엄지가 프레임에서 2.2 cm 떠서 위로 뻗은 상태**, 검지는 펴짐.
- 최적화(`Scripts/Blender/pistol_grip_firm.py`: 손가락 Δ 격자 + 총 미세 이동 탐색; 목표=PIP/DIP/끝이 표면+0.25 이내, 엄지 외전 포함): 총 이동은 0(현 위치가 최적), 오른손 Δ = 검지 MCP -15, 중지 (55,0,55), 약지 (20,-15,40), 새끼 (10,0,0), 엄지 (외전30,15,30,0). 결과 `Data/pistol_grip_firm_s17.json`(뼈별 dq).
- 적용: `Scripts/Unreal/lyra_cr_pistol_lock_apply.py` (잠금 상수 x dq, PgK_<뼈>.Value 만 갱신; 헤드리스 27초) -> 새 상수 `Data/pistol_consts_v2.json`.
- 검증(`pside_s18_*`, 접촉 재측정): 중지/약지/새끼 관절 중심-표면 거리 0.34~0.83 cm(반경 0.5~0.65 = 접촉), 엄지 2.25 -> 0.76~1.06 cm(프레임 옆면에 누움), 검지 약간 펴짐(방아쇠울 옆). 비교 `Data/pside_grip_s17_s18.png`.
### 백그라운드 실행 방식 (PC 입력 안 건드림)
- CR/BP 수정: `UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script="<py 경로(공백 없음) 인자...>" -unattended -nopause -nosplash -NullRHI` (약 20~30초).
- PIE 캡처 프로브: `Scripts/run_ue_probe.ps1 -ScriptPath <py> -Tag <태그> -Done <json> -Timeout 480` 이 에디터를 `-ExecCmds="py <py> <태그>"` 로 띄우고 창을 화면 밖(x=6000)으로 옮긴 뒤 JSON 에 "done": true 가 되면 종료 (약 80초). 주의: -ExecCmds 안에 따옴표를 넣으면 명령이 잘림, .ps1 에 한글 주석을 넣으면 PowerShell 5.1 이 깨짐.

## 1인칭 전용 팔: 총과 한몸으로 보이기/숨기기 (2026-11-20)
3인칭 몸(FurinaMesh)의 팔을 1인칭에서 IK 로 총에 붙여 쓰던 방식 대신, 1인칭에서만 보이는 **팔 전용 스태틱 메시를 총 컴포넌트의 자식**으로 붙였다. 손과 총의 관계가 메시 안에 구워져 있어 어떤 상태(조준/견착/달리기/반동)에서도 손-총 오차가 0 이다.
### 만드는 순서
1. 자세 기록(PIE, 백그라운드): `Scripts/Unreal/lyra_fp_arms_pose_probe.py <태그>` (`p` 로 시작하는 태그는 권총으로 바꾼 뒤) -> `Data/lyra_fp_arms_pose_<태그>.json` (모든 뼈의 컴포넌트/월드 변환 + 참조 포즈, 소총/권총 프레임/카메라 변환, hip/ads/shoulder/crouch).
2. Blender 굽기:
   - 소총 `Scripts/Blender/fp_arms_bake.py -- <포즈> 4 0.5 <카메라 포즈> <소매접기> <출력>` -> `FBX/FPArms/SM_FurinaFPArm<L|R>_<출력>.fbx` (소총 컴포넌트 로컬 좌표).
   - 권총 `Scripts/Blender/fp_pistol_arms_bake.py -- <포즈 p..> <출력> 4 -0.9 "R=sem,L=sem" 0 1` -> `SM_FurinaFPPistArm<L|R>_<출력>.fbx` (FurinaPistolFrame 로컬 좌표).
   - UE 컴포넌트 공간 <-> Blender 아마추어 공간 대응은 참조 포즈 뼈 위치로 맞춘다(결과 X/−Y/Z 반사, 오차 0.0001 cm). 팔 = `Left/Right arm` 이하 뼈 가중치 합 >= 0.5 정점(한 팔 약 2000 정점, 머티리얼 SkinHair/Outfit 2개).
3. 가져오기(헤드리스): `Scripts/Unreal/lyra_fp_arms_import.py <출력> [rifle|pistol]` -> `/Game/Furina/FPArms/SM_FurinaFPArmL/R`, `SM_FurinaFPPistArmL/R` (SK_Furina 머티리얼 슬롯 이름으로 연결, 경계 오차 0.000004 cm 이하 확인).
4. BP(헤드리스, 처음 한 번): `lyra_fp_arms_bp.py` -> `lyra_fp_arms_bp_fix.py` -> `lyra_fp_arms_bp_pistol.py`.
   - 컴포넌트: `FurinaFPArmL/R`(부모 FurinaRifle), `FurinaFPPistArmL/R`(부모 FurinaPistolFrame), 상대 변환 0.
   - `FurinaMagUpdate`(0.033초) 맨 앞 `FPA_*`/`FPP_*`: 1인칭(FPCamera 활성)에서 소총이면 소총 팔, 권총이면 권총 팔을 보이고, 본체의 `Right-arm`/`Left-arm` 뼈를 숨긴다(상태가 바뀔 때만 Hide/UnHide). 3인칭이면 전용 팔 숨김 + 본체 팔 보임.
   - 재장전(`FurinaReloading`) 중에는 왼손이 탄창을 가지러 가야 하므로 전용 왼팔을 숨기고 본체 왼팔을 보인다. 끝난 뒤 `FurinaFPArmLHold`(0.8초 감소) 또는 본체 왼손목이 구운 위치 0.5 cm 이내가 되면 다시 전용 왼팔.
   - 뼈 숨김은 그 뼈의 애니메이션 계산을 빼 버리지만(`ExcludeHiddenBones`), FurinaMesh 가 `AlwaysTickPoseAndRefreshBones` 라서 오른손목 소켓(총이 붙은 곳)은 계속 계산된다(엔진 소스 확인).
### 겪은 문제
- `IsBoneHiddenByName` 은 실행 핀이 있는 함수라 실행선에 넣지 않으면 항상 거짓 -> 숨김이 풀리지 않았다(수정).
- UE5.8 에서 `Subtract/Less/LessEqual_DoubleDouble` 을 파이썬으로 추가하면 승격 연산자가 되어 `set_pin_value` 상수가 비어 있었다(감소량 0, 비교값 0) -> `FInterpTo_Constant`, `InRange_FloatFloat` 로 교체.
- 정조준에서 왼쪽 아래에 황갈색 판: 왼소매 끝 날개(`Sleeve_2/3_L`)의 안감이 보인 것(잘린 끝이 아님: 잘린 끝 정점 23개는 어느 상태에서도 화면 밖). 1인칭 팔만 소매 날개를 팔꿈치 쪽으로 90% 접어서(`소매접기 -0.9`) 해결. Blender 렌더(`fp_arms_render.py`, UE 화면과 일치)로 확인.
- **P220 FBX(`Data/p220_export`)에는 충돌용 볼록 껍질 `UCX_*` 가 같이 들어 있다.** 이전의 권총 파지 스크립트들(`pistol_contact_real.py`, `pistol_grip_firm.py`, `pistol_grip_final.py` 등)은 이것까지 합쳐서 거리를 쟀기 때문에 손잡이 앞/방아쇠울 아래가 꽉 찬 상자로 계산됐다(손가락이 손잡이를 감쌀 수 없었던 원인). 새 스크립트는 `UCX_` 를 뺀다.
- Armpist.fbx -> P220 회전 대응(경계 상자 맞춤)은 앞/뒤를 구분하지 못해 손이 뒤집혀(손가락이 뒤로 감김) 놓였다. 또 그 애니메이션의 왼손은 손잡이 바닥을 받치는 자세였다. -> 권총 손은 **P220 손잡이 실측 단면**(광선 투사 `p220_landmarks.py`: 뒷면 x=-4.25+(z+8)*0.323, 앞면 x=1.72+(z+8)*0.227, 폭 y -1.03..1.47, 방아쇠 x≈5.2 z≈-1.2)으로 목표를 잡는다.
### 권총 파지 계산 (`fp_pistol_arms_bake.py`)
- 목표(프레임 로컬): 오른손 MCP 줄 = 손잡이 오른쪽 면 앞쪽 62%, 손목 = 손잡이 뒤 4 cm, 엄지 = 왼쪽 면 위, 검지 끝 = 방아쇠 / 왼손 MCP 줄 = 손잡이 앞-왼쪽(오른손가락 바깥), 손바닥 = 왼쪽 면.
- 가중 Kabsch 로 손 배치 -> 팔 2본 IK -> 손 6자유도 국소 탐색(±10°, ±1 cm; 실제 피부 정점이 관통 없이 닿게 + 설계 위치 유지 + 검지-방아쇠 거리) -> 손가락 관절별 굽힘 격자(검지/엄지는 옆 벌림 포함). 거리는 실제 피부 정점(주 뼈에 강체 근사)과 P220 표면(왼손은 오른손 피부 포함)의 부호 거리.
- 결과(q10, 피부 정점-P220): 오른손 중지/약지/새끼 세 마디와 엄지가 표면 0~0.1 cm 접촉, 검지 끝 방아쇠(설계점과 0.2 cm), 관통은 손바닥 3정점 최대 0.47 cm. 왼손은 주먹으로 왼쪽 면과 오른손가락을 감싼다(엄지는 앞으로 뻗지 않고 접힘). 렌더 `Data/fpp_q10_*.png`(`fp_pistol_render.py`, 외부 시점).
### UE 확인 (백그라운드 PIE, `lyra_fp_arms_probe.py <태그>`; `p` 태그 = 권총)
- 소총(`fpa_v2_*`): 허리/내려보기/올려보기/정조준/견착/걷기/발사에서 전용 팔 L/R 보임, 본체 팔 숨김. 재장전 시작 0.015초 뒤 전용 왼팔 -> 본체 왼팔, 끝나고 0.8초 뒤 복귀. 권총 전환·3인칭에서 전용 팔 숨김 + 본체 팔 복원. 정조준 소매 안감 수정 후 `SM_FurinaFPArm*` 는 `n9` 굽기.
- 권총(`fpa_pv1_*`, 굽기 `q10`): 1인칭 권총에서 권총 전용 팔만 보이고(소총 팔 숨김), 재장전 중 왼팔 교체, 3인칭 복원. 바깥 시점(`fpa_pv1_grip_cmp.jpg`): 오른손이 손잡이를 높게 감싸고 검지가 방아쇠에, 왼손 주먹이 왼쪽 면과 오른손가락 앞을 감싼다.
### 남은 것 / 한계
- 재장전이 끝나고 본체 왼손 -> 전용 왼손으로 바뀔 때 위치가 다르면 한 번 튄다(소총: 본체 왼손이 조준 피치에 따라 0.3~5.8 cm 덜 닿아서, 끝날 때 약 2.5 cm). 권총은 본체 왼손 지지 위치(CR `PistBAdd`)와 새 주먹 위치가 달라 더 클 수 있다(아직 재지 않음).
- 권총 왼손 엄지는 앞으로 뻗지 않고 접힘. 손바닥 피부가 총에 최대 0.47(오른손)/0.59(왼손) cm 들어가는 정점이 2~3개 있다.
- 전용 팔은 고정 자세라 손가락이 움직이지 않는다(발사 시 방아쇠 손가락 움직임 없음). 본체 팔의 그림자는 1인칭에서 전용 팔 그림자로 바뀐다.

## 개발자용 무기 선택창 (Tab, 2026-11-21)
- **Tab** 으로 열고, 열린 상태에서 **Tab / Esc** 로 닫는다. 열려 있는 동안 마우스 커서가 보이고 입력은 UI 전용(클릭해도 총이 안 나감, 시점 안 돎).
- 위젯 `/Game/Furina/UI/WBP_FurinaWeaponMenu`(버튼+텍스트만): 1번 무기(주무기) 표 = 행 병과 7(장교/보병/돌격병/대전차병/중화기병/저격수/기갑병) x 열 국가 6(독일/일본/이탈리아/미국/소련/영국). 버튼 이름 `Btn_<병과번호>_<국가번호>`(0부터, 예 보병-미국 M1 Garand = `Btn_1_3`), 글자 `Txt_<병과>_<국가>`. **지금은 무기가 없어서 42개 모두 비활성(회색)**. 2번 무기(근접: 삽/칼)는 '비어 있음' 텍스트만.
- 무기를 넣을 때: 해당 `Btn_c_n` 을 활성화하고 OnClicked 에 장착 로직 연결, `Current` 텍스트 갱신.
- 만든 스크립트(헤드리스): `lyra_weapon_menu_widget.py`(위젯 생성. 새 위젯 BP 는 파이썬으로 루트 패널을 지정할 수 없어서 그래프가 비어 있는 번들 위젯 `GrindRailGuideWidgetBP/Guide_Widget_WBP` 를 복제해 루트 CanvasPanel 내용을 교체), `lyra_weapon_menu_widget_logic.py`(위젯 `CloseMenu` 이벤트 + `OnKeyDown` 재정의, 포커스 가능), `lyra_weapon_menu_pawn.py`(폰: 기존 Tab 키 노드 -> 커스텀 이벤트 `FurinaWeaponMenuToggle` 과 같은 경로, 변수 `FurinaWeaponMenu`).
- **Tab 은 원래 마우스 상하 반전 토글(`InvertLookUp?`, FlipFlop)** 이었다. 그 연결을 끊었으므로 지금은 반전 토글 키가 없다(노드는 그래프에 남아 있음).
- C++ 판(`FurinaSource/CppDraft/FurinaWeaponMenuComponent.*`, Slate)도 써 두었지만 이 PC 에 Windows SDK 가 없어 빌드할 수 없어서 쓰지 않는다.
- 확인(`lyra_weapon_menu_probe.py m1`, `Data/wmenu_m1_*.png`): 열기 -> 위젯 닫기 -> 열기 -> 토글 닫기 모두 화면 추가/제거와 커서 표시가 맞게 바뀜. 한글 표시 정상. 실제 키보드 Tab/Esc 누름은 자동 확인하지 못했다(같은 이벤트 경로를 직접 호출해 확인).
### 무기 선택창 국가별 탭으로 변경 + 크기 확대 (2026-11-21)
- 구성: 위쪽 국가 탭 6개(순서: 제3제국, 대일본제국, 이탈리아제국, 미국, 소비에트연방, 영국) -> 선택한 국가의 표(병과 7행 x 1~3순위). 별표(★)와 `†`(대일본제국 저격수 3순위, 이탈리아제국 저격수 1~3순위)는 뺐다(`lyra_weapon_menu_nodagger.py`, 확인 `Data/wmenu_m4_snipers.jpg`). `SMLE No.1 Mk III*` 의 `*` 는 무기 이름의 일부라 둠.
- 국가 전환: 탭 클릭 또는 숫자 1~6. 닫기: Tab / Esc. 글씨 15~26pt(제목 26, 탭 19, 병과 18, 버튼 17), 버튼 290x44, 패널 약 1.1천 x 650 px(1080p 기준).
- 위젯 이름: `Nation_<국가>`(표, 처음엔 0만 보임), `Tab_<국가>`, `TabRow`, 버튼 `Btn_<국가>_<병과>_<순위>`(0부터; 예 미국 보병 1순위 M1 Garand = `Btn_3_1_0`), 글자 `Txt_<...>`. 아직 무기가 없어 126개 모두 비활성.
- 스크립트: `lyra_weapon_menu_widget2.py`(같은 자산에서 내용만 교체 -> 폰 참조 유지), `lyra_weapon_menu_logic2.py`(변수 `NationIndex`, 이벤트 `ApplyNation`, `OnKeyDown` 1~6/Tab/Esc, `OnMouseButtonDown` 탭 클릭 = TabRow 안 가로 위치 6등분).
  - 위젯 변수 지정(`bIsVariable`)은 파이썬 속성으로 안 열려 있어서 `SystemLibrary` 기본 객체의 `call_method('SetBoolPropertyByName', ...)` 로 설정. `GetWidgetFromName` 은 블루프린트에서 쓸 수 없음. `SlateBlueprintLibrary` 는 `/Script/UMG` 소속.
- 확인(`lyra_weapon_menu_probe.py m3`, `Data/wmenu_m3_*.png`): 열기, 미국/영국 전환(표 교체 + 탭 강조), 닫기, 다시 열기/닫기 정상. 실제 마우스 클릭/숫자 키 입력은 자동 확인하지 못함(같은 이벤트를 직접 호출해 확인).
### 무기창 Tab 닫기/클릭이 안 되던 문제 수정 (2026-11-21)
- 원인 3가지:
  1. 복제해 온 번들 안내 위젯의 설정이 남아 위젯 전체가 `HitTestInvisible`, 루트 `CanvasPanel_0` 도 `HitTestInvisible` -> 마우스가 닿지 않고 키보드 포커스도 받지 못함.
  2. `OnKeyDown` 의 키 비교가 UE5.8 승격 연산자(Equal (Key))로 만들어져 비교 키 값이 비어 있었음 -> 어떤 키도 일치하지 않음.
  3. Lyra 는 CommonUI 가 입력 모드/포커스를 관리하므로 `AddToViewport + SetInputMode` 방식이 맞지 않음.
- 수정:
  - 위젯 가시성 `Visible`(활성화 시에도), 루트 캔버스 `SelfHitTestInvisible`(`lyra_weapon_menu_visible.py`, `lyra_weapon_menu_rootvis.py`).
  - 키 비교 B 값에 키 이름 직접 지정(`lyra_weapon_menu_fix3.py`).
  - 위젯 부모 `LyraActivatableWidget`, InputConfig = Menu, 뒤로 가기 처리, 포커스 대상 = 자기 자신(`BP_GetDesiredFocusTarget`), 닫기 = `DeactivateWidget`(`lyra_weapon_menu_commonui.py`).
  - 폰은 `PushContentToLayer_ForPlayer(UI.Layer.GameMenu)` 로 연다(`lyra_weapon_menu_pawn2.py`).
  - 탭 클릭은 `TabRow` 캐시 지오메트리가 0 이라 위치 계산 대신 누른 순간 `Tab_i.IsHovered` 로 판정.
- 실제 키/마우스로 확인(PIE, 화면 조작): Tab 열기 -> 미국 탭 클릭 전환 -> 숫자 6 영국 전환 -> Tab 닫기 모두 정상. Esc 는 Tab 과 같은 분기라 따로 누르지 않음.
- 확인용 도구: `lyra_weapon_menu_watch.py`(화면에 띄운 PIE 에서 상태 기록, `Data/wm_watch_stop` 파일로 종료), `lyra_wm_live_diag*.py`(실행 중 위젯 포커스/호버/가시성 조사).
- 추가 수정: 닫을 때 CommonUI 가 이전 입력 설정이 없어(Lyra HUD 가 지정 안 함) Menu 상태(커서 보임, 마우스 캡처 없음)로 남았다 -> 위젯 `CloseMenu` 와 폰 닫기 분기에서 `DeactivateWidget` 뒤 `SetInputMode_GameOnly` + 커서 숨김(`lyra_weapon_menu_restore.py`). 확인(`lyra_weapon_menu_probe.py m5`): 닫을 때마다 커서 False, 마우스 캡처 NoCapture -> CapturePermanently 복귀.

## 독일(제3제국) 무기 모델 21종 가져오기 (2026-11-21, 모션 없음)
- 원본 zip 20개(다운로드 폴더) -> `Downloads/FurinaWeaponSrc/Germany/<무기>/` 에 안전하게 압축 해제(경로 이탈 검사, 실행 없음, 약 1 GB, git 밖).
- Blender 정리(`Scripts/Blender/de_weapons_build.py -- preview|export`): 형식 FBX/blend/OBJ/STL + DAE(Blender 5.2 에서 Collada 가져오기가 없어 직접 파서 작성).
  - 바닥/카메라/조명/탄띠 제거, 한 메시로 합침, 방향 통일(총구 = UE +Y, 위 = +Z, 원점 = 경계 상자 중심), 실제 전장 길이로 축척(P38 21.6, P08 22.2, PP 17, Kar98k 111, G43 113, StG44 94, MP40 83.3, MP38 63(개머리판 접힘), MG42 122, MG34 121.9, Panzerfaust 104.5, Panzerschreck 164, 로켓 65, PzB39 162, GrW34 110(세운 상태), 박격포탄 33, ZF4 27, ZF39 28, ZF41 13, 7.92x94 탄 11.75, 클립 8.2 cm).
  - 무기별 처리: P38 원본은 권총 2자루+탄창+탄을 늘어놓은 장면 -> 닿아 있는 부품끼리 묶어 한 자루만, 주성분 축으로 세운 뒤 수동 보정(`Data/de_weapons_orient.json`). MP40 원본 탄창은 옆에 45도로 따로 놓여 있어 **제외**(탄창 없는 MP40). Kar98k 위에 떠 있던 부품 제거. MG42 탄띠/판 제거. ZF39 는 조립 모델(main_view)만. GrW34 의 4 m 장식 고리 제거(박격포 자체는 원본이 76삼각형 저폴리). 애니메이션 포함 FBX 는 애니메이션 끄고 가져옴. 서브디비전 모디파이어 제거.
  - 미리보기 `Data/de_prev_<키>_side.png`, 결과 `Data/de_weapons_build.json`, FBX `FurinaWeaponSrc/Germany/_export/SM_DE_<키>.fbx`.
- 텍스처 대응(`Scripts/Tools/de_weapons_texmap.py` -> `Data/de_weapons_texmap.json`): 머티리얼 이름 + 접미사(BaseColor/albedo/_a, Normal/_n, Roughness/_r, Metallic, AO). Walther PP 는 머티리얼 이름이 GUID 라 면 수로 본체/탄 구분. 텍스처 없는 박격포탄/ZF39/ZF41/클립은 단색(어두운 금속, 황동 등).
- UE(`Scripts/Unreal/lyra_de_weapons_import.py`): `/Game/Furina/Weapons/Germany/<키>/SM_DE_<키>`, 텍스처 `Textures/T_DE_*`, 머티리얼 인스턴스 `MI_DE_<키>_<슬롯>`. 공용 마스터 `/Game/Furina/Weapons/Materials/M_FurinaWeaponPBR`(BaseColor x Tint, Normal, Roughness/Metallic = 텍스처 x Scale + Add, AO). OpenGL 노멀은 G 채널 뒤집음. 30만 삼각형 넘는 MP38(221만)/ZF39/ZF41/7.92x94 탄(141만)은 Nanite.
  - 확인: 크기(cm) 21종 모두 위 값과 일치, 줄 세운 캡처 `Data/de_lineup_l2_*.png`(`lyra_de_weapons_lineup.py`, 레벨 저장 안 함)에서 총구 방향/축척 확인.
- 무기창: 제3제국 탭 21개 버튼 활성(`lyra_weapon_menu_de_buttons.py`). 누르면 `SelectedPrimary`(무기 이름)/`SelectedPrimaryKey`(모델 키, 조준경 조합은 `kar98k+zf39` 식) 변수와 '현재 선택' 글자가 바뀐다. **장착/모션은 아직 없음.** 클릭 처리는 `OnPreviewMouseButtonDown` 에서 마우스가 올라간 버튼(IsHovered)으로 판정.
  - 확인: 버튼 21개 활성 화면 캡처(`Data/wmenu_m6_de.jpg`). 실제 마우스 클릭으로 '현재 선택' 이 바뀌는지는 아직 화면에서 눌러 보지 않았다.

## 저격수 조준경 합본 (2026-11-21)
- 이전에는 조준경을 소총에 달지 않고 무기창에 `kar98k+zf39` 같은 기록만 남겼다. 실제 장착 위치 자료를 보고 합본 메시 3개를 만들었다(`Scripts/Blender/de_scoped_build.py -- preview|export`).
  - **Kar98k + ZF39(저포탑):** 앞 받침 = 앞 리시버 링(y 3.4), 뒤 받침 = 뒤 브리지(y 15.5), 조준경은 총열 중심선 위 4.8cm. 원본에 마운트가 없어 링+기둥을 만들었다.
  - **Kar98k + ZF41:** 가늠자 받침 **왼쪽**에 물리고 팔이 수평으로 뻗어 조준경이 총열 위 가운데에 온다(American Rifleman).
    - 원본 모델 방향(큰 대물 통 = 앞, 고정 팔 = 총의 왼쪽)이 원래 맞았고, 처음에 180° 돌렸던 것은 잘못이라 되돌렸다.
    - 뒤 다리가 가늠자 받침 돌출부와 0.2cm 겹쳐 0.25cm 왼쪽으로 옮겼다.
  - **G43 + ZF4:** 리시버 **오른쪽** 도브테일 레일. 원본 마운트(아래로 늘어진 다리 2개)가 왼쪽 장전 손잡이의 이동 경로와 겹쳐 지우고, 오른쪽 레일판·다리·링을 새로 만들었다(링 아래와 리시버 윗면 사이 1.1cm).
- **재질(조준경은 따로 구한 모델이라 색감이 다름):**
  - 소총 텍스처의 금속 부위(metallic>0.5) 평균을 쟀다(`Scripts/Tools/de_metal_color.py` → `Data/de_metal_color.json`): Kar98k 선형 0.08 / 거칠기 0.36, G43 0.05 / 0.30.
  - ZF4 원본 텍스처는 평평한 회색에 늘어진 픽셀이고 금속값이 0이었다.
  - 그래서 조준경 3종을 소총 실측값에 맞춘 단색 블루잉 강철로 바꿨다. 수집가 자료에서 원래 마감은 블루잉, 마운트는 인산염이라 ZF4 마운트는 인산염 회색으로 했다.
  - 단품 조준경 에셋 3개에도 같은 색을 적용했다.
- UE: `/Game/Furina/Weapons/Germany/<kar98k_zf39|kar98k_zf41|g43_zf4>/SM_DE_<키>`.
  - `lyra_de_weapons_import.py` 가 `Data/de_scoped_texmap.json`(소총 재질 재사용 + 단색)을 합쳐 읽는다.
  - 다시 가져올 때 예전 텍스처 매개변수를 지우도록 바꿨다.
  - 무기창 저격수 버튼 키를 에셋 키(`kar98k_zf39` 등)로 바꿨다.
- 확인: 옆/위/앞/뒤 렌더 `Data/de_prev_<키>_*.png`, 모음 `Data/de_scoped_sheet.jpg`.
- 출처는 `Motion/DE_FP_MOTION_RESEARCH.md` 1-1, 2절.

## 독일 무기 1인칭 모션 — Kar98k 먼저 (2026-11-21)
- **조사:** `Motion/DE_FP_MOTION_RESEARCH.md`.
  - 무기마다 출처를 3개 이상 정리했다. 당시 자료로 TM-E 30-451(1945)과 Lone Sentry 전재본을 썼다.
  - 사용자가 준 볼트액션 1인칭 애니(zip)는 **참고만** 했다. 메시·뼈·키는 쓰지 않았다(`ref_fps_anim_phases.py` 로 단계별 시간과 손 경로만 수치화).
  - 박격포 등 특수 경우는 보류 목록에 적었다.
- **방식:** M4 의 1인칭(컨트롤 릭 + 구운 정적 팔)과 달리, 볼트·클립 같은 움직이는 부품 때문에 **팔+총 한 몸 스켈레탈 뷰모델**을 만들었다.
  - 공용 라이브러리 `Scripts/Blender/fpvm_lib.py`, `fpvm_lib2.py`(다른 무기도 사용):
    - `Furina_cm.fbx` 의 팔을 게임 1인칭 기록(`lyra_fp_arms_pose_a1.json`)의 카메라 기준으로 옮기고, 쇄골 자세도 게임과 같게 했다.
    - 팔 정점만 남기고 스키닝을 유지한다.
    - 팔꿈치 IK, 손목 회전 목표를 쓴다.
    - 손가락: 무기 표면에 닿을 때까지 관절 순서대로 굽힌다. 볼트 손잡이 쥐기·클립 집기·엄지 누르기는 손가락 모양을 고정하고 관통이 없는 손 방향을 탐색한다.
  - `Scripts/Blender/fpvm_kar98k.py -- pose|anim|close|export`:
    - Kar98k 볼트(`Material_005`)를 회전부와 덮개로 나눴다.
    - 마우저 클립(5발)을 뒤 브리지 클립 홈(y 14.3)에 꽂는다.
    - 클립 3개(30fps):
      - **Idle 4.0초:** 호흡.
      - **Fire 1.2초:** 반동 → 오른손이 볼트로 → 위(90°) → 뒤(8.8cm = 7.92×57 전장 8.2cm + 여유) → 앞 → 아래 → 손잡이로 복귀. 분당 10~15발 조준 사격에 맞춘 길이다.
      - **Reload 3.2초:** 총을 어깨에서 내려 몸 앞으로 → 볼트 열기 → 탄입대에서 클립 → 홈에 꽂기 → 엄지로 5발 눌러 넣기 → 볼트 닫기(빈 클립이 튀어나감) → 손잡이.
  - 위치: 푸리나 팔이 39cm 로 짧아 왼손이 닿는 범위 안에서 정했다. 왼손은 앞 리시버 링 바로 앞 앞받침(장전 때는 탄창 앞으로 미끄러짐)에 둔다. 장전 자세는 클립 홈이 화면 오른쪽 아래에 보이도록 탐색했다.
  - 정조준: 가늠쇠 끝(y -53.75)과 뒤 가늠자 홈(y -12.3, 높이 8.96)을 잇는 조준선이 화면 가운데에 오게 했다. 눈-뒤 가늠자 거리는 43cm(`fpvm_ads_calc.py` → `Data/fpvm_kar98k_ads.json`).
- **UE:**
  - `lyra_fpvm_import.py Kar98k kar98k` → `/Game/Furina/FPVM/Kar98k/SK_FPVM_Kar98k`, `AS_FPVM_Kar98k_<Idle|Fire|Reload>`.
    - UE5.8 Interchange 가 다시 가져올 때 애니를 빼먹어, 에셋을 지우고 애니만 따로 다시 가져온다.
    - 블렌더 FBX 가져오기가 장면 fps 를 24로 바꿔, 굽기 직전에 30으로 다시 맞춘다.
  - `lyra_fpvm_bp.py`(캐릭터 BP, 노드 `VM_*`):
    - 컴포넌트 `FurinaFPVM`(부모 FPCamera, 상대 변환 0).
    - 1인칭 + 무기 키 `kar98k` + 권총 아님이면 뷰모델을 보이고 M4(자식 포함)와 1인칭 팔·본체 팔을 숨긴다.
    - 사격 이벤트 앞에서 1.2초 안의 재발사를 막고 Fire 를 재생한다.
    - 재장전 시작 때 Reload 를 재생하고, 끝나면 Idle 로 돌아간다.
    - 정조준 가중치(21/s)로 정조준 변환을 보간한다.
  - 무기창 버튼이 캐릭터 변수 `FurinaPrimaryKey` 에 키를 넣는다(`SetStringPropertyByName`).
  - `lyra_fpvm_fix2.py`: 무기 마스터 재질에 '스켈레탈 메시에 사용'을 켰다(안 켜면 기본 회색 재질).
- **확인(PIE, `lyra_fpvm_probe.py v2`, 캡처 `Data/fpvm_v2_*.png`, 모음 `Data/fpvm_v2_sheet.jpg`):**
  - 키 설정 + 1인칭: 뷰모델 보임, M4 숨김, Idle 재생.
  - 사격: 잔탄 20→19. 0.54초 뒤 다시 쏘면 막힘(19 유지). 1.2초 뒤에는 다시 발사.
  - 재장전: 3.2초 애니가 게임 재장전(3초)과 함께 돈다. 클립과 탄이 화면 오른쪽 아래에 보인다.
  - 정조준: 볼트 축이 화면 가운데 세로선(y=0)에 온다.
  - 3인칭: 뷰모델 꺼짐, M4 다시 보임.
- **남은 것 / 한계:**
  - 탄은 숨긴 M4 의 총구에서 나간다. 조준점은 맞지만 총구 화염 위치가 Kar98k 총구와 다르다.
  - 탄약·HUD 는 M4(20발, AUTO) 그대로다. Kar98k 5발 내장 탄창으로는 아직 바꾸지 않았다.
  - 3인칭은 M4 그대로다(이번 요청은 1인칭만).
  - 엉덩이 사격 자세에서는 볼트 조작 손이 카메라 아래라 화면에 거의 안 보인다. 어깨 견착 위치 그대로라서 그렇다.
  - ZF39/ZF41/G43 등 나머지 무기 모션은 `Motion/DE_FP_MOTION_RESEARCH.md` 의 순서대로 남아 있다.
  - 실수로 엔진 기본 재질 `/Engine/EngineMaterials/WorldGridMaterial` 의 '스켈레탈 메시 사용'을 켜고 저장했다가 다시 끄고 저장했다. 동작은 원래와 같지만 엔진 설치 파일이 한 번 다시 저장됐다. Epic 런처에서 UE 5.8 '확인(Verify)'을 하면 원본 파일로 돌아간다.

## 조준경 재질 2차 + G43 1인칭(클립 2개 연속 장전) (2026-11-21)
- **조준경 재질(수집가 사진·설명 참고):**
  - ZF4 실물 사진(Legacy Collectibles): 몸체는 검은 블루잉에 일부가 닳았고, BLM 주조 마운트는 조준경보다 밝은 무광 회색이다.
  - ZF39(Hensoldt Dialytan)는 '전체 블루잉', ZF41 은 블루잉에 일부 검은 도장이다.
  - 조정 값(선형):
    - 조준경 관: ZF39 0.048, ZF41 0.044, ZF4 0.032. 블루잉이라 총의 금속(0.05~0.08)보다 약간 검게.
    - ZF4 마운트: 인산염 회색 0.17, 무광(0.62).
    - 렌즈: 어두운 푸른 유리(거칠기 0.04).
  - ZF39·ZF4 원본은 렌즈 없는 빈 관이라, 양 끝 0.8cm 안쪽에 내경에 맞춘 유리 원판을 넣었다(`de_scoped_build.py`). UE 캡처 `Data/de_scoped_s1_*.png`.
- **G43 1인칭** (`Scripts/Blender/fpvm_g43.py`, 출처는 `Motion/DE_FP_MOTION_RESEARCH.md` 2절):
  - 재질이 하나라서 볼트 캐리어(+왼쪽 장전 손잡이, 오른쪽 걸쇠, 볼트)는 연결 성분 경계로 떼어 `VM_Carrier`(뒤로 9.3cm)로 만들었다.
  - 애니:
    - **Fire 0.30초:** 반자동이라 반동과 캐리어 왕복만.
    - **Reload 5.9초:** 사용자 지정대로 클립 2개를 연속으로 넣는다.
      1. 왼손이 장전 손잡이를 당겨 연다.
      2. 클립 1: 꽂기 → 엄지로 누르기 → 뽑아 버리기.
      3. 클립 2: 같은 순서.
      4. 왼손으로 살짝 당겼다 놓아 닫는다.
  - 정조준: 뒤 가늠자 V홈(y -0.9, z 8.64)과 가늠쇠(y -54, z 8.96), 눈-가늠자 33cm.
- **캐릭터 BP 무기별 전환**(`lyra_fpvm_bp2.py`, 노드 `VW_*`):
  - 키가 바뀌면 다음을 키별 값으로 바꾼다: 메시, 애니 3개, 사격 간격(Kar98k 1.2초 / G43 0.25초), 재장전 길이, 정조준 위치·회전.
  - 키가 kar98k·g43 이 아니면 뷰모델을 끈다.
  - 메시를 바꾼 뒤 재질 슬롯 0~9 의 덮어쓰기를 비운다(`lyra_fpvm_fix4.py`). 원인: 게임 시작 때 프로젝트가 캐릭터의 모든 메시 컴포넌트에 동적 재질(MID)을 만들어 두어, G43 메시에 Kar98k 재질이 그대로 쓰였다. 처음엔 UV 문제로 의심했지만, UE 에서 다시 내보낸 FBX 의 UV 는 정상이었다.
  - `lyra_fpvm_import.py`: 재질을 새 `SkeletalMaterial` 로 넣도록 고쳤다(예전 방식은 저장되지 않았음). 팔 메시 UV 는 1개만 남긴다.
- **확인(PIE `lyra_fpvm_probe.py g3`, `Data/fpvm_g3_sheet.jpg`):**
  - G43 메시, 갈색 나무, 연속 사격(0.46초 간격 정상 발사).
  - 재장전 5.9초 동안 발사 막힘. 클립 1·2 와 탄이 화면 오른쪽 아래에 보인다.
  - 정조준 오프셋 적용.
  - 키를 kar98k 로 바꾸면 Kar98k 메시와 재질로 바뀐다. 3인칭 복귀 정상.
- **남은 것:**
  - 탄약·HUD 는 여전히 M4(20발)이다. G43 은 10발이어야 한다.
  - 클립 홈 위치(캐리어 앞면)는 모델 형상으로 정한 가정이다.
  - 반자동이지만 좌클릭을 누르고 있으면 0.25초마다 계속 쏜다(한 번 누를 때 한 발은 아직 아님).
  - G43+ZF4 조준경형 1인칭은 아직이다(조준경이 리시버 위를 덮어 클립 장전 동작이 달라질 수 있음).

## 1인칭 손 위치·내부 도색·낱발 각도 수정 + MP40·MP38·StG44 (2026-11-21)
- **손 보정 공통**(`Scripts/Blender/fpvm_lib2.py`):
  - `seat_hand`: 손바닥 가운데 피부 정점이 총 표면에 닿을 때까지 IK 목표를 손바닥 쪽으로 옮긴다(최대 3cm). 부호 없는 거리를 쓴다. 부호 거리는 모델 일부 면 법선이 안쪽이라 손을 9cm 밀어냈다.
  - `fold_sleeves`: 소매를 접는다. `palm_gap`: 진단용.
  - 손목 기록은 IK 목표가 아니라 실제 손목 뼈 위치를 쓴다.
- **Kar98k·G43:**
  - 대기 자세 위치는 각각 (32,-9,-12.5), (29,-9,-11.2)이다.
  - 왼손 자리는 팔 길이 37cm 안에서 자동으로 찾는다. 손바닥 방향은 맞은 면의 법선으로 정한다.
- **권총 3종:**
  - 손이 화면 밖에 있던 문제를 고쳤다. 총 위치는 (28,-6,-6.5)이고, 팔꿈치 방향 힌트와 소매 접기, `seat_hand`를 적용했다.
- **사격·재장전 때 부품 안쪽이 투명하게 보이던 문제:**
  - 무기 마스터 재질 `M_FurinaWeaponPBR`를 양면(two-sided)으로 바꿨다(`lyra_fpvm_reimport.py`).
  - 이 재질을 쓰는 모든 무기에 적용되므로, 앞으로 넣는 무기도 따로 처리할 필요가 없다.
- **낱발 탄 각도:**
  - 소켓 기준으로 90° 누워 있던 탄 방향을 고쳤다(`fpvm_loose_prop.py`, `Data/fpvm_round_fix.json`).
- **MP40·MP38·StG44** (`Scripts/Blender/fpvm_smg.py -- <key> <pose|grip|anim|export>`; 근거는 `Motion/DE_FP_MOTION_RESEARCH.md` 3·4절):
  - MP38: 접힌 채 모델링된 개머리판을 경첩(y 27) 기준 180°로 폈다.
  - MP40: 원본에 탄창이 없어서 MP38 탄창(같은 32발 탄창)을 끼웠다.
  - StG44: 어깨끈(Belt)을 제거하고, 총구 방향을 Z축 180°로 맞췄다(`de_stg44_fix.py`).
  - 왼손 받침:
    - MP38/MP40은 **탄창 하우징**을 쥔다. 당시 탄창을 쥐면 급탄 고장이 나서 하우징을 쥐도록 교육했다.
    - StG44는 탄창 앞쪽 총열 덮개 아래를 받친다.
    - 받침 자리가 팔 길이 안에 오도록 총의 앞뒤 위치를 자동으로 정한다. 조준선은 눈 아래 5cm다.
    - 처음에는 오른손 기준으로 배치해서 왼손이 닿지 않았고, 화면에 손이 보이지 않았다.
  - 애니메이션:
    - 대기 4초.
    - 사격 1발 주기: MP 500발/분, StG44 550발/분.
    - 재장전 2.85초: 탄창 빼기 → 탄입대 → 새 탄창 → 장전 손잡이.
    - MP38/MP40은 오픈볼트라서 쏠 준비 상태에서 노리쇠가 뒤에 있다.
  - UE 반영:
    - `lyra_fpvm_smg_bp.py`: 키별 분기, 연발, 32/32/30발, 사격 간격 변수 `FurinaFireInterval`.
    - `lyra_fpvm_smg_refresh.py`: 메시와 애니를 다시 가져오고 정조준 값을 갱신한다.
- **Kar98k 장전 자세 올림:**
  - 클립 홈 목표를 화면 아래 14°에서 4°로 바꿨다(`fpvm_kar98k.py` 의 `guide_down`). 그 결과 PIE에서 홈 높이가 -27°(화면 아래 끝, 낱발이 안 보임)에서 약 -15°가 되었다.
  - 다시 가져오기는 `lyra_fpvm_k98_refresh.py`로 했다.
- **확인:** PIE `lyra_fpvm_probe.py k_<key>_<n>`, 캡처는 `Data/fpvm_k_<key>_<n>_*.png`.
  - MP40/MP38/StG44:
    - 연발로 32→29, 30→27발이 줄고, 재장전하면 32/30발로 돌아왔다.
    - 허리·재장전·정조준 때 왼손이 화면에 보였다.
  - Kar98k(`k_kar98k_4`): 3발 남은 상태에서 `Loose2`로 2발을 넣어 5발이 되었다. 탄두는 총구 쪽을 향해 총과 나란히 들어갔다.
  - G43(`k_g43_2`): 3발 남은 상태에서 `Loose7`이 재생되었다. 탄 방향은 총과 나란했다.
  - 낱발 캡처 시간은 탄이 홈에 닿는 순간에 맞췄다. probe 는 캡처 한 번에 약 0.37초가 더 걸린다.
- **엔진 파일 주의:** 앞선 작업 중 엔진의 `WorldGridMaterial`이 한 번 수정되었다가 되돌려져 다시 저장되었다. Epic 런처에서 UE 5.8 **확인(Verify)**을 한 번 실행하는 것을 권장한다.

## 권총 세 자세 + 탄약 기반 총구 화염·연기·반동·흔들림 + 조준경 아래 총 보이기 (2026-11-21)
- **권총**(`Scripts/Blender/fpvm_pistols2.py`):
  - 세 자세:
    - 비조준: 한손으로 낮게, 안쪽으로 8° 기울임.
    - 견착: 한손으로 팔을 끝까지 뻗고 총을 안쪽으로 20° 기울임.
    - 정조준: 기존 두 손 자세라 정조준 변환은 그대로임.
  - 클립: 자세별 Idle/Fire 3쌍, 전환 6개(T_HS 등, 0.20~0.27초), 재장전(한손 → 두 손 → 한손).
  - 처음에는 비조준에서 손이 총에서 떨어졌다. 두 손 자세의 IK 목표가 이미 팔 길이 밖(팔을 끝까지 뻗은 자세)에 있었기 때문이다. 실제 손목 위치(WREST)를 기준으로 고쳤다.
  - BP 상태(노드 `HFX_`):
    - 원하는 자세 = 정조준 ? 2 : 견착(FurinaShoulder/Auto) ? 1 : 0.
    - 자세가 바뀌면 전환 애니를 재생하고, 그 시간 동안 사격을 막는다.
    - Idle/Fire는 `FurinaPAnims` 맵(키_클립)에서 고른다.
    - 재장전 중에는 비조준이다.
- **총구 소켓 `VM_Muzzle`:**
  - 1인칭 메시 11종 모두에 붙였다(뼈 VM_Gun, +Y 앞).
  - 위치는 `Scripts/Blender/fpvm_muzzle_points.py`로 구한 총구 둘레 중심이다. 소켓 오차는 0cm로 확인했다.
  - 소켓 속성은 파이썬에서 읽기 전용이라 `Set*PropertyByName`으로 넣었다.
- **사격 효과**(`Scripts/Unreal/lyra_hist_fx.py`, 수치 `Data/hist_fx.json`, 근거는 연구 문서 9절):
  - 1인칭 뷰모델이면 VM_Muzzle에서 `BP_HistFlash`, `NS_MuzzleFlash`, `BP_HistSmoke`를 만든다.
    - `BP_HistFlash`: M4 화염을 복제하고 소염기 꽃잎·별을 껐다. 크기와 길이는 표를 따른다.
    - `NS_MuzzleFlash`: Global Scale 0.2 × 크기.
    - `BP_HistSmoke`: 액터 크기로 농도, 지속, 크기를 넘긴다. 틱마다 Age를 재질에 넣는다.
  - 반동: 기존 배율 × 표 값(권총 한손 ×1.5).
  - 흔들림: 표 값을 쓰고, 정조준에서도 0.35배로 흔든다.
  - 연기에서 고친 것:
    - 재질 Time과 BP 시간 기준이 달라 연기가 안 보였다. 그래서 Age를 직접 넘긴다.
    - 크기 되돌리기를 BeginPlay 맨 뒤로 옮겼다. 순수 노드는 쓰는 순간 다시 읽혀서, 먼저 되돌리면 지속 시간이 1초가 됐다.
    - 연기 생성 실행선이 끊겨 있어 다시 이었다(`lyra_hist_fx_fix.py`).
- **조준경:**
  - 조준 중에 뷰모델 전체를 숨기지 않고, 조준경 몸통·유리·받침 슬롯만 `M_FPVM_Hidden`으로 가린다. 그래서 아래 총몸과 손이 보인다.
  - 렌즈 재질에 다음을 넣었다:
    - 흐릿한 접안부 테두리(4배 1.30R, ZF41 1.12R)
    - 가장자리로 갈수록 많은 먼지
    - 가는 기스와 닦은 자국 호
    - 가장자리 옅은 뿌연 기운
- **확인**(PIE `lyra_fx_capture.py`, `Data/fx_*.png`):
  - 권총 자세가 0/1/2로 바뀌고 애니가 바뀐다.
  - 11종 모두 사격 때 화염 액터와 연기 액터가 생긴다(연기 농도·지속 값 확인).
  - 조준경 조준 중에 `FurinaScopeTubeHidden`이 켜지고, 아래 총이 보인다.
- **보지 못한 것:** 반동·흔들림 각도 실측, 연사 시 연기 부하.

## 긴 총 견착 + 대기 자세 뒤로 + 탄창 재장전 구도 + 저격용 G43 탄창 교환 (2026-11-21)
- **견착**(우클릭 길게, `FurinaShoulder`/`FurinaShoulderAuto`):
  - 긴 총(소총·기관단총·조준경형): 정조준 가중치 목표를 0.6으로 둔다. 개머리판을 어깨에 붙이고 총을 조준선 쪽으로 60% 올리며, 4a(1−a)×3cm 만큼(약 2.9cm) 낮춘다.
  - 권총은 기존 견착 클립(팔 뻗고 기울임)을 그대로 쓴다.
  - 노드 `STC_`, 스크립트 `Scripts/Unreal/lyra_fpvm_stance.py`.
- **대기 자세 뒤로 당기기:** 긴 총의 비조준 기준 위치를 4cm 뒤로 옮겼다(`STC_Pull`). 정조준 위치는 그대로다.
- **탄창 재장전 구도**(MP40/MP38/StG44/저격용 G43):
  - Blender 자세 탐색 비용을 바꿨다(`fpvm_smg.py`, `fpvm_g43.py`):
    - 총을 조금 들어 올린다(위 5cm, 총구 10~30° 위).
    - 옆으로 35~55° 눕혀, 탄창 입구가 화면 가운데 약간 아래(세로 −10°)에 오고 아랫면 법선이 카메라를 향하게 한다.
  - 처음 75°는 총이 누워 보였고, 40°는 아랫면이 안 보였다.
  - 팔이 짧아 총이 눈앞을 가리는 문제를 보완하려고, UE에서 재장전 중 뷰모델 전체를 앞 9cm·아래 3cm로 민다(`FurinaRlOfs` 맵, `FurinaVMRlW` 보간).
- **저격용 G43**(`g43_zf4`):
  - 클립·낱발 대신 탄창 교환을 쓴다(사용자 지정, 조준경이 클립 홈 위를 가림).
  - 10발 탄창(성분 2개)을 `VM_Mag` 뼈로 떼어 ZF4 메시에 넣었다.
  - `AS_FPVM_G43_MagReload` 3.2초: 탄창 빼기 → 탄입대 → 새 탄창 → 장전 손잡이를 당겼다 놓기.
  - BP `HistoryReload_Amount` 뒤에 `STC_MagG43` 분기를 둬서, 한 번에 가득 채운다.
  - 일반 G43은 클립 두 개 그대로다.
- **확인**(PIE `lyra_fx_capture.py stance`, `Data/st_sh.jpg`, `Data/st_rl.jpg`):
  - 긴 총 견착 가중치 0.6, 권총 견착 자세 1.
  - 재장전 완료 시간: G43 ZF4 3.4초(탄창, 10발), 일반 G43 5.9초(클립).
- **남은 점:** G43 ZF4가 장전 손잡이(조준경 위 왼쪽)를 당길 때 왼팔이 약 0.5초 동안 화면을 크게 가린다.

## 다시 만들기 순서 (1인칭 무기, 2026-11-21 기준)
처음부터 다시 만들거나 모델·자세를 바꾼 뒤에는 아래 순서로 실행한다. 언리얼 스크립트는 모두 에디터를 끈 상태에서 아래처럼 띄워 실행한다.
`powershell -File Scripts/run_ue_probe.ps1 -ScriptPath <py> -Tag <태그> -Done <결과 json>`
이 명령은 열려 있는 에디터를 닫으니, 먼저 저장해야 한다.
1. **Blender 내보내기**(`Scripts/Tools/fpvm_export_all.sh`): `A`와 `B`를 병렬로 돌린 뒤 `C`를 돌린다.
   - A: Kar98k(+ZF39/ZF41), 권총 3종(`fpvm_pistols2.py`), 판처파우스트·판처슈렉(`fpvm_launchers.py`)
   - B: G43(+ZF4·`magreload`), MP40/MP38/StG44
   - C: 낱발 탄, 총구 위치(`fpvm_muzzle_points.py`), 정조준 변환(`fpvm_ads_calc.py all`), 연기 덩어리, 사격 효과 수치(`gen_hist_fx.py`)
   - 예전 `fpvm_pistols.py`(두 손 클립 3개)는 더 쓰지 않는다. 일괄 스크립트도 `fpvm_pistols2.py`로 바꿨다.
2. **언리얼 에셋 다시 가져오기**(`Scripts/Unreal/lyra_fpvm_reimport.py`, 결과 `Saved/FPVMReimport.json`):
   - 양면 재질, 낱발 탄, 소총·조준경 메시와 애니(G43 `MagReload` 포함), 권총(메시와 클립 13개), 기관단총을 가져온다.
   - 마지막에 모든 1인칭 메시에 `VM_Muzzle` 소켓을 다시 넣는다. 메시를 다시 가져오면 소켓이 빠질 수 있기 때문이다.
3. **캐릭터 BP 설치**(새 BP에 한 번만, 위에서 아래로). 각 스크립트는 자기 노드가 이미 있으면 건너뛴다.
   1. 기존 1인칭 기반: `lyra_fpvm_bp.py` → `lyra_fpvm_bp2.py` → `lyra_fpvm_fix1~4.py`
   2. 조준경·무기 선택·권총·탄수·재장전 분기: `lyra_fpvm_optics.py` → `lyra_fpvm_lens_view.py` → `lyra_fpvm_primary.py`
      - `lyra_fpvm_lens_view.py`는 화면 전체 렌즈다. 지금은 아래 7번이 가중치를 0으로 끈다.
   3. 기관단총: `lyra_fpvm_smg_bp.py`
   4. 사격 효과, 권총 자세 상태, 반동·흔들림, 조준경 슬롯: `lyra_hist_fx.py`
      - 이어서 보정 `lyra_hist_fx_fix.py`(권총 클립, 연기 실행선, 받침 슬롯)와 `lyra_hist_smoke_mat.py`(연기 재질·틱)를 돌린다.
   5. 긴 총 견착, 대기 4cm 뒤, 탄창 재장전 구도, 저격용 G43 탄창 교환: `lyra_fpvm_stance.py`
   6. 정조준 값 갱신(정조준 변환이 바뀌었을 때만): `lyra_fpvm_ads_update.py`
   7. 조준경 화면 속 화면, 연기 끄기, 권총 재장전 길이 2.5초·구도: `lyra_scope_pip.py`
      - 에셋만 다시 만들 때는 `lyra_scope_glass_flag.py`를 쓴다.
   8. 권총 탄피·견착: `lyra_pistol_cases.py` → `lyra_pistol_shoulder_reach.py`
   9. 대전차 화기 + 소총 영점: `lyra_launchers.py`(에셋·BP·HUD 모두) → `lyra_launchers_fix1.py`(적중 기록, 이름으로 부르는 영점 이벤트)
   10. 십자선 복구 + P38 슬라이드 정위치: `lyra_crosshair_p38.py`
   11. 병과 캐릭터 7종 + 무기창 병과 버튼: `lyra_class_fp_head.py` → `lyra_classes.py`(Blender `build_class_on_furina.py -- <키> build` 7종 먼저)
4. **확인:** `lyra_fx_capture.py <all|stance|v3|lch|zero|무기+무기>` → `Data/fx_*.png`
- **주의:**
  - 3번 스크립트들은 노드 이름(접두사 `HFX_`, `STC_`, `PIP_` 등)으로 서로를 찾아 이어 붙인다. 순서를 바꾸면 찾을 노드가 없어 실패한다. 이미 설치된 BP에 다시 돌리면 대부분 'already installed'로 건너뛴다.
  - 연기(`BP_HistSmoke`)는 7번에서 실행선을 끊어 꺼 두었다. 다시 켜려면 `HFX_NSShell` 다음에 `HFX_SmokeSpawn`을 다시 이으면 된다.

## 권총 탄창 재장전(고증) + 조준경 화면 속 화면 + 연기 끄기 (2026-11-21)
- **권총**(`fpvm_pistols2.py`): 모델의 실제 탄창 부품을 연결 성분으로 떼어 `VM_Mag` 뼈로 움직인다.
  - 부품: P38 몸통+바닥판, P08 나무 바닥 탄창 하나, PP 몸통+바닥판.
  - 다른 작업에서 넣었던 상자 모양 임시 탄창은 대체했다. P38 슬라이드 위치 보정 0.83cm는 유지했다.
  - 재장전 2.5초:
    - 총을 가슴 앞으로 들고, 안쪽으로 35° 눕혀 총 왼쪽 면과 손잡이 밑이 보이게 한다.
    - P38: 왼손이 힐 걸쇠를 밀며 탄창을 뽑는다.
    - P08/PP: 오른손 엄지로 단추를 누르면 탄창이 왼손 위로 떨어진다.
    - 이어서 탄입대 → 새 탄창 → 손바닥으로 밀어 넣기.
    - P38/PP는 슬라이드를 위에서 잡아 당겼다 놓는다. P08은 토글을 위·뒤로 꺾었다 놓는다.
  - 재장전 중에는 뷰모델을 앞 6cm·아래 2cm로 민다.
  - 근거는 연구 문서 5-2절.
- **조준경**(`lyra_scope_pip.py`):
  - 정조준 화면(가로 시야 60°)은 확대하지 않는다. 조준경 몸통과 총이 보이고, 유리 슬롯만 별도 장면 캡처를 화면 좌표로 붙인다.
  - 캡처 컴포넌트는 4배 16.4°, 1.5배 42.1° 두 개다. 시야 속성은 BP에서 바꿀 수 없어서 둘로 나눴다. 조준경을 조준하는 동안만 매 프레임 `CaptureScene`한다.
  - 뷰모델은 캡처에서 뺀다. 십자선, 먼지, 기스, 가장자리 그늘은 유리 재질(`M_FPVM_ScopeGlass_*`)에서 그린다.
  - 눈-접안부 거리: ZF39 15, ZF4 11, ZF41 30cm. 조준경이 작게 보여도 된다는 요청에 따랐다.
  - 유리 재질에 스켈레탈 메시 사용 표시가 없으면 기본 격자 재질로 보인다. 그래서 표시를 켰다.
- **연기:** 생성을 끊었다. 화염은 그대로다.
- **확인**(PIE `lyra_fx_capture.py v3`, `Data/v3_scope.jpg`, `Data/v3_prl.jpg`):
  - 연기 액터 0개, 화염 1개.
  - 조준경: 렌즈 안만 확대되고 십자선이 보인다.
  - 권총 재장전 완료 후 8발.
- **남은 점:** 권총 재장전 중 슬라이드를 잡으러 갈 때, 그리고 저격용 G43 장전 손잡이를 당길 때 왼쪽 소매가 화면을 크게 가린다.

## ZF41 렌즈 '이중 원' 수정 (2026-11-21)
- **원인 1(파이프라인):** `fpvm_receiver_interior.add_existing_optic`이 조준경 전체를 한꺼번에 Decimate로 줄였다. 그때 ZF41의 얇은 렌즈 원판(유리 9,506면)이 2,206면의 조각으로 뭉개졌다.
  - 이제 유리 면은 따로 떼어 두고 나머지만 줄인 뒤 다시 합친다. 모든 조준경에 적용된다.
- **원인 2(원본 모델):** 접안부 끝(y −1.75)에 안쪽 반지름 0.55cm의 금속 고리와 렌즈 조각 여러 장이 겹쳐 있다. 그래서 뒤에서 보면 고리와 가운데 구멍이 보였다.
  - 실제 ZF41처럼 렌즈 한 장이 관을 채워 보이도록, 끝면 바로 바깥(y −1.70)에 관 안쪽 반지름 0.80cm의 유리 원판(양면)을 덧댔다.
- **유리 재질:**
  - `M_FPVM_ScopeGlass_ZF41`의 렌즈 반지름 기준을 0.80cm로 고쳤다(전에는 추정 1.2cm).
  - 세 유리 재질 모두 양면으로 바꿨다.
- **처음 판단이 틀렸던 점:** 처음에는 "원본 유리가 원통 모양"이라고 답했다. 원본 합본 모델을 직접 재 보니 렌즈는 축을 향한 원판이었고, 첫 측정은 법선 길이를 맞추지 않은 측정 실수였다.
- **확인:** PIE `lyra_fx_capture.py zf41` → `Data/zf41_zoom2.png`. 렌즈 한 장 가득 1.5배 장면과 십자선이 보인다.
- **다시 가져오기:** 메시만 바꿀 때는 `lyra_zf41_reimport.py`(소켓 포함), 유리 재질만 바꿀 때는 `lyra_scope_glass_flag.py`를 쓴다.

## MP40 자체 탄창 사용 (2026-11-21)
- 원본 `MP40.fbx`에는 탄창(`Mag`, 정점 378)과 탄(`bullet`)이 총 옆에 45°로 따로 놓여 있다. 정리 스크립트(`de_weapons_build.py`)가 이 둘을 빼서, 지금까지는 MP38 탄창을 옮겨 썼다.
  - 그 탄창의 가운데(y −13.0)가 하우징 입구 가운데(y −14.19)보다 1.2cm 뒤라서, 재장전 때 엉뚱한 곳에 꽂혔다.
- `Scripts/Blender/de_mp40_mag.py`:
  - 정리 변환(최장축 → Y, 둘째 → Z, 실제 길이 0.833m, 가운데 맞춤)을 총 부품만으로 다시 계산했다. 정리본 경계 상자와의 오차는 0.000002cm였다.
  - 같은 변환을 탄창에 적용한 뒤, 탄창 축으로 세웠다: 긴 축은 위, 탄두 쪽은 총구 방향.
  - 하우징 입구 가운데(x −0.34, y −14.19)에 맞추고, 위끝을 총열 축 아래 1.3cm까지 밀어 넣었다.
  - 탄창 크기는 2.2 × 4.0 × 24.1cm이고, 결과는 `FBX/Weapons/SM_DE_mp40_mag.fbx`다.
- `fpvm_smg.py`: MP40은 이 탄창을 쓴다. 재질은 같은 MP40 아틀라스다.
  - 왼손 하우징 잡는 자리가 앞으로 옮겨져서, 총 위치(x 9.6 → 8.1)와 정조준 값이 다시 계산됐다.
- 다시 가져오기: `lyra_fpvm_smg_refresh.py mp40`. 메시, 애니, 정조준 값, `VM_Muzzle` 소켓을 함께 처리한다.
- 확인: PIE `lyra_fx_capture.py mp40rl`(`Data/mp40_rl_zoom.jpg`)에서 탄창이 하우징에서 빠졌다가 같은 자리에 꽂히고, 재장전 뒤 32발이 됐다.
- 다시 만들기 순서(1번 Blender)의 B줄 앞에 `de_mp40_mag.py`를 한 번 돌린다. 원본이 바뀌지 않는 한 결과 파일을 그대로 쓴다.

## 권총 탄피 배출 고증 (2026-11-21)
- **기반:** 다른 작업이 넣어 둔 배출을 그대로 쓴다.
  - `lyra_fpvm_pistol_reload_cases.py`: `PistolCase_` 노드, `BP_FPVM_9mmCase`/`BP_FPVM_32Case`, 9mm·.32 탄피 메시.
  - 이 배출은 모든 권총에서 탄피가 카메라 기준 오른쪽·앞·위로 튀었다.
- **고증 보정**(`Scripts/Blender/fpvm_pistol_ejection.py` → `Data/fpvm_pistol_ejection.json`, `Scripts/Unreal/lyra_pistol_cases.py`):
  - 배출구 = 총열 뒤끝(총구 + 총열 길이 P38 125 / P08 100 / PP 98mm) + 0.8cm.
  - 소켓 `VM_CaseFX`를 그 자리로 옮겼다. 소켓 +X가 배출 방향이다.
    - P38: 슬라이드 왼쪽 → 왼쪽(조금 위·뒤)
    - P08: 토글 위 → 위(조금 오른쪽·뒤)
    - PP: 슬라이드 오른쪽 → 오른쪽(조금 위·뒤)
  - 생성 회전을 카메라 회전에서 소켓 회전으로 바꿨다(`PistolCase_SocketRotation`).
  - 탄피 초기 속도는 소켓 +X로 3.5m/s다(`TFPCaseDirection` = 350,0,0).
- **확인**(PIE `lyra_fx_capture.py case` / `caseslow`(0.1배속)):
  - 발사 직후 속도(카메라 기준 cm/s, +y = 오른쪽): P38 (−123, −311, 69) 왼쪽, P08 (−104, 61, 295) 위, PP (−46, 271, 181) 오른쪽.
  - 0.1배속 캡처에서 P38 탄피가 총 왼쪽으로 나가는 것을 확인했다(`Data/caseslow.jpg`).
- **주의:** `lyra_fpvm_pistol_reload_cases.py`를 다시 돌리지 말 것.
  - 이 스크립트는 예전 상자 모양 임시 탄창(`MagazineDisplay`)과 이전 클립을 기대한다.
  - 다시 돌리면 실제 탄창 재장전 메시·클립을 덮어쓰거나, 탄창 슬롯을 찾지 못해 실패한다.
  - 탄피만 다시 만들 때는 그 안의 `prepare_cases()`만 쓰고, 이어서 `lyra_pistol_cases.py`를 돌린다.

## 권총 견착: 뻗은 팔 부각 (2026-11-21)
- **사용자 지정:** 견착은 손을 뻗는 자세이니 뻗은 팔과 멀어진 손·권총이 두드러지게.
- **배경:** 팔 길이 39.2cm 중 견착 자세가 이미 38.3cm를 쓰고 있어서 팔을 더 펼 수 없었다.
- **방법**(`Scripts/Unreal/lyra_pistol_shoulder_reach.py`, 노드 `PSR_`):
  - 권총 견착일 때(정조준 아님) 뷰모델 전체를 앞 12cm·아래 1cm로 민다.
  - 가중치 `FurinaVMShW`는 0.033초마다 보간한다(속도 10).
  - 대기 기준 위치 = 기존(`STC_ALoc`) + (12, 0, −1) × 가중치.
- **결과:** 손과 권총이 눈에서 약 33cm로 멀어지고, 소매를 포함한 아래팔이 화면 아래에서 가운데까지 길게 보인다.
- **확인:** PIE `lyra_fx_capture.py psh`, `Data/psh_compare.jpg`(위 = 전, 아래 = 후).
- **다시 만들기 순서:** 3번 BP 설치의 7번(`lyra_scope_pip.py`) 다음에 `lyra_pistol_cases.py` → `lyra_pistol_shoulder_reach.py`를 돌린다.

## 판처파우스트·판처슈렉 + 휠 영점 + 소총 영점 300/200 m (2026-11-21)
- **사용자 지정:**
  - 판처파우스트는 탄두가 날아가므로 관과 탄두를 나눈다.
  - 정조준 영점은 마우스 휠로 올리고 내린다. 비조준 때는 가장 낮은 영점을 쓴다.
  - 판처슈렉은 파일 안의 탄두(로켓)를 쓰고 고증을 지킨다.
  - 저격총 정조준 영점은 300 m, 나머지는 특이한 경우가 아니면 200 m다.
- **근거:** `Motion/DE_FP_MOTION_RESEARCH.md` 7, 7-1, 10절. 당시 자료는 TM-E 30-451(1945)이다.
- **Blender**(`Scripts/Blender/fpvm_launchers.py -- <panzerfaust|panzerschreck> <pose|ads|anim|export>`):
  - 판처파우스트(Pzf 60):
    - 관 입구(y −27.6) 앞 덩어리(탄두·꼬리 마개·Korn)를 `VM_Warhead` 뼈로 떼었다. 가늠자 판은 `VM_Leaf`(접기·세우기)다.
    - 가늠자 구멍 30/60/80 m는 탄두 45 m/s 포물선 발사각(4.18°, 8.45°, 11.40°)에 맞게 판 높이를 다시 매핑했다. 원본은 30 m 구멍이 Korn보다 낮았다.
    - 정조준 화면 가운데에서 Korn 끝이 V 홈 안에 보인다(`Data/lch_pzf_korn.jpg`).
  - 판처슈렉(RPzB 54):
    - 원본은 총구가 +Y라 Z축으로 180° 돌렸다. 원본 안 로켓 면(`Rocket_001`)은 지우고, 단품 로켓 모델(65 cm)을 같은 자리에 `VM_Rocket` 뼈로 넣었다.
    - 방아쇠 앞 사각 고리는 장전 레버(`VM_Lever`)로 정했다. 조준점은 방패 창(사수 왼쪽) 가운데다.
  - 영점별 정조준 변환은 같은 영점에서 관을 발사각만큼 든 자세다. `Data/fpvm_launchers_ads.json`에 쓰고, `fpvm_ads_calc.py all` 이 `fpvm_view_alignment.json`에 `<키>_0~2`로 합친다.
  - 애니 4개:
    - Idle 4 s, IdleEmpty 4 s(탄두·로켓 없음).
    - Fire: Pzf 1.0 s, Pzs 0.8 s. 무반동이라 작게 들썩인다.
    - Reload: Pzf 3.0 s(빈 관 내림 → 새 관 → 가늠자 세움), Pzs 4.0 s(견착 유지 → 로켓이 뒤에서 들어와 걸림 → 배선·신호 흔들림 → 왼손 장전 레버).
  - 판처파우스트 발사체 메시 `FBX/FPVM/SM_FPVM_PzfWarhead.fbx`: 탄두에 관 안에 있던 꼬리대와 날개 4장을 단순한 형상으로 붙였다.
- **언리얼**(`Scripts/Unreal/lyra_launchers.py`, 노드 접두사 `LCH_`):
  - 에셋:
    - `/Game/Furina/FPVM/<PANZERFAUST|PANZERSCHRECK>/`에 메시와 애니 4개를 넣었다.
    - 소켓: `VM_Muzzle`(관 앞 끝), `VM_Launch`(발사 위치), `VM_Rear`(관 뒤 끝, 후폭풍).
  - 발사체 `/Game/Furina/FP/BP_FurinaPzfWarhead`(45 m/s), `BP_FurinaPzsRocket`(110 m/s, 연기 꼬리):
    - `BP_FurinaBullet`을 복제했다. 직격 피해 300(GAS)은 그대로 쓰고, 공기 저항과 도탄은 껐다.
    - 적중하면 폭발(`NS_Grenade_Explosion`)과 소리가 나고, 반경 2.5 m 안 다른 폰에 120 피해를 준 뒤 사라진다.
    - 쏜 사람(Owner)과는 부딪히지 않는다.
  - 캐릭터 BP:
    - 무기 키 분기: 기관단총 다음, 권총 앞. 탄은 1발이다. 장착할 때 탄이 없으면 빈 대기 애니를 쓴다.
    - 사격: 소총탄 대신 `VM_Launch`에서 발사체를 낸다. 방향 = 카메라 + 위로 발사각(정조준 = 고른 영점, 비조준 = 가장 낮은 영점). 쏜 뒤 대기 애니는 빈 것이고, 관 뒤 끝에 후폭풍 화염이 난다.
    - 재장전: 재장전 애니가 끝나면 탄이 있는 대기 애니로 돌아온다.
    - 휠: 입력 `IA_FurinaZeroUp/Down`(MouseScrollUp/Down, `Default_IMC`)으로 영점 칸 0~2를 바꾸고 정조준 변환을 교체한다. 정조준 보간 때문에 관이 부드럽게 들린다. 같은 동작을 커스텀 이벤트 `FurinaZeroUp/Down`으로도 부를 수 있다.
  - HUD: 대전차 화기면 탄 수 옆에 `ZERO 60m`를 표시한다.
- **소총 영점**(같은 스크립트):
  - 정조준 조준점 = 카메라 + 카메라 앞 × 영점 거리. 예전에는 숨긴 3인칭 소총 가늠자에서 50 m였다.
  - 영점 거리: 저격총(`kar98k_zf39`, `kar98k_zf41`, `g43_zf4`) 300 m, 나머지 200 m.
  - 권총은 특이한 경우로 보고 25 m로 정했다. 고정 가늠자의 근거리 권총이라 200 m 영점은 맞지 않는다고 판단했다.
  - 3인칭 M4는 예전 50 m를 그대로 둔다. 낙차 보정 상한은 200 → 400 m로 올렸다.
- **확인(PIE):**
  - `lyra_fx_capture.py lch`(`Data/lch_pzf_pie.jpg`, `lch_pzs_pie.jpg`):
    - 영점 칸이 0 → 1 → 2(2에서 멈춤) → 1로 바뀌고, 정조준 회전 차이가 4.27°·2.95°(Pzf), 1.17°·1.17°(Pzs)다.
    - 쏘면 탄 1 → 0이 되고, 대기 애니가 빈 것으로 바뀐다.
    - 탄두 발사각 측정값: 정조준 60 m에서 8.4°(목표 8.45°), 비조준에서 약 5.0°(목표 4.18°). 0.8° 차이는 흔들림 때문으로 추정한다.
    - 폭발, 재장전 뒤 탄 1발이 된다.
  - 실제 마우스 휠(화면 조작, `lchlive`): 0 → 1 → 2 → 2 → 1 → 0으로 바뀌었다. 정조준 시야각 60°는 휠로 바뀌지 않았다.
  - `zero`(쏜 순간 탄 방향, 카메라 기준 위로):
    - MP40(200 m) 0.088°(계산 0.089°), P38(25 m) 0.145°(계산 0.153°).
    - Kar98k(200 m) 0.109°, 저격총(300 m) 0.149°(계산 0.118°).
    - 0.02~0.03° 차이는 원래 있던 탄 퍼짐(같은 기록에서 좌우 ±0.03°)으로 추정한다.
- **남은 것 / 한계:**
  - HUD의 `ZERO` 글자는 고해상도 캡처에 HUD가 찍히지 않아 화면으로 확인하지 못했다.
  - 판처슈렉 가늠쇠 눈금 모양은 자료가 없다. 장전 레버 부품과 장전 순서도 추정이다.
  - 탄두와 로켓은 기본 맵의 포털 충돌 캡슐(`B_TeleportToUserFacingExperience`)에도 맞아 터진다.
  - 판처파우스트 비조준은 손이 화면 아래라 거의 안 보인다.
  - 판처슈렉 방패가 비조준에서도 화면 아래 절반을 가린다(실물 크기).
  - 3인칭은 아직 M4다.

## 십자선 복구 · P38 슬라이드 정위치 (2026-11-22)
- **에디터를 끄지 않고 실행:** `python Scripts/Tools/ue_remote_run.py <스크립트.py> [인수]` 로 열려 있는 에디터에 파이썬을 보낸다(프로젝트 설정 `bRemoteExecution=True`). PIE 중이면 에셋 스크립트가 'End PIE first' 로 멈춘다.
- **십자선(`lyra_crosshair_p38.py`):** 독일 무기(1인칭 뷰모델)를 들면 `lyra_fpvm_primary.hide_weapon_hud` 가 무기 HUD 를 통째로 막아 조준경이 아닐 때 아무것도 그리지 않았다. `ScopeView_HasGlass` 의 else → `LCH_HudDraw`(영점 글자) → `K2Node_FPAH_IsAds`(정조준이 아니면 십자선)로 이었다. 옛 M4 탄수 틀은 계속 숨김. 확인: PIE 에서 M4·P38 비조준 화면 가운데 십자선(`Data/look_p38_hip.png`).
- **P38 슬라이드:** 원본 모델이 슬라이드를 3.31cm 당긴(후퇴) 상태였다(슬라이드 앞 y -1.74 > 프레임 앞 -5.05, 뒤끝이 공이치기를 덮음). `fpvm_lib.seat_p38_slide` 가 불러올 때 슬라이드에 붙은 부품(윗몸·가늠자·안전장치·핀)을 앞으로 옮긴다(예전 0.83cm 보정 두 곳은 지움). 가늠자가 앞으로 간 만큼 눈-가늠자 거리를 35.31cm 로 늘려 정조준 화면 구도는 그대로(`fpvm_ads_calc.py`). P38 메시·클립 13개·`VM_Muzzle`/`VM_CaseFX` 소켓·정조준 상수를 다시 넣었다.
  - 참고: P38/P08 메시의 소켓 목록에 같은 이름이 여러 번 들어 있다(전부터 있었고 다시 가져오며 늘었다). 첫 번째 것이 쓰이므로 동작에는 문제없다.

## 제3제국 병과 캐릭터 7종 (2026-11-22)
- **받은 모델**(`Downloads/제3제국/<병과> <키>cm.zip`, 원신 MMD PMX, 키 = 의상 포함 발바닥~맨 위, 사용자 지정): 장교 진 173, 보병 미카 165, 돌격병 케이아 184, 대전차병 클레 125, 중화기병 노엘 166, 저격수 엠버 163, 기갑병 유라 171.
  - 원본 사본: `FBX/Classes/source/<키>/`(압축 안 이름이 Shift-JIS 라 그 인코딩으로 풀었음). **사용 규칙: 재배포·상업 이용·18금 등 금지(miHoYo 저작권)** → 공개 저장소에 올리지 말 것.
- **Blender `build_class_on_furina.py -- <키> [build|preview]`** → `FBX/Classes/<키>_cm.fbx`, `Data/class_<키>_build.json`, 미리보기 `Data/class_<키>_*.png`, `class_all_rest_front.jpg`.
  - PMX 는 `Scripts/Blender/pmx_reader.py`(직접 만든 PMX 2.x 파서)로 읽는다(Blender 5.2 에 MMD 가져오기 없음). (x, z, y) 축 변환 + 면 감김 뒤집기.
  - 원래 MMD 가중치를 표준 뼈 이름(下半身·上半身·首·頭·左腕·左ひじ·左手首·左足(D)·指… ) → 푸리나 뼈로 합침. 머리카락·치마 등 물리 뼈는 가장 가까운 조상 뼈로(흔들림 없음).
  - 관절(몸 21 + 손가락 30)은 각 모델 PMX 뼈 위치, 뼈 방향은 푸리나와 같게 돌려 굳힘 → 언리얼 `SK_Furina_Skeleton` 의 이 51개 뼈 이동 리타깃 = Skeleton, Hips = AnimationScaled 로 푸리나 애니메이션을 각 몸 비율로 재생.
  - 숨은 재질(알파 0)과 MMD 반사 덧칠 층(이름 끝 `+`, spa/sph 텍스처)은 뺀다. 불투명으로 그리면 머리가 검게 덮였다(미카 `髮+`).
- **언리얼 `lyra_classes.py [import|retarget|pawn|menu|delete|all]`**(열린 에디터에 `ue_remote_run.py` 로 보냄): `/Game/Furina/Classes/<Key>/SK_Class_<Key>`, `T_<Key>_NN`(색 텍스처로 고정: 유라 푸른 옷 텍스처가 노멀맵으로 자동 판정돼 연두색으로 보였음), `MI_<Key>_MatNN`(부모 `M_Furina_Opaque`).
  - 캐릭터 BP: 이벤트 `FurinaLookOfficer/Infantry/Assault/AntiTank/Heavy/Sniper/Armor` = 메시 교체 → 재질 덮어쓰기 비우기(라이라가 시작할 때 현재 재질로 만든 동적 인스턴스가 남지 않게) → `FurinaLook` 저장. 1인칭이고 외형이 푸리나가 아니면 `Head` 뼈 숨김(`lyra_class_fp_head.py`).
  - **기본 외형 = 보병(미카)**. 푸리나는 에셋(`SK_Furina` 등)과 이벤트 `FurinaLookFurina` 만 남기고 버튼은 없앴다(비활성, 나중에 쓸 때 이 이벤트를 부르면 됨).
  - 무기창(Tab) '병과 (외형)' 줄: 장교·보병·돌격병·대전차병·중화기병·저격수·기갑병 7개 모두 활성(툴팁에 캐릭터·키).
  - 받은 군인 모델(`ww2-german-wehrmacht-soldier`)은 에셋·원본·스크립트 모두 지웠다.
- **확인(PIE):** 시작 = 보병, 7종 이벤트로 3인칭 모습(`Data/class_pie_sheet.jpg`), 1인칭 머리 숨김(`Data/cls_fp.jpg`). 경계 상자 높이: 장교 173.2, 보병 164.6, 돌격병 184.1, 대전차병 125.0, 중화기병 166.3, 저격수 163.1, 기갑병 171.2 cm.
  - 실제 마우스로 병과 버튼을 누르는 것은 확인하지 못했다(이벤트 직접 호출로 확인).
  - 한계: 1인칭 뷰모델 팔은 여전히 푸리나 소매. 치마·머리카락 물리 흔들림 없음(조상 뼈에 붙음). 죽고 다시 나오면 기본(보병). 3인칭 총 잡는 손은 푸리나 팔 길이 기준 컨트롤 릭이라 캐릭터별로 어긋날 수 있다. 표정(모프)은 가져오지 않았다.

## 조준경 정조준 감도 (2026-11-22)
- **`lyra_scope_sensitivity.py`:** 조준경으로 정조준할 때(`FurinaScopeActive`: 조준경 무기 + 정조준 + 재장전 아님) 마우스 회전량 × 1/배율. 렌즈 속 화면(시야각 2·atan(tan30°/배율))이 기존 정조준(60°)과 같은 속도로 움직인다. ZF39·ZF4(4배) 0.25배, ZF41(1.5배) 0.667배, 조준경 없는 무기와 비조준은 그대로.
  - 노드: `SENS_One`, `SENS_InvZoom`, `SENS_Scale`, `SENS_MulYaw`/`SENS_MulPitch`(IA_Look → AddControllerYaw/PitchInput 의 Val 앞).
  - 확인(PIE): Kar98k ZF39 정조준 → 배율 4, 감도 0.25 / ZF41 → 1.5, 0.667 / Kar98k(가늠자) → 1.0. 실제 마우스로 움직여 본 것은 아니다(변수 값으로 확인).

## 병과 캐릭터 1인칭 팔 · 3인칭 몸 비율 · 대일본제국 7종 · 판처파우스트 60 재질 (2026-11-22)
- **1인칭 팔(14종):** 리더 포즈로 별도 팔 메시를 따라가게 하는 방식은 이 뷰모델에서 팔이 축소·엇나가 버림. `fpvm_lib.class_arm_objects` 가 모든 1인칭 무기 메시(14개)에 병과 캐릭터 14종 팔을 같은 팔 뼈대로 함께 넣는다(재질 슬롯 `CA<Key>_MatNN`, 무기 스크립트 5개가 load_arms 직후 만들고 메시 내보낼 때 같이 선택, `fpvm_receiver_interior.export_mesh_only` 도 포함).
  - 캐릭터 팔은 뼈마다 '푸리나 관절 + (정점 - 캐릭터 관절) × 길이비'로 1인칭 팔 길이에 맞춤(무기 쥐는 손 위치 그대로). 큰 소매는 팔 축에서 5cm(위팔)·3.8cm(아래팔, 손목 앞 소맷부리 포함) 밖을 당김(`SLEEVE_MAX_CM`, 손가락 제외).
  - 언리얼: `lyra_class_fp_arms2.py`(슬롯마다 `MI_<Key>_MatNN`, 시점 갱신마다 (외형 + 무기 메시)가 바뀌면 지금 외형 팔 슬롯만 보이고 나머지·푸리나 팔은 `M_FPVM_Hidden`, 이 재질은 스켈레탈 메시 사용을 켬). 무기 메시를 다시 가져온 뒤에는 `lyra_class_fp_arms2.py slots` 와 `lyra_pzf60_material.py` 를 다시 실행.
  - 시작: BeginPlay → `LOOK_StartLook`(보병) → 타이머(`FMG_Timer`). 정리 중 이 연결이 끊겨 타이머가 멈췄던 것을 복구.
- **3인칭 몸 비율(수정·확인):** 원인 = 애니메이션 뼈 이동이 푸리나 길이로 풀리고, `CR_FurinaSecondary` 의 다리·팔·손가락 IK 길이가 푸리나 값(39.40/41.22, 21.14/18.02cm 등)으로 고정 -> 클레는 다리가 늘어 무릎이 굽고 발이 바닥 아래로.
  - 캐릭터마다 자기 뼈대 `SKM_<Key>_Skeleton`(푸리나 뼈대와 호환, Hips = AnimationScaled; `lyra_class_skeletons.py`), ABP 컨트롤 릭 노드 'Set Initial Transforms From Mesh' 켬(`lyra_abp_cr_refpose.py`).
  - 컨트롤 릭 맨 앞(`CL_` 노드): 몸·손가락 뼈 50개를 '부모 지금 위치 + 부모 지금 회전 × 부모 기준 회전⁻¹ × (자식 기준 위치 - 부모 기준 위치)'로(이 계층은 Hips 에 100배 크기가 있어 로컬 값을 쓰면 몸이 접힘), IK 길이 = 기준 자세 관절 거리, 경사 게이트 입력 = 엉덩이 높이 / (메시 Hips 높이 / 92.76). 엉덩이 높이 자체는 뼈대의 AnimationScaled 에 맡김(컨트롤 릭에서 또 곱하면 두 번 줄어듦).
  - 순서: `lyra_cr_class_lengths.py` → `lyra_cr_class_iklen.py` → `lyra_cr_class_local_fix.py` → `lyra_cr_class_global_fix.py`(자동 재컴파일 끄고 한 번에; 켠 채로는 에디터가 멈춤) → `CL_HipsScaled.Factor` = 1. 보정 전 백업: 스크래치 `CR_FurinaSecondary.before_classlen.uasset`.
  - 확인(PIE, 서서): 발끝 높이가 모든 캐릭터 7~13cm(푸리나 8.4)로 같은 바닥, 클레 엉덩이 63.7·머리 95cm 등 각자 비율(`Data/legs_sheet.jpg`).
- **대일본제국 7종:** 장교 아야토 187, 보병 토마 186, 돌격병 헤이조 166, 대전차병 요이미야 163, 중화기병 라이덴 177, 저격수 사라 178, 기갑병 이토 190(의상 포함). Blender `build_class_on_furina.py -- jp_<병과>`(PMX 가 여러 개면 가장 큰 것 = 캐릭터), 언리얼 `lyra_classes_jp.py`(자기 뼈대 메시 `SKM_Jp*`, 이벤트 `FurinaLookJp*`, 무기창 '병과 (외형) - 대일본제국' 줄 `Look_8..14`). 미리보기 `Data/class_jp_*.jpg`, 1인칭 `Data/fparms_jp_sheet.jpg`.
- **판처파우스트 60:** 받은 `panzerfaust-60.zip` 의 모델은 이미 1인칭 판처파우스트에 들어가 있던 파일과 같음(`fpvm_panzerfaust60.py`, 체크섬 동일). 비어 있던 재질 슬롯 `Panzerfaust60Surface` 에 받은 텍스처 4장으로 `MI_DE_panzerfaust60`(부모 `M_FurinaWeaponPBR`)을 만들어 1인칭 메시와 발사체 탄두에 지정(`lyra_pzf60_material.py`).
- **머리카락·망토 흔들림(남음):** `pmx_reader.py` 가 강체·조인트를 읽음(물리 뼈 34~275개/캐릭터). 이 뼈들을 캐릭터 뼈대에 살리고, 메시별 물리 에셋 + ABP 의 Rigid Body 노드(또는 컴포넌트 물리)로 흔들림을 붙이는 단계가 남음.

## 권총 그립 재작성 + 정조준 한 손 (2026-11-22)
- **문제(6방향 렌더로 확인):** 손이 손잡이 아래쪽(탄창 바닥 근처)을 쥐고 손가락이 탄창 밑을 감쌌으며, 검지도 손잡이를 감싸 방아쇠울 밖에 있었다. 원인은 손바닥을 손잡이 중간에 두고 손가락 방향을 거의 아래(-z 0.88)로 잡은 것과 검지를 다른 손가락처럼 계산한 것.
- **수정(`fpvm_pistols2.py`, `GRIP_R`):**
  - 손바닥: 손잡이 윗부분 오른쪽 면(높은 그립). 손가락: 손잡이 축(단면 두 높이로 계산)에 수직인 앞쪽 -> 가운데·약지·새끼가 방아쇠울 아래 손잡이 앞면을 감쌈, 엄지는 프레임 왼쪽 면.
  - 검지: 감싸기 계산에서 빼고, 지문 면(끝마디 60%)이 방아쇠 앞면 목표에 닿는 관절 각 + 첫마디 좌우 벌림을 탐색(손끝이 방아쇠 앞으로 0.4cm 넘게 나가면 벌점). 결과 빗나감: P38 0.14cm, PP 0.27cm, P08 0.63cm.
  - P08 은 손잡이가 크게 눕고 메시가 성겨(z -1~-2 에 정점 없음) 단면 대신 옆모습에서 읽은 값(손잡이 중심 y 4.6, 축 (0, 0.57, -0.82))과 손가락 방향을 수평 쪽으로(`flat` 0.8).
  - 정조준(A)도 오른손 한 손(사용자 지정): 왼손은 쉬는 자세, 오른손 손가락은 비조준과 같은 그립.
- **검증:** `blender ... fpvm_pistols2.py -- <p38|p08|pp> gripcheck` -> `Data/fpvm_<key>_grip_<H|A>_<left|right|top|bottom|front|back>.png`, 묶음 `Data/grip_all_H.jpg`, `grip_all_A.jpg`. 게임 화면 `Data/pgrip_game.jpg`(비조준/정조준).
- 언리얼 반영: `lyra_hist_fx.pistols` + `sockets`(권총만), `lyra_pistol_cases.py`, `lyra_class_fp_arms2.py slots`, `lyra_fpvm_ads_update.py`.
- 참고: 에디터가 엔진 플러그인 단언(`AsyncGameplayMessageSystem` OuterWorld.IsValid)으로 한 번 충돌해 다시 켰다(작업 스크립트와 무관).

## 손·손가락 ↔ 총 정합 1cm 이내 작업 (2026-11-22)
- **측정 도구:** `Scripts/Blender/fpvm_grip_audit.py -- <SK> <클립> [render] [hand=Body|Arms_<Key>] [frames=N]` — 손가락 마디(가운데·끝)·손바닥의 총 표면 틈/파고듦(안·밖은 6방향 광선, 면 법선은 모델마다 뒤집혀 있어 안 씀), 손목-총 흔들림, 6방향 렌더(`Data/audit_<SK>_<손>_<R|L>_<방향>.png`, 묶음 `Scripts/Tools/sheet6.py`). 전체: `Scripts/Tools/grip_audit_all.sh [render]`(무기 10 × 손 15, `PAIRS_OVERRIDE` 로 일부만) → `grip_audit_summary.py` → `Data/grip_audit_summary.json`.
- **찾은 원인과 수정:**
  1. 병과 팔(Arms_*)이 휴식 자세 굳히기에서 빠져 손목 10~40cm·손가락 4~11cm 어긋남(게임에서 '흐느적') → `fpvm_lib.bake_arms_rest(arm, [body] + CA)`(소총·기관단총·대전차 4개 스크립트). 병과 팔 UV 1개로.
  2. 손가락 자동 쥐기가 뼈 선만 보고 손끝이 닿으면 멈춰 손가락이 펴진 채 남음 → 피부 정점 기준 풀이 `fpvm_grip.py`(세 관절 격자+좌표 하강, 파고듦 벌점, 지나가는 길 검사). `fpvm_lib2.grip_fingers` 가 자동으로 씀(`FPVM_GRIP_SEG=1` 이면 예전 방식). 뿌리 관절 한계 95°, 엄지 35/45/50°.
  3. 소총·기관단총·판처슈렉 오른손 검지 → 방아쇠울 자동 찾기 `fpvm_grip.trigger_target`(손가락 벌림 `<뼈>@spread` 키, 손끝 넘어감 벌점). 판처파우스트는 방아쇠울이 없어 제외.
  4. 기관단총 오른손을 2cm 올리고 손가락을 손잡이 축에 수직으로(`SPEC fR`), 왼손 MP40 `hold_dz` 5.5 / MP38 3.5·`hold_dy` -0.75, G43 왼손 `yL` 8.0(모두 측정으로 고름).
  5. 애니 굽기 때 IK 목표 보정 3번 → 12번(손목이 1.5~2.5cm 덜 닿았음, 판처슈렉에서 확인).
  6. **1인칭이 푸리나 손:** 시작 무기가 비어 예전 M4 + 푸리나 전용 1인칭 팔이 나왔음 → BeginPlay 에서 무기 키가 비어 있으면 `kar98k`(`Scripts/Unreal/lyra_default_primary.py`, 노드 `DEFW_*`). 독일·일본 무기 메시에는 병과 팔 14종이 있어 지금 외형 팔만 보임(PIE 확인: 보병 → `CAInfantry` 슬롯만 보이고 푸리나 슬롯 가림). 남은 예전 메시 `SK_FPVM_Kar98k`·`SK_FPVM_G43`(병과 슬롯 없음)은 게임에서 쓰지 않음.
- **언리얼 쪽 확인:** 클립 압축으로 손이 총 위에서 미끄러지는 양 최대 0.21cm(`Scripts/Unreal/lyra_fpvm_hand_drift.py`) — 원인 아님.
- **최종 측정(대기 자세, 손 15개):** 최대 틈/파고듦 cm — Kar98k 0.77/0.24, G43 0.54/0.30, StG44 0.35/0.50, P38 0.55/0.58, P08 0.92/0.95, PP 0.93/0.31, 판처파우스트 0.64/0.33, 판처슈렉 0.53/0.34(모두 1cm 이내). 남음: MP40 왼손 검지 가운데 마디(병과 5종 최대 1.16), MP38 왼손 새끼·검지 가운데 마디(병과 6종 최대 1.29). 푸리나 손은 두 총 모두 1cm 이내. 손목-총 흔들림은 모든 무기 0.00cm.
- 언리얼 반영 완료: `lyra_fpvm_reimport.py`, `lyra_launchers.py assets`, `lyra_class_fp_arms2.py slots`, `lyra_pzf60_material.py`, `lyra_pistol_cases.py`, `lyra_fpvm_ads_update.py`, `lyra_default_primary.py`.

## 판처파우스트 안 보임 · 대전차 화기 조준 고증 · 병과 버튼 나라 탭 기준 (2026-11-22)
- **판처파우스트가 안 보이던 버그:** 재질 덮어쓰기는 컴포넌트에 '슬롯 번호'로 남는다. Kar98k 등에서 가린 병과 팔 슬롯 번호가 판처파우스트에서는 본체 슬롯(`Panzerfaust60Surface`) 번호라 본체가 가림 재질로 남았다(장착 때 0~9번만 되돌림). → 팔 슬롯 고르기(외형+메시가 바뀔 때)에서 무기 슬롯도 기본 재질로 되돌림, 조준경 몸통 가림 상태도 초기화(`Scripts/Unreal/lyra_fpvm_slot_reset.py`, 노드 `FPRS_`).
- **자료:** bergflak.com [가늠자](https://www.bergflak.com/pssight.html)·[방패](https://www.bergflak.com/psshield.html)·[사용법](https://www.bergflak.com/psuse.html), [Tank Archives 판처파우스트 교범 번역](https://www.tankarchives.com/2020/12/panzerfaust-manual.html), [Axis History Forum 판처파우스트 설명서](https://forum.axishistory.com/viewtopic.php?p=264132), Wikipedia [Panzerfaust](https://en.wikipedia.org/wiki/Panzerfaust)·[Panzerschreck](https://en.wikipedia.org/wiki/Panzerschreck).
- **판처슈렉(RPzB 54) 정조준:** 뒤 가늠자는 방패 바로 뒤 관 옆에 용접되고 방패 고정쇠가 그 앞에 끼어 유리창이 조준선 위에 온다. 앞 가늠자는 열린 틀 + 흰 기둥, 뒤 가늠자는 앞지름 홈(0·15·30). 원본 모델의 가늠자 틀은 창보다 9cm 낮아 조준선이 창을 지나지 않았다 → 원본 틀을 지우고 창 중심을 지나는 조준선에 홈판(가운데 + 양옆 15·30 홈)과 앞 틀·기둥을 새로 만듦(150 m 에서 기둥 끝이 홈 바닥). 눈 = 홈 뒤 28cm(예전 창 중심 뒤 40cm, 가늠자 없이 창만 봄). `fpvm_launchers.py`.
- **판처파우스트 60 영점:** 받은 모델의 실제 가늠자를 잼(판 구멍 높이 5.2/7.55/10.0cm = 30/60/80 m, 가늠쇠 = 탄두 맨 위). 예전에는 공식으로 정한 높이를 써서 이 모델 구멍과 안 맞아 80 m 에선 눈이 판의 막힌 곳을 지났고 탄두 끝이 구멍에 안 보였다. 이제 각 구멍 가운데에 탄두 끝이 보임(`Data/pzf_ads_zoom.jpg`). 조준선 각 5.56°/10.85°/16.12° 에서 거꾸로 구한 실효 속도 39.1 m/s(공기 저항 포함, 사료 45 m/s 와 맞음)를 탄두 속도로 씀. 겨드랑이 자세라 눈 = 판 뒤 34cm(예전 24cm 는 판이 화면 세로를 다 덮음), 대기 자세는 예전 그대로.
- **병과(외형) 버튼:** 나라별 두 줄 대신 한 줄. 위 국가 탭이 대일본제국이면 같은 병과의 일본 캐릭터, 그 밖(제3제국 등)이면 독일 캐릭터(`Scripts/Unreal/lyra_look_by_nation.py`, 노드 `LN_`; 일본 줄 `LookRow2` 는 접음).
- **확인:** PIE 에서 판처파우스트 보임, 대전차 화기 정조준 캡처 `Data/lch_game_new.jpg`. 병과 버튼은 배선(형변환 → NationIndex==1 분기 → 일본/독일 이벤트)으로 확인, 실제 마우스 클릭은 못 해 봄.
- 참고: 메뉴를 고친 직후 PIE 시작에서 에디터가 Python 쓰레기 수거 중 충돌(스크립트가 쥔 위젯 객체)해 다시 켰다. 저장은 충돌 전에 끝나 있었다.
