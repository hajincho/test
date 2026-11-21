"""Lyra 에디터(`py <파일> <뼈이름:부모이름> ...`): CR_FurinaSecondary 리그 계층에 스켈레톤 뼈(Imported)를 추가한다 (예: Thumb3_R:Thumb2_R Thumb3_L:Thumb2_L).
 CR 이 스켈레톤 뼈를 이름으로 매핑하므로 추가 후 해당 뼈를 SetRotation 등으로 제어할 수 있다.  -> Data/lyra_cr_add_bone.json"""
import unreal, json, sys, traceback
ARGS = [a for a in sys.argv[1:] if not a.endswith('.py')]
R = {'args': ARGS, 'log': []}
try:
    cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary')
    h = cr.hierarchy if hasattr(cr, 'hierarchy') else cr.get_hierarchy()
    hc = cr.get_hierarchy_controller() if hasattr(cr, 'get_hierarchy_controller') else h.get_controller()
    keys = {str(k.name): k for k in h.get_all_keys()}
    for a in ARGS:
        nm, par = a.split(':')
        if nm in keys: R['log'].append([nm, 'exists']); continue
        assert par in keys, 'parent missing ' + par
        pk = keys[par]
        try: key = hc.add_bone(nm, pk, unreal.Transform(), False, unreal.RigBoneType.IMPORTED, True)
        except Exception as e:
            R['log'].append([nm, 'add_bone err ' + str(e)[:150]]); key = None
        R['log'].append([nm, 'added' if key is not None and str(getattr(key, 'name', '')) == nm else str(key)])
    cr.recompile_vm()
    h2 = cr.hierarchy if hasattr(cr, 'hierarchy') else cr.get_hierarchy()
    R['now_has'] = [str(k.name) for k in h2.get_all_keys() if 'Thumb3' in str(k.name)]
    R['saved'] = bool(unreal.EditorAssetLibrary.save_loaded_asset(cr, False))
except Exception: R['error'] = traceback.format_exc()[-900:]
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_add_bone.json', 'w', encoding='utf-8'), indent=1, default=str); print('LYRA_CR_ADD_BONE', R.get('saved'), R.get('error', ''))
