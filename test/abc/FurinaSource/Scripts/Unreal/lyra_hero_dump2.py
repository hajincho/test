"""LYRA 에디터(헤드리스): 어빌리티 세트 항목, 액션 세트 액션의 실제 내용 덤프 -> Data/lyra_hero_dump2.json"""
import unreal, json, sys, traceback
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_hero_dump2.json'
R = {}
def s(v, n=700):
    t = str(v)
    return t if len(t) <= n else t[:n] + '...'
def ge(o, name):
    try: return o.get_editor_property(name)
    except Exception as e: return 'ERR ' + s(e, 80)
def struct_list(lst): return [s(x) for x in lst]
try:
    a = unreal.load_asset('/ShooterCore/Game/AbilitySet_ShooterHero'); row = {}
    for pn in ('granted_gameplay_abilities', 'granted_gameplay_effects'):
        v = ge(a, pn); row[pn] = struct_list(v) if hasattr(v, '__iter__') and not isinstance(v, str) else s(v)
    R['AbilitySet_ShooterHero'] = row
    def acts(path):
        o = unreal.load_asset(path); out = []
        for x in ge(o, 'actions'):
            d = {'cls': x.get_class().get_name()}
            for pn in ('component_list', 'layout', 'widgets', 'input_configs', 'input_mappings', 'abilities_list', 'ability_list', 'granted_abilities'):
                v = ge(x, pn)
                if isinstance(v, str) and v.startswith('ERR'): continue
                d[pn] = struct_list(v) if hasattr(v, '__iter__') and not isinstance(v, str) else s(v)
            out.append(d)
        return out
    for p in ('LAS_ShooterGame_StandardComponents', 'LAS_ShooterGame_SharedInput', 'LAS_ShooterGame_StandardHUD'): R[p] = acts('/ShooterCore/Experiences/' + p)
    R['EAS_BasicShooterAcolades'] = acts('/ShooterCore/Accolades/EAS_BasicShooterAcolades')
    exp = unreal.load_asset('/Game/System/Experiences/B_Furina_Experience'); cdo = unreal.get_default_object(exp.generated_class()); out = []
    for x in ge(cdo, 'actions'):
        d = {'cls': x.get_class().get_name()}
        for pn in ('component_list', 'layout', 'widgets', 'input_configs', 'input_mappings', 'abilities_list'):
            v = ge(x, pn)
            if isinstance(v, str) and v.startswith('ERR'): continue
            d[pn] = struct_list(v) if hasattr(v, '__iter__') and not isinstance(v, str) else s(v)
        out.append(d)
    R['B_Furina_Experience_actions'] = out
    # 영웅 BP 부모 클래스와 그래프 이름
    bp = unreal.load_asset('/ShooterCore/Game/B_Hero_ShooterMannequin')
    R['B_Hero_parent'] = s(unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp))
    R['B_Hero_graphs'] = [str(g) for g in unreal.BlueprintEditorLibrary.list_graph_names(bp)]
    # 에셋 레지스트리로 무기 관련 에셋 규모
    ar = unreal.AssetRegistryHelpers.get_asset_registry(); wp = {}
    for root in ('/Game/Weapons', '/ShooterCore/Weapons', '/ShooterCore/Weapon', '/ShooterCore/Item', '/ShooterCore/Items', '/Game/Items', '/Game/Inventory'):
        try: wp[root] = len(ar.get_assets_by_path(root, recursive=True))
        except Exception as e: wp[root] = 'ERR'
    R['weapon_asset_counts'] = wp
    R['weapon_like_in_shootercore'] = sorted({str(x.package_name) for x in ar.get_assets_by_path('/ShooterCore', recursive=True) if any(k in str(x.package_name).lower() for k in ('weapon', 'quickbar', 'inventory', 'ammo', 'reticle', 'equipment', 'melee', 'grenade', 'pistol', 'rifle', 'shotgun', 'aimassist'))})[:150]
    R['weapon_like_in_game'] = sorted({str(x.package_name) for x in ar.get_assets_by_path('/Game', recursive=True) if any(k in str(x.package_name).lower() for k in ('quickbar', 'inventory', 'ammo', 'reticle', 'equipment', 'weaponspawn', 'aimassist'))})[:100]
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_HERO_DUMP2', R.get('error', 'ok')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
