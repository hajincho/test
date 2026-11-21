"""역사 무기 사격 효과 수치(2026-11-21): 탄약 장약량·탄두·총 무게로 반동/화면 흔들림/총구 화염/연기 배율 -> Data/hist_fx.json
출처(자세한 표는 Motion/DE_FP_MOTION_RESEARCH.md 9절):
  [1] de.wikipedia 7,92×57 mm 표: s.S.-Patrone(1933) 탄두 12.8 g, 장약 2.75~2.85 g, v0 755 m/s(Kar98k 60 cm 총열)
  [2] en.wikipedia Karabiner 98k: 3.7~4.1 kg, 총열 600 mm, 760 m/s / TM-E 30-451(1945): Kar98k 약 9 lb
  [3] en.wikipedia Gewehr 43: 4.4 kg, 총열 550 mm, 746~776 m/s, 가스 작동
  [4] en.wikipedia 7.92×33mm Kurz: 탄두 8.1 g, 탄 전체 17.05 g, 685 m/s / StG 44: 4.6 kg(장전 5.13 kg), 총열 419 mm
  [5] en.wikipedia MP 40: 3.97 kg, 총열 251 mm, 400 m/s / TM-E 30-451: 9 lb(탄창 없이), 순환 500발/분
  [6] en.wikipedia Walther P38: 960 g, 총열 125 mm, 320 m/s / Luger: 871 g, 100 mm, 350~400 m/s / Walther PP: 660 g(7.65), 98 mm, 320 m/s
      .32 ACP: 71 gr(4.6 g) FMJ / de.wikipedia 9×19: 원래 탄두 124 gr(약 8 g)
  [7] en.wikipedia Free recoil: v_총 = (m_탄 v_탄 + m_장약 v_가스)/M, E = ½Mv² (예시 7×57 단기제 2.75 g, 가스 1,585 m/s)
  [8] en.wikipedia Muzzle flash: 화염 크기 = 장약 연소 에너지·덜 탄 분출물 양·총구 장치에 좌우. s.S. 는 짧은 총열에서 S 보다 화염이 적음(Kar98k 문서)
추정(출처에 숫자 없음, 그렇다고 표시): 7.92×33 장약 1.57 g, 9×19 Pist.Patr.08 장약 0.36 g, 7.65 장약 0.17 g, MP38 무게 4.1 kg,
  조준경+마운트 무게(ZF39 0.6, ZF41 0.3, ZF4 0.5 kg), 가스 속도(소총 1,585 m/s = [7] 예시, Kurz 1.75 v, 권총탄 1.5 v)
게임 환산(물리값을 게임 배율로 바꾸는 규칙, 가정):
  반동 배율 = 총의 자유 반동 속도 / M4(1.8 m/s, gen_ballistics.py 의 기준)   -> 기존 BP 의 수직·수평 반동에 곱함(권총 한손은 1.5배 더)
  흔들림 배율 = sqrt(반동 에너지 / M4 5.5 J)
  화염 크기 = sqrt(장약/2.8 g) × (600 mm/총열)^0.3,  화염 길이비: 소총 1.0, 기관단총 0.75, 권총 0.55
  연기 농도 = sqrt(장약/2.8 g), 연기 지속(초) = 1.6 + 1.6 × 농도"""
import json, math, os, sys
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', 'Data')
V_REF = (0.004 * 900 + 0.0016 * 1.75 * 900) / 3.4; E_REF = 0.5 * 3.4 * V_REF ** 2
W = {   # 키: (탄두 g, 탄속 m/s, 장약 g, 가스 m/s, 총 kg, 총열 mm, 종류, 탄약 이름)
    'kar98k':      (12.8, 755, 2.80, 1585, 3.9, 600, 'rifle', '7.92x57 s.S.'),
    'kar98k_zf39': (12.8, 755, 2.80, 1585, 4.5, 600, 'rifle', '7.92x57 s.S.'),
    'kar98k_zf41': (12.8, 755, 2.80, 1585, 4.2, 600, 'rifle', '7.92x57 s.S.'),
    'g43':         (12.8, 760, 2.80, 1585, 4.4, 550, 'rifle', '7.92x57 s.S.'),
    'g43_zf4':     (12.8, 760, 2.80, 1585, 4.9, 550, 'rifle', '7.92x57 s.S.'),
    'stg44':       (8.1, 685, 1.57, 1.75 * 685, 5.13, 419, 'smg', '7.92x33 Kurz'),
    'mp40':        (8.0, 400, 0.36, 1.5 * 400, 3.97, 251, 'smg', '9x19 Pist.Patr.08'),
    'mp38':        (8.0, 400, 0.36, 1.5 * 400, 4.1, 251, 'smg', '9x19 Pist.Patr.08'),
    'p38':         (8.0, 320, 0.36, 1.5 * 320, 0.96, 125, 'pistol', '9x19 Pist.Patr.08'),
    'p08':         (8.0, 375, 0.36, 1.5 * 375, 0.871, 100, 'pistol', '9x19 Pist.Patr.08'),
    'pp':          (4.6, 320, 0.17, 1.5 * 320, 0.66, 98, 'pistol', '7.65 Browning'),
}
LEN = {'rifle': 1.0, 'smg': 0.75, 'pistol': 0.55}
out = {'ref': {'v_m4_ms': round(V_REF, 3), 'e_m4_j': round(E_REF, 2)}, 'weapons': {}}
for k, (mp, vp, mc, vc, M, L, kind, ammo) in W.items():
    imp = (mp * vp + mc * vc) / 1000.0; v = imp / M; E = 0.5 * M * v * v
    flash = math.sqrt(mc / 2.8) * (600.0 / L) ** 0.3; smoke = math.sqrt(mc / 2.8)
    out['weapons'][k] = dict(ammo=ammo, impulse_ns=round(imp, 3), recoil_v_ms=round(v, 3), recoil_e_j=round(E, 2),
                             recoil=round(v / V_REF, 3), shake=round(math.sqrt(E / E_REF), 3), flash=round(flash, 3), flash_len=LEN[kind],
                             smoke=round(smoke, 3), smoke_life=round(1.6 + 1.6 * smoke, 2), kind=kind)
json.dump(out, open(os.path.join(D, 'hist_fx.json'), 'w'), indent=1)
for k, v in out['weapons'].items(): print(k, v)
