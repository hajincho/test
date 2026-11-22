# 독일 무기 1인칭 모션 조사 (2026-11-21)

1인칭만 구현합니다. 무기마다 **출처를 3개 이상** 쓰고, 그중 하나 이상은 당시 자료(1940년대 미군 교범 TM-E 30-451, 당시 교범 전재본 Lone Sentry 등)입니다.
사용자가 준 `fps-animations-sniper-rifle.zip`(볼트액션 1인칭 애니)는 **참고만** 합니다. 메시·뼈·키를 가져다 쓰지 않고 단계별 시간과 손 경로만 수치로 뽑았습니다.

출처 신뢰도 표기: **[당시]** 1940년대 교범·전재본, **[전문]** 총기 전문지·박물관·경매 기록, **[2차]** 위키·포럼(보조로만).

---

## 0. 참고 애니 수치화 (`Scripts/Blender/ref_fps_anim_phases.py` → `Data/ref_boltaction_phases.json`)

60fps, 총(Body 뼈) 기준 좌표, 단위는 cm/°. `SRifle_Shot_sight`(사격 + 볼트 조작)의 구간은 다음과 같습니다.

| 구간 | 프레임 | 시간 | 내용 |
|---|---|---|---|
| 발사·반동 | 1–6 | 0.08초 | 총이 뒤로 3.2cm, 아래로 2.3cm, 위로 0.8° |
| 오른손이 볼트로 감 | 6–31 | 0.42초 | 손잡이에서 위·뒤로 이동, 반동이 가라앉음 |
| 볼트 들기 | 31–36 | 0.08초 | 볼트가 총열 축 둘레로 회전 |
| 볼트 당기기 | 36–41 | 0.08초 | 7.3cm 후퇴 |
| 뒤에서 멈춤 | 41–51 | 0.17초 | 탄피 배출 |
| 밀기 | 51–61 | 0.17초 | 전진 |
| 볼트 내리기 | 61–66 | 0.08초 | 잠금 |
| 손잡이로 복귀 | 66–91 | 0.42초 | |
| **합계** | 6–91 | **약 1.42초** | 볼트 조작 중 총이 3~5° 오른쪽으로 기울어짐(roll) |

- 왼손은 내내 총 앞받침에 고정되어 있습니다(오차 0.1cm 미만).
- `SRifle_Reload`(3.17초)는 분리형 탄창을 씁니다. Kar98k는 클립 장전이라 구성만 참고하고(왼손 이동 경로, 총 기울이기 최대 15°) 동작은 아래 교범 순서로 새로 만듭니다.
- 참고 애니의 볼트는 단계마다 값이 계단식으로 튑니다(보간 없음). 우리는 부드러운 곡선으로 만듭니다.

---

## 1. Kar98k (볼트액션, 5발 내장 탄창, 클립 장전) — **이번에 구현**

**동작 순서**
1. 사격: 반동으로 총이 뒤·위로 움직입니다. 개머리판은 어깨에 붙인 채 둡니다.
2. 볼트 조작(**위 → 뒤 → 앞 → 아래**): 볼트를 들어 올리는 순간 공이가 젖혀집니다(cock-on-opening). 끝까지 당겨 탄피를 빼고, 밀어서 다음 탄을 넣은 뒤 내려 잠급니다. 그 뒤 바로 손잡이를 다시 쥡니다.
3. 클립 장전(5발 클립):
   - 볼트를 엽니다(위·뒤).
   - 클립을 리시버 뒤 브리지의 클립 홈에 꽂습니다.
   - 엄지로 탄을 눌러 탄창에 밀어 넣습니다.
   - 볼트를 닫으면 빈 클립이 밀려 튀어나갑니다. 손으로 빼도 됩니다.
4. 손 모양:
   - 볼트 손잡이 공은 꽉 쥐지 않습니다. 굽힌 검지 옆면과 엄지 사이에 끼웁니다.
   - 조작 내내 개머리판은 어깨에, 눈은 표적에 둡니다.

**수치**
- 볼트 회전 90°: 손잡이가 수평에서 수직 가까이 올라갑니다. Mauser 98은 90° 회전 볼트입니다.
- 볼트 후퇴량 약 8.6cm: 7.92×57mm 탄 전장이 82mm라서 탄을 빼고 넣으려면 그보다 길게 물러나야 합니다. 우리 모델에서는 볼트 부품을 분리해 실제로 잴 예정입니다.
- 조준 사격 속도: 숙련자 기준 분당 10~15발. 이것으로 볼트 1회 조작 약 1.0~1.4초를 잡습니다(참고 애니 1.42초와 맞음).

