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
