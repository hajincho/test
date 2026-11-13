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

## 머리카락 물리 (Unity `HuTaoChainPhysics` → `ABP_Furina`의 AnimDynamics 5개)

- **생성:** `Scripts/Tools/gen_t3d3.py <Data 경로>` → `Data/abp_graph3.t3d` (ABP_Furina AnimGraph 전체)
- **대상 사슬:** 땋은 머리 `F_0..17_1_L/R`, 옆머리 `CF_1..2_L/R`, 아호게 `DM_0..5_1`
- **파라미터:** Unity `ProfileFor()`의 HairBack / HairSide / Ahoge 값을 그대로 씁니다. 변환식은 다음과 같습니다.
  - 감쇠 d = 1−e^(−damping)
  - 스프링 = 12×stiffness²
  - 중력 = gravityInfluence×0.6
  - 회전 한계: 뿌리→끝으로 보간
- **충돌:** 몸 캡슐은 Unity `CacheBodyCapsules()`의 Furina 목록을 구로 옮겼습니다. 휴식 자세에서 이미 닿는 구는 줄이거나 제외합니다(`CacheAttachmentContacts`와 같은 처리).
- **시뮬레이션 공간:** Head 본 기준입니다. Unity의 parentMotionInfluence에 해당하며, 머리 가속의 일부만 관성으로 받습니다.

## 눈 깜빡임 (Unity `UntitledCharacterIdle.UpdateIdleBlink` 타이밍 → `CR_FurinaSecondary`)

- **조건:** 대기·걷기·뛰기 상태와 관계없이 깜빡입니다. `FurinaIdle` 블렌드 값으로 눈 감김을 차단하지 않습니다.
- **간격:** 4~5초(TimeLoop 4.5초 + 사인 지터)입니다.
- **동작:** 감기 0.045초 → 유지 0.065초 → 뜨기 0.085초, 스무스스텝입니다.
- **출력:** `IdleBlink` 모프 커브를 설정합니다. 빌더가 Control Rig 커브와 스켈레톤의 morph-target 메타데이터를 유지합니다.

## 무릎과 걷기 발소리 수정 (2026-11-14)

- `CR_FurinaSecondary`의 양쪽 TwoBoneIK 폴은 **각 허벅지 위치 + 앞쪽 50 cm + 바깥쪽 6 cm**인 위치입니다. Furina 메시의 앞은 +Y, 왼쪽은 +X입니다. UE 5.8의 해당 노드는 `Direction`을 선택해도 내부 두 뼈 솔버에 위치처럼 전달하므로, 원점 기준 방향 벡터를 넣으면 무릎이 안으로 접힙니다. `Location`과 다리 기준 위치를 명시합니다.
- IK 가중치의 ×10 증폭을 제거했습니다. 걷기·뛰기 전환 초기에 IK가 갑자기 최대 강도로 켜지지 않습니다.
- `AS_Furina_Walk`의 `FurinaWalkSteps` 트랙에 0.0667 / 0.7333초의 발 접촉 알림을 넣었습니다. 1.333초 주기에 두 번이며, 재생 가중치가 0.5 이상일 때 발목에서 작은 발소리를 냅니다(볼륨 0.28, 피치 1.05).
- `Manny_AnimBlueprint`의 원래 `Footstep` 경로는 `FurinaWalk > 0.5`에서 건너뜁니다. 보이는 걷기 애니메이션의 소리와 숨긴 Manny 소리가 겹치지 않으며, 뛰기 소리와 공중 상태 검사는 기존 경로를 사용합니다.
- 제자리 적용: `Scripts/Unreal/ue_apply_character_fixes.py`. 백업은 `Backups/CharacterFixes_20261114/`에 있습니다. 다른 에디터 프로세스가 같은 에셋을 열고 있으면 파일 잠금 때문에 저장할 수 없습니다.
- 검증: `ue_validate_character_fixes.py`는 1,440프레임의 걷기·뛰기 전환, 이동 중 깜빡임, 다리 길이, 폴 위치의 이동 불변성을 검사합니다. 전후 결과는 `Data/character_fix_validation_before.json`, `Data/character_fix_validation_after.json`에 있습니다. `ue_verify_character_runtime.py`는 임시 PIE 검사 후 편집 모드로 돌아가며 레벨을 저장하지 않습니다.

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