**출처**
- [당시] Lone Sentry, *Mauser Kar. 98K Rifle — WWII German Infantry Weapons*(미 육군 정보 자료 전재): 볼트를 열고, 클립 홈에 클립을 넣고, 탄을 눌러 넣고, 볼트를 닫으면 빈 클립이 빠짐 — https://m.lonesentry.com/manuals/german-infantry-weapons/kar98-german-rifle.html
- [당시] TM-E 30-451 *Handbook on German Military Forces*(1945): Kar98k는 미국 스프링필드 소총과 같은 방식으로 장전 — https://lonesentry.com/manuals/tme30/ch7sec2sub5.html , 원본 스캔 https://archive.org/details/TM-E30-451/page/n0
- [2차] Wikipedia *Karabiner 98k*: 5발, 클립 또는 한 발씩 장전, 볼트를 닫을 때 빈 클립 배출 — https://en.wikipedia.org/wiki/Karabiner_98k
- [2차] Wikipedia *Stripper clip*: 볼트를 연 뒤 클립을 꽂고 탄을 눌러 벗겨 넣음 — https://en.wikipedia.org/wiki/Stripper_clip
- [전문] American Rifleman *Exploded View: Mauser K98k* — https://www.americanrifleman.org/content/exploded-view-mauser-k98k/
- [전문] Outdoor Hub *Running a Bolt-Action Rifle*: 쏘자마자 볼트 조작 시작, 개머리판은 어깨에, 눈은 표적에, 닫으면 바로 다시 쥠 — https://www.outdoorhub.com/how-to/2016/10/03/shooting-mann-running-bolt-action-rifle/
- [2차] Accurate Reloading 포럼: Mauser 손잡이 공을 검지 옆면과 엄지 사이에 끼워 조작 — https://forums.accuratereloading.com/eve/forums/a/tpc/f/1411043/m/775104051
- [2차] 분당 사격 속도: Forgotten Weapons(독일 숙련병 분당 11발 언급), The Armory Life — https://www.forgottenweapons.com/still-talking-when-theres-science-to-do/ , https://www.thearmorylife.com/germany-karabiner-98k-rifle/
- [참고] `fps-animations-sniper-rifle.zip`의 `SRifle_Shot_sight`·`SRifle_Reload` 구간 수치(위 0절)

## 1-1. Kar98k 조준경 사수형 (ZF39 / ZF41) — Kar98k 모션에서 파생

- **ZF39(저포탑, 조준경이 리시버 위):** 볼트를 수직까지 올리면 손잡이가 조준경에 걸립니다. 그래서 저격형은 볼트 손잡이를 아래로 꺾은(turned-down) 형태를 썼습니다. 클립 장전도 조준경이 리시버 위를 덮어 어렵기 때문에 한 발씩 넣는 동작으로 대체합니다(구현 시 확인).
- **ZF41(가늠자 받침 위, 앞쪽에 낮게):** 리시버가 비어 있어 일반 Kar98k와 똑같이 클립 장전·볼트 조작을 합니다. 1.5배 장안거리(eye relief)가 긴 조준경입니다.
- 출처:
  - [전문] American Rifleman *The K98k Zf 41 — The First Scout Rifle?* — https://americanrifleman.org/articles/2016/6/16/the-k98k-zf-41-the-first-scout-rifle
  - [전문] HistoryRise *German WWII sniper scope mounting systems* — https://historyrise.com/article/the-development-of-german-wwii-sniper-scope-mounting-systems/
  - [전문] Rock Island Auction *K98k sniper rifle with ZF41* — https://www.rockislandauction.com/detail/4100/400/wwii-german-mauser-byf43-k98k-sniper-rifle-with-zf411-scope
  - [2차] Wikipedia *Zf 41* — https://www.Wikipedia.org/wiki/Zf-41

## 2. Gewehr 43 (+ZF4) — 반자동, 10발 분리형 탄창(5발 클립으로도 채움)

**이 게임의 장전 방식(사용자 지정, 2026-11-21): 탄창 교환 대신 5발 클립 두 개를 연속으로 넣는다. 구현 완료(`Scripts/Blender/fpvm_g43.py`).**
- 순서:
  1. 왼손이 왼쪽 장전 손잡이를 끝까지 당긴다. 볼트 캐리어의 홀드오픈 걸쇠에 걸려 열린 채로 있다.
  2. 클립 1을 열린 캐리어 앞 클립 자리에 꽂고, 엄지로 5발을 탄창에 눌러 넣는다.
  3. 빈 클립을 손으로 뽑아 버린다. Kar98k 와 달리 볼트가 닫히면서 클립을 밀어내지 않는다.
  4. 클립 2도 같은 순서로 넣는다.
  5. 왼손이 장전 손잡이를 살짝 당겼다 놓아 볼트를 닫는다.
- 근거:
  - [전문] CE: G43 – MP44 Collectors Service(espeholt.dk): 급탄은 10발 분리형 탄창이고 클립도 쓸 수 있다. 볼트 캐리어에 홀드오픈 걸쇠가 있다(말기 생산품 일부는 없음). 장전 손잡이를 끝까지 당겨 다룬다. https://www.espeholt.dk/g43_parts.html
  - [2차] Wikipedia *Gewehr 43*: G41처럼 탄창을 빼지 않고 5발 클립으로 장전하도록 설계. https://en.Wikipedia.com/wiki/Gewehr_43
  - [전문] Forgotten Weapons *German Troop Trials Push-Button Gewehr 41(W)*: 클립 두 개로 장전한 뒤 버튼으로 볼트를 닫는다. 볼트 손잡이를 살짝 당겼다 놓아도 된다. https://www.forgottenweapons.com/german-troop-trials-push-button-gewehr-41w/
  - [2차] Wikipedia *Gewehr 41*: 고정 10발 탄창을 Kar98k 클립 두 개로 채운다. https://wikipedia.com/wiki/Gewehr_41
  - [전문] Forgotten Weapons *Gewehr 43*(사용자 의견): 새 탄창, 한 발씩, 또는 클립으로 장전. https://forgottenweapons.com/german-ww2-rifles/gewehr-43
