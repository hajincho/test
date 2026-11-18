import unreal, json
OUT=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\furina_imc_keys.json'
R={}
for p in ('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Input/Default_IMC','/Game/Furina/Input/IMC_FurinaStance'):
    imc=unreal.load_asset(p); rows=[]
    for m in imc.get_editor_property('default_key_mappings').get_editor_property('mappings'):
        ia=m.get_editor_property('action'); rows.append([str(m.get_editor_property('key').get_editor_property('key_name')), ia.get_name() if ia else None, bool(ia.get_editor_property('consume_input')) if ia else None])
    R[p]=rows
json.dump(R,open(OUT,'w',encoding='utf-8'),indent=1)
