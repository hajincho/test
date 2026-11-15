"""Writes Data/api_dir.json: public attributes of unreal.<Class> for each class name in argv."""
import unreal, sys, json
R = {cn: [a for a in dir(getattr(unreal, cn)) if not a.startswith('_')] if hasattr(unreal, cn) else None for cn in sys.argv[1:]}
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\api_dir.json', 'w'), indent=1); print('API_DIR', list(R))