- 확인이 남은 점: 클립 자리의 정확한 위치(캐리어 앞면으로 가정했다). 사진·도면으로 더 확인해야 한다.

- **동작:**
  - 사격하면 볼트가 스스로 돌아옵니다. 장전 손잡이는 쏠 때 움직이지 않습니다.
  - 장전 손잡이는 리시버 **왼쪽**에 있어 왼손으로 당깁니다.
  - 탄창 교환은 빼기 → 넣기 → 장전 손잡이 당기기 순서입니다. 볼트가 열린 상태에서 위에서 클립 2개로 채울 수도 있습니다.
- **출처:**
  - [전문] Forgotten Weapons *Slow Motion Gewehr 43* — https://www.forgottenweapons.com/slow-motion-gewehr-43/
  - [전문] Forgotten Weapons *RIA German Gewehr 41M* — https://www.forgottenweapons.com/ria-german-gewehr-41m/
  - [전문] TFB *WWII German G43 Run and Gun* — https://www.thefirearmblog.com/blog/2015/11/05/wwii-german-g43-run-gun/
  - [2차] Wikipedia *Gewehr 43* — https://en.Wikipedia.com/wiki/Gewehr_43
  - [2차] IMFDB *Gewehr 43* — https://www.imfdb.org/index.php/Gewehr_43
- **ZF4 장착:**
  - 리시버 오른쪽 도브테일에 붙습니다(이번 합본에 반영).
  - [전문] k98kforum *G/K43 ZF4 scope position* — https://k98kforum.com/threads/g-k-43-zf4-scope-position.60675/post-474742
  - [전문] Legacy Collectibles *ZF4 with BLM mount* — https://legacy-collectibles.com/zf4-g43-k43-scope-with-blm-serialized-mount/301181

## 3. MP40 / MP38 — 오픈볼트 기관단총, 32발 탄창

- **동작:**
  - 장전 손잡이는 왼쪽에 있습니다. 끝까지 당긴 뒤 위쪽 'S' 홈에 걸면 안전입니다. 확실한 안전장치는 아니고, 후기형은 손잡이를 밀어 넣는 잠금이 있습니다.
  - 탄창 교환은 탄창 멈치를 누르고 빼는 방식입니다.
  - 받침손은 **탄창 하우징**(또는 하우징과 손잡이 사이 아래쪽 덮개)을 잡습니다. 탄창 몸통을 손잡이로 쥐면 하우징이 탄창을 단단히 물지 못해 탄창 입구가 급탄 선에서 밀려 고장이 났고, 당시 병사들은 하우징이나 덮개를 잡도록 교육받았습니다(Wikipedia *MP 40*). 총열에 단열이 없어 받침손이 앞으로 가면 화상을 입었다는 점도 같은 문서에 있습니다. → 구현: 왼손을 하우징 왼쪽에서 감쌈(2026-11-21).
  - 연사 속도: 순환 500발/분, 실용 180발/분(TM-E 30-451, 1945). Wikipedia 정보란은 500~550발/분. → 구현 500발/분(0.12초 간격).
- **출처:**
  - [당시] Lone Sentry *Submachine Gun (M.P. 38 and M.P. 40)* — https://lonesentry.com/manuals/german-infantry-weapons/mp40-machine-pistol.html
  - [당시] TM-E 30-451 기관단총 항목 — https://lonesentry.com/manuals/tme30/ch7sec2sub4.html
  - [2차] Wikipedia *MP 40* — https://en.wikipedia.org/wiki/MP_40
  - [전문] GSG MP40 설명서 — https://www.action-shop24.de/media/2e/5c/1f/1725970300/940.70.01.0_Anleitung_GSG_MP40_9x19_EN_DE_2021_web.pdf

## 4. StG44 — 돌격소총, 30발 탄창, 단발/연발

- **동작:**
  - 장전 손잡이는 **왼쪽**에 있어, 오른손으로 손잡이를 쥔 채 왼손으로 당깁니다.
  - 탄창 멈치는 왼쪽에 있어, 탄창을 잡은 채 누르고 뺍니다.
  - 안전장치와 단발/연발 전환 레버도 왼쪽에 있습니다.
  - 장전 손잡이가 쏠 때 움직이는지는 자료끼리 엇갈립니다. 구현 전에 영상 자료로 확인해야 합니다.
  - 연사 속도: Wikipedia *StG 44* 정보란 약 500~600발/분, 본문은 당시 교범을 인용해 540발/분. → 구현 550발/분(0.109초 간격).
  - 받침손 위치는 읽은 자료에 명시가 없어, 탄창(MP40 과 같은 이유로 손잡이로 쓰지 않는 쪽이 안전)을 피해 탄창 앞 총열 덮개 아래를 받치게 했습니다(2026-11-21).
