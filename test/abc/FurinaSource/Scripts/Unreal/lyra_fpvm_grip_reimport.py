"""검증 목록에 있는 1인칭 AnimSequence만 기존 에셋에 다시 가져온다."""

import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyra_fpvm_animation_import import import_clip


def main(manifest):
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'PIE를 종료한 뒤 에셋을 가져와야 합니다.'
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    source = root / 'FurinaSource' / 'FBX' / 'FPVM'
    content = root / 'Content' / 'Furina' / 'FPVM'
    checkpoint = manifest.parent / 'UnrealImport.json'
    backup = manifest.parent / 'BeforeApply'
    candidate = manifest.parent / 'FBX' / 'FPVM'
    rows = json.loads(manifest.read_text(encoding='utf-8'))
    result = {'clips': {}, 'done': False}
    if checkpoint.is_file():
        result = json.loads(checkpoint.read_text(encoding='utf-8'))
        result['done'] = False

    def save_checkpoint():
        temporary = checkpoint.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        temporary.replace(checkpoint)

    assets = unreal.EditorAssetLibrary
    world = editor.get_editor_world()
    cvar = 'Interchange.FeatureFlags.Import.FBX'
    use_interchange = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    unreal.SystemLibrary.execute_console_command(world, cvar + ' 0')
    save_checkpoint()
    try:
        for model, name in rows:
            assert model.isalnum() and name.startswith(f'AS_FPVM_{model}_') and name.replace('_', '').isalnum()
            folder = f'/Game/Furina/FPVM/{model}'
            path = f'{folder}/{name}'
            target_fbx = source / f'{name}.fbx'
            target_asset = content / model / f'{name}.uasset'
            file = candidate / f'{name}.fbx'
            previous = result['clips'].get(name, {})
            length = previous.get('previous_seconds')
            previous_fbx = None
            try:
                assert file.is_file() and target_fbx.is_file() and target_asset.is_file(), name
                candidate_bytes = file.read_bytes()
                digest = hashlib.sha256(candidate_bytes).hexdigest()
                if previous.get('saved') and candidate_bytes == target_fbx.read_bytes():
                    previous['fbx_sha256'] = digest
                    continue
                animation = unreal.load_asset(path)
                assert isinstance(animation, unreal.AnimSequence), path
                skeleton = animation.get_editor_property('skeleton')
                assert skeleton
                if length is None:
                    length = animation.get_play_length()
                backup.mkdir(exist_ok=True)
                for original in (target_fbx, target_asset):
                    original_backup = backup / original.name
                    if not original_backup.exists():
                        shutil.copy2(original, original_backup)
                result['clips'][name] = {'previous_seconds': length}
                save_checkpoint()
                previous_fbx = target_fbx.read_bytes()
                target_fbx.write_bytes(candidate_bytes)
                revised = import_clip(folder, skeleton, name)
                assert revised.get_path_name() == animation.get_path_name(), revised.get_path_name()
                assert abs(revised.get_play_length() - length) <= 0.034, name
                assert assets.save_loaded_asset(revised, False), path
                result['clips'][name]['saved'] = True
                result['clips'][name]['seconds'] = round(revised.get_play_length(), 4)
                result['clips'][name]['fbx_sha256'] = digest
            except Exception:
                if previous_fbx is not None:
                    target_fbx.write_bytes(previous_fbx)
                result['clips'][name] = {'previous_seconds': length,
                                         'saved': False, 'error': traceback.format_exc()[-1800:]}
            save_checkpoint()
    finally:
        unreal.SystemLibrary.execute_console_command(world, cvar + (' 1' if use_interchange else ' 0'))
    result['done'] = all(result['clips'].get(name, {}).get('saved') for _, name in rows)
    save_checkpoint()
    print('GRIP_IMPORT', sum(row.get('saved', False) for row in result['clips'].values()), len(rows))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
