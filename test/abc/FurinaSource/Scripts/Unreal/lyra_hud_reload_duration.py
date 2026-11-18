"""Lyra 에디터(`py <파일>`, 새로 시작한 에디터에서 이 스크립트만 한 번): HUD 재장전 점 채우기가 고정 3.0초로 나누던 것을 실제 재장전 시간으로 바꾼다.
 긴급 재장전은 2.0초, 전술 재장전은 3.69초가 됐는데 BP_FurinaHUD 는 경과 시간 / 3.0 이라 점이 일찍 차거나(전술) 끝까지 안 찼다(긴급).
 ReloadP = FClamp(경과 / FMax(경과 + 남은 시간, 0.01), 0, 1)   (타이머가 없으면 경과 = 남은 = -1 -> 합이 음수 -> 0.01 로 올려 -100 -> 0)
 노드: FHUD2_Remaining, FHUD2_Sum, FHUD2_Max.  FHUD_ReloadDiv.B 를 FHUD2_Max 로 연결.   -> Data/lyra_hud_reload_duration.json"""
import unreal, json, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hud_reload_duration.json'
R = {}
def run():
    b = unreal.load_asset('/Game/Furina/FP/BP_FurinaHUD'); e = unreal.BlueprintGraphEditor.get_graph_editor_by_name(b, 'EventGraph')
    N = {n.get_name(): n for n in e.list_all_nodes()}
    for need in ('FHUD_ReloadElapsed', 'FHUD_ReloadDiv', 'FHUD_ReloadClamp'): assert need in N, need
    CONN = unreal.BlueprintGraphPinLibrary.try_create_connection
    def pin(n, name, out=False):
        p = n.find_output_pin(name) if out else n.find_input_pin(name)
        assert p is not None and p.is_valid(), (n.get_name(), name); return p
    def link(a, c): assert a is not None and c is not None and a.is_valid() and c.is_valid() and CONN(a, c), ('link', a, c)
    K = '/Script/Engine.KismetMathLibrary:'
    if 'FHUD2_Max' in N: R['note'] = 'exists'
    else:
        tel = N['FHUD_ReloadElapsed']; dv = N['FHUD_ReloadDiv']
        rem = e.add_call_function_node('/Script/Engine.KismetSystemLibrary:K2_GetTimerRemainingTime'); rem.rename('FHUD2_Remaining')
        for src in list(pin(tel, 'Object').list_connected_pins()): link(src, pin(rem, 'Object'))
        pin(rem, 'FunctionName').set_pin_value('FurinaFinishReload')
        sm = e.add_call_function_node(K + 'Add_DoubleDouble'); sm.rename('FHUD2_Sum')
        link(pin(tel, 'ReturnValue', True), pin(sm, 'A')); link(pin(rem, 'ReturnValue', True), pin(sm, 'B'))
        mx = e.add_call_function_node(K + 'FMax'); mx.rename('FHUD2_Max')
        link(pin(sm, 'ReturnValue', True), pin(mx, 'A')); pin(mx, 'B').set_pin_value('0.01')
        pin(dv, 'B').break_pin_links(); link(pin(mx, 'ReturnValue', True), pin(dv, 'B'))
        R['added'] = True
    del e, N
    import gc; gc.collect()
    unreal.BlueprintEditorLibrary.compile_blueprint(b); R['status'] = str(b.get_editor_property('status'))
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(b, False) if b.get_editor_property('status') != unreal.BlueprintStatus.BS_ERROR else 'not saved (error)'
    del b
try: run()
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HUD_RELOAD_DURATION', R.get('status'), R.get('error', ''))
import gc; gc.collect()
