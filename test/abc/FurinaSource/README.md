# FurinaSource

abc 프로젝트의 플레이어를 Furina로 바꾸면서 만든 원본 파일·스크립트·데이터입니다.
`Content/` 밖에 있어서 언리얼이 임포트하지 않습니다. 결과 에셋은 `Content/Furina`에 있습니다.

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
  - **좌클릭:** 사격합니다. 크로스헤어 방향으로 몸을 돌린 뒤 사격 몽타주와 소총 노리쇠 모션을 재생합니다. 화면 중앙으로 레이 판정을 하며, 맞은 물체가 물리 시뮬레이션 중이면 밀어냅니다. 판정선은 0.15초 동안 표시됩니다.
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
- **달리기 총 기울이기:** 달리기 비율(`Run`, 걷기 120 → 달리기 600cm/s)에 비례해 적용됩니다. 총구가 안쪽(왼쪽)으로 20° 돌고, 총 윗면이 왼쪽으로 30° 기울며, 총구가 6° 내려갑니다. 총 전체는 오른쪽 2cm, 뒤 3cm, 아래 7cm로 옮겨집니다(PUBG식 로우 레디). 3인칭에서도 같은 자세라 시점 전환이 이어집니다. 값은 `Tools/gen_fp_rig.py`의 `SPRINT_*`에 있습니다.
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
