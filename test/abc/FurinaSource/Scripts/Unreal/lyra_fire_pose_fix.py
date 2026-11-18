"""Lyra 에디터(`py <파일>`, PIE 중지 상태): 3인칭 '사격 자세'(FireHold)만 고친다. 대기(휴식) 자세는 FireW=0 이라 그대로.
측정(Data/lyra_fire_pose_base.json, 폰 로컬 x 앞/y 오른쪽/z 위): 개머리판 끝 (-0.2, 2.9, 26.9) - 몸 중심선 가슴 안쪽에 박혀 있고 오른쪽 어깨 관절(1.7, 9.1, 29.5)과 떨어져 있었다.
수정(가중치 FireWN = FireW x NotAim, 3인칭 TpW 는 TpOff/TwAng 에서 곱해짐):
 (1) 총 위치: TpD 뒤에 TpD2 = TpD + FIRE_D x FireWN  (FIRE_D 는 조준 좌표 X=왼쪽, Y=앞, Z=위 cm)  -> 개머리판을 오른쪽 어깨 앞(어깨 주머니)으로
 (2) 상체 비틀기: TwAng.B = rad(-BASE_DEG) + rad(FIRE_TW_DEG) x FireWN  -> 사격 중에는 왼쪽 어깨 앞/오른쪽 어깨 뒤로(기본 14도 오른쪽-앞 비틀기에 20도를 더해 순 6도 왼쪽-앞)
값은 아래 상수 또는 Data/fire_pose_fix.json({"d":[x,y,z],"tw":deg}) 로 바꾼다. 여러 번 실행해도 노드는 한 번만 만들고 값만 갱신. -> Data/lyra_fire_pose_fix.json"""
import unreal, json, math, os, traceback
D_DIR = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
OUT = D_DIR + r'\lyra_fire_pose_fix.json'
FIRE_D = [-5.0, 3.1, 0.6]; FIRE_TW_DEG = 20.0; BASE_DEG = 14.0
if os.path.exists(D_DIR + r'\fire_pose_fix.json'):
    _o = json.load(open(D_DIR + r'\fire_pose_fix.json')); FIRE_D = _o.get('d', FIRE_D); FIRE_TW_DEG = _o.get('tw', FIRE_TW_DEG)
R = {'FIRE_D': FIRE_D, 'FIRE_TW_DEG': FIRE_TW_DEG}
U = '/Script/ControlRig.RigUnit_'
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    names = lambda: {str(n.get_node_path()) for n in g.get_nodes()}
    have = names(); R['had'] = sorted(x for x in ('FireWN', 'FireTw', 'TwB', 'FireDV', 'TpD2') if x in have)
    for need in ('FireW', 'NotAim', 'TpD', 'TpOff', 'TwAng'): assert need in have, 'missing node ' + need
    def mk(typ, nm, x, y):
        if nm not in names(): c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(x, y), nm)
    mk('MathFloatMul', 'FireWN', 0, 0); mk('MathFloatMul', 'FireTw', 0, 100); mk('MathFloatAdd', 'TwB', 0, 200)
    mk('MathVectorScale', 'FireDV', 0, 300); mk('MathVectorAdd', 'TpD2', 0, 400)
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:60]])
    if 'TpD2' not in R['had']:
        link('FireW.Result', 'FireWN.A'); link('NotAim.Result', 'FireWN.B')
        link('FireWN.Result', 'FireTw.A'); link('FireTw.Result', 'TwB.B'); link('TwB.Result', 'TwAng.B')
        link('FireWN.Result', 'FireDV.Factor')
        try: c.break_link('TpD.Result', 'TpOff.Value')
        except Exception as e: L.append(['break', str(e)[:60]])
        link('TpD.Result', 'TpD2.A'); link('FireDV.Result', 'TpD2.B'); link('TpD2.Result', 'TpOff.Value')
    R['links'] = L
    S = [c.set_pin_default_value('FireTw.B', '%.6f' % math.radians(FIRE_TW_DEG), True, False),
         c.set_pin_default_value('TwB.A', '%.6f' % math.radians(-BASE_DEG), True, False),
         c.set_pin_default_value('FireDV.Value', '(X=%.4f,Y=%.4f,Z=%.4f)' % tuple(FIRE_D), True, False)]
    R['set'] = [bool(x) for x in S]
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_FIRE_POSE_FIX', R.get('saved'), R.get('error', '')[-200:])