- **출처:**
  - [당시] Lone Sentry *Sturmgewehr 44 — Tactical and Technical Trends* — https://lonesentry.com/articles/ttt07/stg44-assault-rifle.html
  - [2차] Wikipedia *StG 44* — https://en.wikipedia.org/wiki/StG_44 , IMFDB *StG44* — https://www.imfdb.org/wiki/StG44
  - [전문] Gun Digest *StG 44: Father of the Modern Fighting Rifle* — https://gundigest.com/?p=296221
  - [전문] TFB *Shooting the Sturmgewehr* — https://www.thefirearmblog.com/blog/2016/05/25/sturmgewehr-full-auto-mp43-mp44-stg44/
  - [전문] The Armory Life *Origin of Everything: the German StG44* — https://www.thearmorylife.com/origin-of-everything-the-german-stg44/

## 5. 권총 — P38(DA/SA, 디코커), P08(토글 잠금), PP(블로우백, DA/SA)

- **P38:**
  - 공이치기를 젖히지 않고 바로 쏠 수 있습니다(더블액션).
  - 안전장치를 걸면 공이치기가 안전하게 내려갑니다.
  - 장전은 슬라이드를 당기는 방식입니다.
- **P08:**
  - 슬라이드가 없습니다. 위쪽 토글(관절 팔)의 손잡이 두 개를 집어 위·뒤로 꺾어 장전합니다.
  - 탄창 멈치는 방아쇠 뒤 왼쪽 버튼입니다.
- **PP:** P38과 같은 DA/SA이며, 안전·디코커 레버가 슬라이드 위에 있습니다.
- **출처:**
  - [당시] *WWII Walther P-38 Owner's Manual*(스캔) — https://archive.org/download/MManuals/WwiiWaltherP-38OwnersManual.pdf
  - [전문] American Rifleman *A Look Back at the Walther P38* — https://www.americanrifleman.org/content/a-look-back-at-the-walther-p38/
  - [전문] Gun Digest *Walther P38* — https://gundigest.com/article/walther-p38
  - [2차] Wikipedia *Luger pistol* — https://www.Wikipedia.org/wiki/Luger_P08
  - [2차] Wikipedia *Walther PP* — https://en.wikipedia.com/wiki/Walther_PP
  - [전문] GunsAmerica *German Military Handguns of WWII* — https://www.gunsamerica.com/blog/milsurp-german-military-handguns-world-war-ii-armorers-nightmare/

## 6. MG34 / MG42 — 탄띠 급탄 기관총 (나중에, 복잡)

- **동작:**
  - 탄띠는 왼쪽에서 들어갑니다. 덮개를 열거나 닫은 채로 첫 탄이 멈춤쇠 3개에 걸릴 때까지 당겨 넣습니다.
  - 쏠 준비가 되면 장전 손잡이를 끝까지 당깁니다.
  - 양각대는 펴서 엎드려 쏩니다. 서서 쏘기·허리 사격은 예외적인 자세입니다.
- **출처:**
  - [당시] Lone Sentry *MG-34* — https://3g.lonesentry.com/manuals/german-infantry-weapons/mg34-machine-gun.html
  - [당시] Lone Sentry *MG-42* — https://3g.lonesentry.com/manuals/german-infantry-weapons/mg42-machine-gun.html
  - [당시] TM-E 30-451 기관총 항목 — https://lonesentry.com/manuals/tme30/ch7sec2sub6.html
  - [2차] Wikipedia *MG 34*, *MG42* — https://Www.Wikipedia.org/wiki/MG_34 , https://wikipedia.com/wiki/MG42

## 7. Panzerfaust — 일회용 대전차 (2026-11-21 구현, Pzf 60)

- **동작:**
  - 안전핀을 뺍니다.
  - 가늠자 판을 세웁니다. 세우지 않으면 격발이 안 되므로 이것도 안전장치입니다.
  - 안전 막대를 앞으로 밉니다. 30형은 위쪽 장전 막대를 밉니다.
  - **겨드랑이에 끼워** 표적·가늠자·탄두 윗부분을 맞춰 조준합니다. 쏘고 나면 빈 관을 버립니다.
- **출처:**
  - [2차] Wikipedia *Panzerfaust* — https://en.wikipedia.org/wiki/Panzerfaust
  - [전문] Tank Archives *Panzerfaust manual*(당시 교범 소개) — https://www.tankarchives.com/2020/12/panzerfaust-manual.html
  - [전문] Panzerworld *Panzerfaust* — https://panzerworld.com/panzerfaust
  - [2차] IMFDB *Panzerfaust 60* — https://www.imfdb.org/wiki/Panzerfaust_60
  - [전문] The Armory Life *Panzerfaust* — https://www.thearmorylife.com/panzerfaust/

## 8. PzB 39 — 단발 대전차 소총, 낙하 노리쇠(falling block) (나중에)

- **동작:**
  - 권총손잡이를 앞·아래로 움직여 노리쇠를 내립니다.
  - 한 발 넣고 손잡이를 되돌립니다.
  - 탄 보관함(옆에 붙는 탄 상자)이 있었는지는 자료끼리 엇갈려 구현 전에 확인합니다.
- **출처:**
  - [당시] Lone Sentry *Pz.B. 39 Antitank Rifle* — https://lonesentry.com/manuals/german-infantry-weapons/antitank-rifle-pzb-39.html
  - [전문] Forgotten Weapons *PzB 39 at RIA* — https://www.forgottenweapons.com/pzb-39-german-anti-tank-rifle-at-ria/
  - [2차] Wikipedia *Panzerbüchse 39* — https://en.wikipedia.org/wiki/Panzerb%C3%BCchse_39
  - [2차] IMFDB *Panzerbüchse 39* — https://www.imfdb.org/wiki/Panzerbüchse_39

