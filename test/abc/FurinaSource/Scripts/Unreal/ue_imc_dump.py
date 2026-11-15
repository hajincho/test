"""Editor: lists the key mappings of IMC_FurinaStance (action, key) -> Data/imc_dump.json"""
import unreal, json, traceback
def main():
    imc = unreal.load_asset('/Game/Furina/Input/IMC_FurinaStance'); R = {'props': [p for p in dir(imc) if 'mapping' in p.lower()]}
    out = []
    for name in ('mappings', 'default_key_mappings'):
        try:
            v = imc.get_editor_property(name)
            if hasattr(v, 'get_editor_property'): v = v.get_editor_property('mappings')
            for m in v: out.append([name, str(m.get_editor_property('action').get_name()), str(m.get_editor_property('key').get_editor_property('key_name'))])
        except Exception as e: out.append([name, 'ERR', str(e)[:100]])
    R['mappings'] = out
    json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\imc_dump.json', 'w'), indent=1); print('IMC', out)
try: main()
except Exception: json.dump({'error': traceback.format_exc()}, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\imc_dump.json', 'w'))
