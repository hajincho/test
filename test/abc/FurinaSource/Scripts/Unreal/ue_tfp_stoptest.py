import unreal,gc,types
for f in gc.get_objects():
 if isinstance(f,types.FunctionType) and f.__name__=='tick' and f.__code__.co_filename.endswith(('ue_tfp_ads_runtime.py','ue_tfp_runtime.py')):
  try:unreal.unregister_slate_post_tick_callback(f.__globals__['S']['h']);f.__globals__['S']['phase']='stopped'
  except Exception:pass
