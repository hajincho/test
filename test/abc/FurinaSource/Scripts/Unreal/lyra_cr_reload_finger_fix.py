"""Lyra 에디터(`py <파일> [Blend]`, 기본 10): 재장전 중 손가락/엄지 문제 2개 수정 (측정: Data/lyra_reload_finger_probe_f1.json)
 (1) 엄지 꿈틀: 빈 탄창 재장전 끝에서 엄지 고정(ThSet0-2, 가중치 ReloadSm)이 RifleReload 곡선이 0 이 되면서 풀리고, 몽타주 블렌드 아웃 포즈로 0.3초 동안
     엄지 2마디가 최대 45도 움직였다가 돌아왔다(전술은 처음부터 끝까지 고정이라 이상 없음).  -> 1인칭(RlFpW) 소총(권총 아님: 1-PistW)에서는 엄지 가중치를 항상 1 로:
     ThW = Max(ReloadSm, RlFpW x (1 - PistW))  -> ThSet0/1/2.Weight
 (2) 손잡이 당기러 갈 때 손가락이 튐: HandleFp 곡선(0->1 이 0.12초에 올라감)을 그대로 쓰면 손가락이 0.06초에 25~30도 튄다 -> AccumulateLerp(Blend)로 부드럽게:
     RlHSm.TargetValue <- RlHC.Value,  RlHInv.Value <- RlHSm.Result
 노드: ThNotPist, ThFp, ThW, RlHSm.   -> Data/lyra_cr_reload_finger_fix.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_reload_finger_fix.json'
U = '/Script/ControlRig.RigUnit_'
nums = []
for a in sys.argv[1:]:
    try: nums.append(float(a))
    except ValueError: pass
BLEND = nums[0] if nums else 10.0
R = {'blend': BLEND}
def run():
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); c = cr.get_controller_by_name('RigVMModel') or cr.get_controller(); g = c.get_graph()
    def nodes(): return {str(n.get_node_path()): n for n in g.get_nodes()}
    N = nodes()
    for need in ('ThSet0', 'ThSet1', 'ThSet2', 'ReloadSm', 'RlFpW', 'PistW', 'RlHC', 'RlHInv'): assert need in N, 'missing ' + need
    L = []
    def link(a, b):
        try: L.append([a, b, bool(c.add_link(a, b))])
        except Exception as e: L.append([a, b, 'err ' + str(e)[:80]])
    def mk(typ, nm, **pins):
        if nm not in nodes():
            c.add_unit_node_from_struct_path(U + typ, 'Execute', unreal.Vector2D(0, 0), nm)
            for k, v in pins.items(): c.set_pin_default_value('%s.%s' % (nm, k), v, True, False)
    if 'ThW' not in N:
        mk('MathFloatRemap', 'ThNotPist', SourceMinimum='0', SourceMaximum='1', TargetMinimum='1', TargetMaximum='0', bClamp='True'); mk('MathFloatMul', 'ThFp'); mk('MathFloatMax', 'ThW')
        link('PistW.Result', 'ThNotPist.Value'); link('RlFpW.Result', 'ThFp.A'); link('ThNotPist.Result', 'ThFp.B'); link('ReloadSm.Result', 'ThW.A'); link('ThFp.Result', 'ThW.B')
        for i in range(3):
            try: c.break_link('ReloadSm.Result', 'ThSet%d.Weight' % i)
            except Exception as e: L.append(['break', i, str(e)[:60]])
            link('ThW.Result', 'ThSet%d.Weight' % i)
    if 'RlHSm' not in N:
        mk('AccumulateFloatLerp', 'RlHSm', bIntegrateDeltaTime='True')
        try: c.break_link('RlHC.Value', 'RlHInv.Value')
        except Exception as e: L.append(['break', 'RlHC', str(e)[:60]])
        link('RlHC.Value', 'RlHSm.TargetValue'); link('RlHSm.Result', 'RlHInv.Value')
    R['set_blend'] = bool(c.set_pin_default_value('RlHSm.Blend', '%.3f' % BLEND, True, False))
    R['links'] = L
    del N, g
    cr.recompile_vm(); R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
try: run()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_CR_RELOAD_FINGER_FIX', R.get('saved'), R.get('error', '')[-200:])
import gc; gc.collect()