---

## 보류(특수 경우, 아직 만들지 않음)

| 무기 | 보류 이유 |
|---|---|
| **8cm GrW 34 박격포** | 분대가 운용합니다. 받침판·양각대를 설치하고 포탄을 위에서 떨어뜨려 쏩니다. 1인칭 손 모양이 일반 소총 틀과 맞지 않습니다. |
| 박격포탄(Mortar Shell) | 박격포에 딸린 부속입니다. |
| MG34 / MG42 양각대 거치 사격 | 엎드림·거치 상태 전환이 필요합니다. 들고 쏘기만 먼저 할지는 나중에 정합니다. |
| 탄약(7.92×94, 마우저 클립), 조준경 단품(ZF4/ZF39/ZF41) | 무기가 아니라 다른 모션에 쓰이는 소품입니다. 클립은 Kar98k 장전에 씁니다. |

## 구현 순서(계획)

1. Kar98k (완료)
2. G43 (완료, 클립 2개 연속 장전)
3. Kar98k ZF41 / ZF39, G43 ZF4
4. MP40 / MP38
5. StG44
6. P38 / P08 / PP
7. PzB 39
8. Panzerfaust
9. MG34 / MG42(들고 쏘기)

## 5-1. 권총 세 자세(비조준 한손 / 견착 한손 팔 뻗기 / 정조준 두 손) — 2026-11-21 구현

- **사용자 지정:**
  - 비조준: 한손.
  - 견착: 팔을 쭉 뻗은 한손, 총을 안쪽으로 기울여 정조준과 구별.
  - 정조준: 두 손으로 기계식 조준기를 봄.
- **역사:** 2차대전기 군·특수부대 권총 사격은 한손 지향사격 위주였습니다.
  - Applegate의 *Kill or Get Killed*(1943, Fairbairn·Sykes와 만든 OSS 훈련 FSA) 방식:
    - 한손으로 팔·손목을 굳힌 채 권총을 몸 가운데로 들어 올려 쏩니다.
    - 표적이 옆에 있으면 어깨·팔꿈치가 아니라 허리로 몸을 돌립니다.
  - 두 손 조준 자세는 전후에 퍼졌습니다:
    - Weaver: 1959년, Jack Weaver.
    - Isosceles: 1980년대 IPSC.
  - 그래서 정조준만 두 손이고 나머지는 한손입니다.
- **출처:**
  - [2차] Wikipedia *Point shooting*(Applegate 1943, FSA) — https://en.wikipedia.org/wiki/Point_shooting
  - [2차] Wikipedia *Weaver stance* — https://en.wikipedia.org/wiki/Weaver_stance
  - [2차] Wikipedia *Isosceles stance* — https://en.wikipedia.org/wiki/Isosceles_stance
  - [당시] TM-E 30-451(1945) 권총 항목: P08·P38 제원(사격 자세 기술은 없음) — https://lonesentry.com/manuals/tme30/ch7sec2sub1and2.html
- **구현:** `Scripts/Blender/fpvm_pistols2.py`

## 5-2. 권총 탄창 교환 방식(2026-11-21 구현)

- **P38:** 탄창 걸쇠가 손잡이 밑 뒤쪽에 있는 힐(heel) 방식입니다. 걸쇠를 밀며 탄창을 손으로 뽑아냅니다. 마지막 발 뒤에는 슬라이드가 열린 채 멈추고, 새 탄창을 넣은 뒤 슬라이드를 당겼다 놓습니다.
- **P08:** 손잡이 왼쪽, 방아쇠 뒤에 탄창 단추가 있습니다. 탄창 바닥에는 나무 손잡이가 있습니다. 마지막 발 뒤에는 토글이 열린 채 멈추고, 토글 손잡이를 위·뒤로 꺾었다 놓아 닫습니다.
- **PP:** 손잡이 왼쪽, 방아쇠 뒤에 탄창 단추가 있습니다. 마지막 발 뒤에는 슬라이드가 열린 채 멈추고, 슬라이드를 당겼다 놓아 닫습니다.
- **출처:**
  - [당시] TM-E 30-451(1945) 권총 항목(P08·P38 제원·작동) — https://lonesentry.com/manuals/tme30/ch7sec2sub1and2.html
  - [2차] Wikipedia *Walther P38* / *Luger pistol* / *Walther PP* — https://en.wikipedia.org/wiki/Walther_P38 , https://en.wikipedia.org/wiki/Luger_pistol , https://en.wikipedia.org/wiki/Walther_PP
  - [2차] IMFDB *Walther P38* / *Luger P08* / *Walther PP* (영상 속 장전 장면) — https://www.imfdb.org/wiki/Walther_P38 , https://www.imfdb.org/wiki/Luger_P08 , https://www.imfdb.org/wiki/Walther_PP
- **확인하지 못한 점:** 이 절의 걸쇠·단추 위치와 열린 채 멈춤 여부는 위 문서들에서 따로 확인하지 않았습니다. 일반적으로 알려진 사실을 바탕으로 정리했습니다.

## 5-3. 권총 탄피 배출 방향(2026-11-21 구현)

