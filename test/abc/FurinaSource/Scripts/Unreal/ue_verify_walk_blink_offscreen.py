"""Fresh-load verification without depending on the user's foreground window."""
import unreal,os,time,runpy,json
HERE=os.path.dirname(__file__)
D=os.path.abspath(os.path.join(HERE,'..','..','Data'))
report=os.path.join(D,'walk_blink_runtime_validation.json')
# -unattended disables background throttling in UEditorEngine, without changing
# any user preference or editor config.
state={'started':time.time()}
def finish_check(dt):
    ready=os.path.isfile(report) and os.path.getmtime(report)>state['started']
    if not ready and time.time()-state['started']<90:return
    unreal.unregister_slate_post_tick_callback(state['h'])
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
runpy.run_path(os.path.join(HERE,'ue_verify_walk_blink_runtime.py'),run_name='__main__')
state['h']=unreal.register_slate_post_tick_callback(finish_check)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
