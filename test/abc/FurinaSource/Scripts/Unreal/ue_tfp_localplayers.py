import unreal,json
R=[]
for x in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem):
 if not x.get_name().startswith('Default__'):
  lp=x.get_outer();R.append({'path':x.get_path_name(),'outer':lp.get_path_name(),'api':[n for n in dir(lp) if any(v in n for v in ('player_controller','game_instance','world'))]})
json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_localplayers.json','w'),indent=1)