- **P38:** 배출구가 슬라이드 **왼쪽**에 있어 탄피가 왼쪽으로 튑니다. 오른손잡이 사수 기준으로 드문 배치입니다.
- **P08:** 토글이 위로 꺾이며 열려 탄피가 **위**(조금 오른쪽·뒤)로 튑니다.
- **PP:** 슬라이드 **오른쪽** 배출구로 탄피가 오른쪽으로 튑니다.
- **출처:** Wikipedia *Walther P38* / *Luger pistol* / *Walther PP*, IMFDB 각 문서(영상 장면). 링크는 5-2절과 같습니다.
- **확인하지 못한 점:** 방향은 일반적으로 알려진 내용으로 정리했고, 위 문서들에서 따로 확인하지 않았습니다.
- **탄피:** 9×19 Pistolenpatrone 08은 놋쇠 또는 전쟁 중 강철 탄피, 7.65 Browning(.32 ACP)은 짧은 반테두리 탄피입니다. 모델은 프로젝트의 `SM_FPVM_9mmCase`, `SM_FPVM_32Case`를 씁니다.

## 9. 탄약 장약량 기반 사격 효과(총구 화염·연기·반동·화면 흔들림) — 2026-11-21

| 무기 | 탄약 | 탄두 g | 장약 g | 탄속 m/s | 총 kg | 총열 mm | 자유 반동 m/s (M4 대비) | 반동 J | 흔들림 | 화염 크기 | 연기 농도·지속 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Kar98k | 7.92×57 s.S. | 12.8 | 2.75~2.85 | 755 | 3.9 | 600 | 3.62 (×2.01) | 25.5 | 2.15 | 1.00 | 1.0 · 3.2초 |
| Kar98k+ZF39 / ZF41 | 〃 | | | | 4.5 / 4.2(추정) | | ×1.74 / ×1.87 | 22.1 / 23.7 | 2.00 / 2.07 | 1.00 | 1.0 |
| G43 / +ZF4 | 〃 | 12.8 | 2.8 | 760 | 4.4 / 4.9(추정) | 550 | ×1.79 / ×1.61 | 22.8 / 20.5 | 2.04 / 1.93 | 1.03 | 1.0 |
| StG44 | 7.92×33 Kurz | 8.1 | 1.57(추정) | 685 | 5.13(장전) | 419 | ×0.81 | 5.4 | 0.99 | 0.83 | 0.75 · 2.8초 |
| MP40 / MP38 | 9×19 Pist.Patr.08 | 8.0 | 0.36(추정) | 400 | 3.97 / 4.1(추정) | 251 | ×0.48 / ×0.46 | 1.5 | 0.52 | 0.47 | 0.36 · 2.2초 |
| P38 | 9×19 | 8.0 | 0.36(추정) | 320 | 0.96 | 125 | ×1.58 | 3.9 | 0.84 | 0.57 | 0.36 |
| P08 | 9×19 | 8.0 | 0.36(추정) | 375 | 0.871 | 100 | ×2.04 | 5.9 | 1.03 | 0.61 | 0.36 |
| PP | 7.65 Browning | 4.6 | 0.17(추정) | 320 | 0.66 | 98 | ×1.31 | 1.8 | 0.58 | 0.42 | 0.25 · 2.0초 |

- **계산 방법**(`Scripts/Tools/gen_hist_fx.py` → `Data/hist_fx.json`):
  - 자유 반동은 Free recoil 식 v = (m탄·v탄 + m장약·v가스)/M을 씁니다.
  - 가스 속도:
    - 소총: 1,585 m/s(문서의 7×57 예시)
    - Kurz: 1.75 v
    - 권총탄: 1.5 v
- **게임 환산(가정):**
  - 반동은 M4(1.8 m/s) 대비 배율입니다. 권총을 한손으로 쥐면 1.5배를 더 곱합니다.
  - 흔들림은 sqrt(에너지/5.5 J)입니다.
  - 화염 크기는 sqrt(장약/2.8 g) × (600 mm/총열)^0.3입니다.
  - 연기 농도는 sqrt(장약/2.8 g)입니다.
- **화염 모양:**
  - 독일 총은 맨 총구라서 M4 소염기의 꽃잎·별 모양을 껐습니다.
  - 길이비: 소총 1.0, 기관단총 0.75, 권총 0.55.
  - 근거: Muzzle flash 문서. 화염 크기는 장약 연소 에너지와 덜 탄 분출물 양에 좌우되고, 2차 화염은 분출물이 공기와 만나 타면서 생깁니다. Kar98k 문서에 따르면 s.S. 탄은 짧은 총열에서 예전 S 탄보다 화염이 적었습니다.
