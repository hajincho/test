"""2단계 B: 기존 사격/재장전 체인을 권총 장착 여부(FurinaPistolOn)에 따라 분기.  p200_graph_a.py 실행 뒤에 실행."""
import unreal, json, traceback
exec(open(r'L:\FurinaSource\Scripts\Unreal\p200_graph_lib.py', encoding='utf-8').read())
R = {'log': []}
def step(n, f):
    try: R['log'].append([n, f()])
    except Exception: R['log'].append([n, 'ERROR ' + traceback.format_exc()[-900:]])
def vec(x, y, z): return mkvec(float(x), float(y), float(z))
def retarget(node_name, pin_name, new_pin):
    n = node(node_name); p = n.find_input_pin(pin_name); p.break_pin_links(); link(new_pin, p)
def src_of(node_name, pin_name):
    p = node(node_name).find_input_pin(pin_name); c = p.list_connected_pins(); assert c, 'no source %s.%s' % (node_name, pin_name); return c[0]
def pistol(): return is_active('FurinaPistolOn')
# (1) Possessed: 타이머 시작
def possess():
    at = node('K2Node_FP_AttachCam'); t = timer('FurinaP200Tick', 0.008, True)
    old = list(at.find_then_pin().list_connected_pins()); at.find_then_pin().break_pin_links()
    link(at.find_then_pin(), t.find_execute_pin())
    for p in old: link(t.find_then_pin(), p)
    return 'possess ok %d' % len(old)
# (2) 권총은 단발 고정: 기존 Semi 판정에 OR
def semi():
    r = node('FM_IsSemi').find_result_pin(); o = bor(r, pistol())
    retarget('FM_NotSemi', 'A', o); retarget('FM_Delay', 'bPickA', o); return 'semi ok'
# (3) 총구/탄피 위치 (소총 로컬 좌표)
def points():
    pv = [('K2Node_FPF_Muzzle', (0.0, 11.03, 4.63), (-0.0, 40.515, 3.383)), ('M4_FlashPoint', (0.0, 11.03, 4.63), (-0.0, 40.515, 3.383)), ('M4_CasePoint', (-1.3, -0.77, 4.83), (-2.2, -3.5, 4.5))]
    for name, a, b in pv:
        s = fn(KML + 'SelectVector', 'Sel' + name); link(vec(*a), s.find_input_pin('A')); link(vec(*b), s.find_input_pin('B')); link(pistol(), s.find_input_pin('bPickA'))
        retarget(name, 'Location', s.find_result_pin())
    return 'points ok'
# (4) 탄퍼짐/반동 배율
def spread_recoil():
    cone_src = src_of('K2Node_FPF_Cone', 'ConeHalfAngleInDegrees'); m = mulf(cone_src, selfloat(2.5, 1.0, pistol())); retarget('K2Node_FPF_Cone', 'ConeHalfAngleInDegrees', m)
    rec_src = src_of('K2Node_FPF_RecV', 'B'); mr = mulf(rec_src, selfloat(2.2, 1.0, pistol()))
    retarget('K2Node_FPF_RecV', 'B', mr); retarget('K2Node_FPF_RecH', 'B', mr); return 'spread/recoil ok'
# (5) 총알/탄피 클래스
def classes():
    out = []
    for path in (KML + 'SelectClass', '/Script/Engine.KismetSystemLibrary:SelectClass'):
        try:
            sc = fn(path, 'SelBulletCls'); break
        except Exception as e: out.append('try ' + path + ' failed')
    else: raise RuntimeError('SelectClass not found')
    sc.find_input_pin('A').set_pin_value('/Game/Furina/P200/BP_P220Bullet.BP_P220Bullet_C'); sc.find_input_pin('B').set_pin_value('/Game/Furina/FP/BP_FurinaBullet.BP_FurinaBullet_C'); link(pistol(), sc.find_input_pin('bPickA'))
    sp = node('K2Node_FPF_Spawn'); link(sc.find_result_pin(), sp.find_input_pin('Class'))
    cc = fn(path, 'SelCaseCls'); cc.find_input_pin('A').set_pin_value('/Game/Furina/P200/BP_P220Case.BP_P220Case_C'); cc.find_input_pin('B').set_pin_value('/Game/Furina/M4/BP_223Case.BP_223Case_C'); link(pistol(), cc.find_input_pin('bPickA'))
    link(cc.find_result_pin(), node('M4_CaseSpawn').find_input_pin('ActorClass'))
    out.append([str(sc.find_input_pin('A').get_pin_value())[:60], str(node('K2Node_FPF_Spawn').find_input_pin('Class').get_pin_value())[:60]]); return out
# (6) 머즐 플래시 크기
def flash():
    s = fn(KML + 'SelectVector', 'SelFlashScale'); link(vec(0.55, 0.55, 0.55), s.find_input_pin('A')); link(vec(1, 1, 1), s.find_input_pin('B')); link(pistol(), s.find_input_pin('bPickA'))
    retarget('M4_FlashTransform', 'Scale', s.find_result_pin()); return 'flash ok'
# (7) 탄창 크기/재장전 시간
def mag():
    m = selint(8, 20, pistol()); retarget('M4_NotFull', 'B', m); retarget('TFP_MagRoom', 'A', m)
    t = node('M4_ReloadTimer').find_input_pin('Time'); t.break_pin_links(); link(selfloat(2.3, 3.0, pistol()), t); return 'mag ok'
# (8) 교체 중 사격 금지
def gate():
    src = src_of('M4_FireGate', 'Condition'); g = band(src, bnot(is_active('FurinaSwapping'))); retarget('M4_FireGate', 'Condition', g); return 'gate ok'
# (9) 권총일 때 소총 탄창 연출 중지
def fmg():
    fu = node('FMG_Update'); old = list(fu.find_then_pin().list_connected_pins()); fu.find_then_pin().break_pin_links()
    b = branch(pistol()); link(fu.find_then_pin(), b.find_execute_pin())
    for p in old: link(b.find_else_pin(), p)
    return 'fmg ok %d' % len(old)
# (10) 사격 끝에서 슬라이드 킥
def fx():
    last = node('M4_CaseFinish'); b = branch(pistol()); link(last.find_then_pin(), b.find_execute_pin()); t = timer('FurinaPistolFx', 0.001); link(b.find_then_pin(), t.find_execute_pin()); return 'fx ok'
for name, f in (('possess', possess), ('semi', semi), ('points', points), ('spread_recoil', spread_recoil), ('flash', flash), ('mag', mag), ('gate', gate), ('fmg', fmg), ('fx', fx)):
    step(name, f)
BEL.compile_blueprint(bp); R['status'] = str(bp.get_editor_property('status'))
R['errors'] = [str(x.get_name()) for x in ed.list_nodes_with_errors()][:20] if hasattr(ed, 'list_nodes_with_errors') else []
print('P200_GRAPH_B', json.dumps(R, default=str, ensure_ascii=False)[:4000])

