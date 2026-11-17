"""Lyra 에디터: CR_FurinaSecondary 계층의 뼈 이름(상체/팔 쪽) 확인 -> Data/lyra_cr_bones.json"""
import unreal, json
OUT = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_cr_bones.json'
cr = unreal.load_asset('/Game/Furina/CR_FurinaSecondary'); h = cr.get_hierarchy()
names = [str(k.name) for k in h.get_all_keys(True) if k.type == unreal.RigElementType.BONE]
R = {'n': len(names), 'upper': [n for n in names if any(x in n.lower() for x in ('spine', 'chest', 'neck', 'head', 'hips', 'shoulder', 'clav', 'arm', 'wrist'))][:60]}
json.dump(R, open(OUT, 'w'), indent=1); print('LYRA_CR_BONES', R['n'])
