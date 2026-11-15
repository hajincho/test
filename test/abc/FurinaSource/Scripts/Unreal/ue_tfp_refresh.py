import unreal,gc,types,json
for f in gc.get_objects():
 if isinstance(f,types.FunctionType) and f.__name__=='tick' and f.__code__.co_filename.endswith('ue_tfp_runtime.py'):
  try:unreal.unregister_slate_post_tick_callback(f.__globals__['S']['h'])
  except Exception:pass
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
R={'lib':[n for n in dir(unreal.BlueprintEditorLibrary) if 'refresh' in n or 'reconstruct' in n],'node':[n for n in dir(unreal.K2Node_VariableGet) if 'reconstruct' in n or 'refresh' in n]};json.dump(R,open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tfp_refresh.json','w'))