- **연기:** 무연 화약이라 옅은 회백색 연기가 잠깐 남았다가 위로 오르며 퍼지고 사라집니다.
- **출처:**
  - [1] de.wikipedia *7,92 × 57 mm*(s.S. 장약 2.75~2.85 g, 12.8 g, 755 m/s) — https://de.wikipedia.org/wiki/7,92_%C3%97_57_mm
  - [2] Wikipedia *Karabiner 98k* — https://en.wikipedia.org/wiki/Karabiner_98k
  - [3] Wikipedia *Gewehr 43* — https://en.wikipedia.org/wiki/Gewehr_43
  - [4] Wikipedia *7.92×33mm Kurz* — https://en.wikipedia.org/wiki/7.92%C3%9733mm_Kurz
  - [5] Wikipedia *StG 44* — https://en.wikipedia.org/wiki/StG_44
  - [6] Wikipedia *MP 40*, *Walther P38*, *Luger pistol*, *Walther PP*, *.32 ACP*
  - [7] Wikipedia *Free recoil* — https://en.wikipedia.org/wiki/Free_recoil
  - [8] Wikipedia *Muzzle flash* — https://en.wikipedia.org/wiki/Muzzle_flash
  - [당시] TM-E 30-451(1945): Kar98k 약 9 lb, G43 10 lb, MP40 9 lb·순환 500발/분, MP43/1 2,200 ft/s — https://lonesentry.com/manuals/tme30/ch7sec2sub5.html , https://lonesentry.com/manuals/tme30/ch7sec2sub4.html
- **출처에 숫자가 없어 추정한 값:**
  - 장약: Kurz·9 mm·7.65 mm
  - 무게: MP38, 조준경과 마운트


## 7-1. Panzerfaust 60 구현 수치 (2026-11-21)
- **가늠자:** 접이식 판에 구멍 3개 = 30/60/80 m(TM-E 30-451: "apertures for 30, 60 and 80 meters"). 겨누기 = 가늠자 구멍 + 탄두 앞쪽 위(Korn).
- **탄두 속도:** 약 45 m/s(Wikipedia *Panzerfaust*). 중력만 있는 포물선으로 계산한 발사각: 30 m 4.18°, 60 m 8.45°, 80 m 11.40°.
- **모델 보정:** 원본 모델의 구멍 높이로 계산하면 30 m 구멍이 Korn보다 낮았다(발사각 음수). 그래서 가늠자 판만 세로로 다시 매핑해 위 발사각이 되게 했다. 구멍 아래 V 끝 높이: 1.87/6.03/9.35 → 5.22/7.63/9.32 cm.
- **잡는 법:** 겨드랑이에 끼우거나 어깨에 얹는다. 1인칭에서는 눈이 가늠자 24 cm 뒤에 오고 관은 눈 아래로 지나간다(어깨 쪽). 비조준은 정조준에서 뒤 4·오른쪽 5·아래 7 cm 내린 자세다.
- **일회용:** 쏘면 탄두가 빠진 관만 남는다. 재장전 = 빈 관을 내리고 새 관을 올린 뒤 가늠자를 세운다. 가늠자를 세워야 격발 장치가 풀리는 안전장치다(Tank Archives 교범 소개).
- **탄두 꼬리:** 관 안에 들어가 있던 나무 꼬리대와 스프링 강판 날개 4장은 원본 모델에 없어, 발사체 메시에만 단순한 형상으로 넣었다(크기는 어림값).

## 10. Panzerschreck (RPzB 54, 방패) — 2026-11-21 구현
- **구조:** 8.8 cm 강철 관. 앞·뒤 가늠자가 있다. 후기형은 관에 강철 방패를 물렸고, 방패의 관찰 창은 사수 **왼쪽**에 있다. 방아쇠와 장전 레버는 전기 격발식이다(자석 막대가 코일을 지나며 전류를 만든다).
- **장전:** 로켓을 관 **뒤**로 넣으면 걸쇠에 걸리고, 로켓 꼬리가 관 뒤쪽 전선 단자에 닿는다. 교범상 장전은 부사수가 맡는다.
- **로켓:** 약 3.2 kg(7 lb) 성형작약. 머리에 신관, 꼬리에 원형 날개가 있다. 독일 측 유효 사거리는 120~150 m다. 초속은 en.wikipedia 기준 약 110 m/s다(de.wikipedia는 다른 값).
- **1인칭 구현:**
  - 견착하고, 정조준 눈 위치는 방패 창 가운데 40 cm 뒤다. 로켓은 단품 모델(65 cm)을 원본 로켓 자리에 넣었다.
  - 영점은 100/150/200 m다. 발사각은 각각 2.33°, 3.49°, 4.67°(110 m/s, 포물선)다.
  - 재장전은 견착을 유지한 채 진행한다. 로켓이 뒤에서 들어와 걸리고, 배선 연결·어깨 두드림 신호가 작은 흔들림으로 나타난다. 이어서 사수가 왼손으로 장전 레버를 젖힌다.
- **찾지 못한 것:**
  - 가늠쇠 눈금의 실제 모양과 높이(100/150/200 m 표시)는 찾지 못했다. 그래서 '창 가운데 = 조준점, 영점별로 관을 발사각만큼 든다'로 만들었다.
  - 레버 젖힘과 장전의 순서는 자료로 확인하지 못했다.
  - 장전 레버로 정한 부품(방아쇠 앞 사각 고리)도 모델 모양을 보고 추정한 것이다.
- **출처:**
  - [당시] TM-E 30-451 *German antitank weapons*(1945), Lone Sentry 전재본 — https://lonesentry.com/manuals/tme30/ch7sec2sub7.html
  - [2차] Wikipedia *Panzerschreck* — https://en.wikipedia.org/wiki/Panzerschreck
  - [2차] Wikipedia(독일어) *Raketenpanzerbüchse* — https://de.wikipedia.org/wiki/Raketenpanzerb%C3%BCchse

