"""에디터(편집 전용, PIE 아님, 2026-11-22): CR_FurinaSecondary 를 캐릭터 몸 비율에 맞게 -> Saved/CRClassLengths.json
 문제(병과 캐릭터 3인칭 다리가 어색): 애니메이션(푸리나용)의 뼈 이동이 푸리나 뼈 길이로 풀리고, 이 컨트롤 릭의 다리 IK 도 허벅지 39.40·정강이 41.22cm,
   팔 IK 21.14·18.02cm, 손가락 IK 길이를 푸리나 값으로 고정 -> 클레(125cm)는 다리가 늘어나 무릎이 굽고 발이 바닥에 묻힘, 케이아(184cm)는 줄어듦.
 수정(그래프 맨 앞 + 상수 교체, 푸리나 메시에서는 값이 그대로라 변화 없음):
  1) BeginExecution 바로 뒤: 몸·손가락 뼈 51개의 로컬 이동 = 그 메시의 기준 자세(초기값, ABP 의 'Set Initial Transforms From Mesh')
     Hips(뿌리) 이동 = 애니메이션 값 × (이 메시 Hips 높이 / 푸리나 Hips 높이 92.76cm)
  2) 다리·팔·손가락 IK 의 ItemA/ItemBLength = 기준 자세에서 관절 사이 거리
  3) 경사 자세 게이트(CGateLo/Hi: 엉덩이 높이 60~75 / 112~130cm) 입력 = 엉덩이 높이 / 위 비율"""
import json, traceback
from pathlib import Path
import unreal
ROOT = Path(unreal.Paths.project_dir()).resolve(); FS = ROOT / 'FurinaSource'; R = {'fail': []}
FURINA_HIPS_Z = 92.76


def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    N = {str(n.get_node_path()): n for n in g.get_nodes()}
    if 'CL_Ratio' in N: return 'exists'
    def S(n): return getattr(unreal, n).static_struct().get_path_name()
    def add(unit, name, x, y, **d):
        node = c.add_unit_node_from_struct_path(S(unit), 'Execute', unreal.Vector2D(x, y), name)
        if not node: R['fail'].append('add ' + name); return name
        for k, v in d.items():
            if not c.set_pin_default_value('%s.%s' % (name, k), v, True, False): R['fail'].append('def %s.%s' % (name, k))
        return name
    def link(a, b):
        if not c.add_link(a, b, False): R['fail'].append('link %s -> %s' % (a, b))
    B = lambda n: '(Type=Bone,Name="%s")' % n
    X0, Y0 = -6000, -6000
    # 비율 r = 초기 Hips 높이 / 푸리나
    add('RigUnit_GetTransform', 'CL_HipsInit', X0, Y0, Item=B('Hips'), Space='GlobalSpace', bInitial='True')
    add('RigUnit_MathFloatDiv', 'CL_Ratio', X0 + 300, Y0, B=str(FURINA_HIPS_Z)); link('CL_HipsInit.Transform.Translation.Z', 'CL_Ratio.A')
    # 실행: Begin -> Hips 비율 -> 몸 뼈 로컬 이동 복원 -> (원래 첫 노드)
    begin = [k for k in N if 'BeginExecution' in k][0]
    first = [str(t.get_pin_path()) for p in N[begin].get_pins() for t in p.get_linked_target_pins()]
    for t in first: c.break_link('%s.ExecuteContext' % begin, t) or c.break_link('%s.ExecutePin' % begin, t)
    add('RigUnit_GetTransform', 'CL_HipsAnim', X0, Y0 + 200, Item=B('Hips'), Space='GlobalSpace')
    add('RigUnit_MathVectorScale', 'CL_HipsScaled', X0 + 300, Y0 + 200); link('CL_HipsAnim.Transform.Translation', 'CL_HipsScaled.Value'); link('CL_Ratio.Result', 'CL_HipsScaled.Factor')
    add('RigUnit_SetTranslation', 'CL_HipsSet', X0 + 600, Y0 + 200, Item=B('Hips'), Space='GlobalSpace', bPropagateToChildren='True'); link('CL_HipsScaled.Result', 'CL_HipsSet.Value')
    prev = 'CL_HipsSet'
    ok = False
    for pin in ('ExecuteContext', 'ExecutePin'):
        if c.add_link('%s.%s' % (begin, pin), 'CL_HipsSet.ExecutePin', False): ok = True; break
    if not ok: R['fail'].append('begin link')
    body = [n.replace(' ', '-') for n in json.loads((FS / 'Data' / 'class_infantry_build.json').read_text(encoding='utf-8'))['body_bones'] if n != 'Hips']
    for i, b in enumerate(body):
        y = Y0 + 400 + i * 160
        add('RigUnit_GetTransform', 'CL_I_' + b, X0, y, Item=B(b), Space='LocalSpace', bInitial='True')
        add('RigUnit_SetTranslation', 'CL_S_' + b, X0 + 400, y, Item=B(b), Space='LocalSpace', bPropagateToChildren='True')
        link('CL_I_%s.Transform.Translation' % b, 'CL_S_%s.Value' % b)
        link('%s.ExecutePin' % prev, 'CL_S_%s.ExecutePin' % b); prev = 'CL_S_' + b
    for t in first: link('%s.ExecutePin' % prev, t)
    R['restored'] = len(body); R['first'] = first
    # IK 길이 = 기준 자세 관절 거리
    iks = {k: n for k, n in N.items() if 'TwoBoneIK' in str(n.get_node_title())}
    for k, n in iks.items():
        pv = {str(p.get_name()): str(p.get_default_value()) for p in n.get_pins()}
        def item(s): return s.split('Name="')[1].split('"')[0]
        a, b, e = item(pv['ItemA']), item(pv['ItemB']), item(pv['EffectorItem'])
        for nm, (p, q) in (('A', (a, b)), ('B', (b, e))):
            gp, gq, dn = 'CL_%s_%sp' % (k, nm), 'CL_%s_%sq' % (k, nm), 'CL_%s_%sd' % (k, nm)
            add('RigUnit_GetTransform', gp, X0 - 900, Y0, Item=B(p), Space='GlobalSpace', bInitial='True')
            add('RigUnit_GetTransform', gq, X0 - 900, Y0 + 150, Item=B(q), Space='GlobalSpace', bInitial='True')
            add('RigUnit_MathVectorDistance', dn, X0 - 600, Y0); link(gp + '.Transform.Translation', dn + '.A'); link(gq + '.Transform.Translation', dn + '.B')
            link(dn + '.Result', '%s.Item%sLength' % (k, nm))
        R.setdefault('ik', []).append([k, a, b, e])
    # 경사 게이트: 엉덩이 높이 / r
    add('RigUnit_MathFloatDiv', 'CL_CHeightN', X0 + 800, Y0); link('CHeight.Result', 'CL_CHeightN.A'); link('CL_Ratio.Result', 'CL_CHeightN.B')
    for gate in ('CGateLo', 'CGateHi'):
        c.break_link('CHeight.Result', gate + '.Value'); link('CL_CHeightN.Result', gate + '.Value')
    unreal.BlueprintEditorLibrary.compile_blueprint(cr); cr.recompile_vm()
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
    return 'ok'


try: R['result'] = run()
except Exception: R['error'] = traceback.format_exc()[-1500:]
R['done'] = True; (ROOT / 'Saved' / 'CRClassLengths.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
print('CR_CLASS_LEN', json.dumps(R, ensure_ascii=False)[:2000])
