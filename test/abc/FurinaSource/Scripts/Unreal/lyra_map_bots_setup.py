"""Lyra 에디터(`py <파일> keep`, PIE 중지 상태):
 1) PIE 봇 수 0 오버라이드 해제 (Config/DefaultEditorPerProjectUserSettings.ini 와 실행 중 CDO 모두)
 2) L_FiringRange_WP 를 열어 월드 파티션 액터를 모두 로드한 뒤 Lyra 무기 스포너/인벤토리 패드 액터를 삭제하고 저장
 -> Data/lyra_map_bots_setup.json"""
import unreal, json, sys, traceback, re, collections
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_map_bots_setup.json'
INI = r'C:\Users\fromj\Downloads\test\test\abc\Config\DefaultEditorPerProjectUserSettings.ini'
R = {}
WEAPON_CLASSES = ('B_WeaponSpawner_C', 'B_GrantInventoryPad_WithMesh_C', 'B_GrantInventory_Pad_C', 'LyraWeaponSpawner')
try:
    s = open(INI, encoding='utf-8').read()
    s2 = re.sub(r'; Furina: 봇은 푸리나 폰으로[^\n]*\n', '', s); s2 = s2.replace('bOverrideBotCount=True\n', '').replace('OverrideNumPlayerBotsToSpawn=0\n', '')
    R['ini_changed'] = s2 != s
    open(INI, 'w', encoding='utf-8', newline='').write(s2)
    try:
        ds = unreal.get_default_object(unreal.LyraDeveloperSettings)
        R['bots_before'] = [ds.get_editor_property('override_bot_count'), ds.get_editor_property('override_num_player_bots_to_spawn')]
        ds.set_editor_property('override_bot_count', False)
        R['bots_after'] = ds.get_editor_property('override_bot_count')
    except Exception as e: R['bots_cdo_err'] = str(e)[:120]
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); R['loaded'] = les.load_level('/ShooterMaps/Maps/L_FiringRange_WP')
    lib = unreal.WorldPartitionBlueprintLibrary; descs = lib.get_actor_descs(); R['desc_count'] = len(descs) if descs else None
    if descs: lib.load_actors([d.guid for d in descs])
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); acts = eas.get_all_level_actors(); R['actors'] = len(acts)
    cnt = collections.Counter(a.get_class().get_name() for a in acts); R['weapon_related_classes'] = {k: v for k, v in cnt.items() if any(w in k for w in ('Weapon', 'Inventory', 'Grenade', 'Pickup', 'Spawner', 'Pad'))}
    removed = []
    for a in list(acts):
        if a.get_class().get_name() in WEAPON_CLASSES or 'WeaponSpawner' in a.get_class().get_name():
            removed.append(a.get_actor_label()); eas.destroy_actor(a)
    R['removed'] = removed
    R['saved'] = les.save_current_level()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(OUT, 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False); print('LYRA_MAP_BOTS', R.get('removed'), R.get('saved'), R.get('error', '')[-200:])
if 'keep' not in sys.argv: unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