## 11. MG34(들고 쏘기만) / MG42(설치 사격만) — 2026-11-22 조사·구현
- **사용자 지정:** MG34 는 설치 사격 없이 돌격소총처럼(허리·견착), 재장전 = 50발 탄띠 드럼(Gurttrommel 34) 교체. MG42 는 설치 사격만: 평소엔 총을 어깨에 메고 왼손에 탄약 상자, 설치하면 상자와 250발 탄띠가 연결된 채 바닥에 놓임, 설치된 총 가까이에서 스페이스 = 사격 준비 자세, 재장전 = 새 상자를 꺼내 탄띠 연결. 쏠수록 상자 안 탄이 줄고 탄띠가 줄자처럼 감겨 올라가며 흔들림(물리). 설치 동작 자체는 아직 만들지 않음.
- **MG34 드럼 장전(당시 미군 정보 교범 1943):** 드럼 뚜껑 멈치를 누르고 열어 탄띠 꼬리표를 뺌 -> 꼬리표를 (왼쪽) 급탄구에 넣음(고리 열린 쪽 아래) -> 드럼 앞 좁은 끝을 급탄판 아래 돌기에 걸고 -> 뒤쪽을 총 쪽으로 돌려 스프링 멈치가 걸리게 -> 그다음은 탄띠 상자와 같음: 덮개는 열거나 닫은 채, 첫 탄이 급탄 갈퀴 3개에 걸릴 때까지 탄띠를 당김 -> 오른쪽 장전 손잡이를 '끝까지' 당겼다가 앞으로. 방아쇠 위 E = 단발, 아래 D = 연발. 연발은 '튀는 경향'이 커 부사수가 양각대를 누름.
- **MG34 들고 쏘기:** 당시 가죽 멜빵을 '전진하며 허리에서 쏠 때' 받침으로 썼다는 기록과 사진(bergflak, 동부전선 사진). 교범에 있었는지·흔했는지는 자료가 엇갈림(포럼 증언 양쪽) -> 짧은 연사, 개머리판은 옆구리(허리) 또는 어깨.
- **MG42 탄띠 장전(같은 교범):** 덮개 뒤끝 멈치를 앞으로 밀어 덮개를 엶 -> 꼬리표를 왼쪽 급탄구에(고리 열린 쪽 아래) -> 첫 탄이 갈퀴에 걸릴 때까지(약 탄 3개 폭) 당김(급탄구를 덮을 만큼은 아님) -> 쏠 때가 되면 장전 손잡이를 끝까지 당겼다가 '딸깍' 소리가 날 때까지 앞으로. 발사 속도 분당 1,050~1,350, 양각대 경기관총 25.5 lb, 연발 250발마다 총열 교환.
- **탄약 상자(Patronenkasten 34/41):** 7.92mm 탄띠 300발(50발 탄띠 묶음), 상자 손잡이로 들고 다님, 운반 끈(Tragegurt 34). 사용자 지정에 따라 250발 탄띠 1줄로.
- **출처:**
  - [당시] MIS Special Series No.14 *German Infantry Weapons* (1943) MG34 — https://www.lonesentry.com/manuals/german-infantry-weapons/mg34-machine-gun.html
  - [당시] 같은 교범 MG42 — https://3g.lonesentry.com/manuals/german-infantry-weapons/mg42-machine-gun.html
  - [당시] TM E9-206A *German 7.9mm Dual Purpose Machine Gun MG34* (1943) — https://www.brpguns.com/content/28653950-War-Department-technical-Manual-tm-e9-206a-german-7-9-Mm-Dual-Purpose-Machine-Gun-Mg-34-13-April-1943.pdf
  - [수집가] bergflak *MG34 and MG42 slings* — https://www.bergflak.com/Mgrem.html
  - [수집가] mp44.nl *Patronenkasten 34/41* — https://www.mp44.nl/equipment/patronenkasten.htm , fjm44 상자·끈 — https://fjm44.com/articles/mg-3442-ammunition-box-patronenkasten-34-arr-42/
  - [2차] Wikipedia *MG 34*, *MG 42*; Athlon Outdoors *Full-Auto Sentry: MG34* — https://athlonoutdoors.com/article/german-mg34-machine-gun/
- **MG34 드럼 장전 때 급탄 덮개(2026-11-22 보강, 사용자 지적):** 드럼(바구니)을 단 채 장전하려면 덮개를 열고 탄띠 앞 고리들을 급탄판에 놓은 뒤 덮개를 닫고 탄을 멈춤까지 당김(드럼을 먼저 달면 덮개를 열어야 함) - mg42.us 포럼 *Basic MG-34 questions*(https://www.mg42.us/viewtopic.php?t=12714). 드럼은 덮개를 든 뒤 급탄판 왼쪽에 담 - Athlon Outdoors(https://athlonoutdoors.com/article/german-mg34-machine-gun/). 드럼 앞 끝을 걸고 뒤를 돌려 끼움, 탄을 갈퀴에 걸릴 때까지 당긴 뒤 장전 손잡이 - MIS 1943(위). -> 구현 순서: 덮개 열기 -> 드럼 빼기 -> 새 드럼 걸기(앞 고리, 뒤 돌림) -> 탄띠 앞 고리가 급탄판에 -> 덮개 닫기 -> 오른쪽 장전 손잡이 당겼다 앞으로.
