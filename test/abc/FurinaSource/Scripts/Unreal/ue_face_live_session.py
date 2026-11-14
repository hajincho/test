"""Isolated read-only render-session queue; never saves the project's map or assets."""
import unreal,os,json,runpy,time,traceback
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
REQ=os.path.join(ROOT,'Data','face_live_request.json')
OUT=os.path.join(ROOT,'Data','face_live_reply.json')
s={'last':None,'next':0,'deadline':time.monotonic()+3600}
def tick(dt):
    if time.monotonic()<s['next']:return
    s['next']=time.monotonic()+.2
    if time.monotonic()>s['deadline']:
        unreal.unregister_slate_post_tick_callback(s['h']);unreal.EditorPythonScripting.set_keep_python_script_alive(False);return
    try:
        if not os.path.isfile(REQ):return
        q=json.load(open(REQ,encoding='utf-8-sig'))
        if q['id']==s['last']:return
        s['last']=q['id']
        if q.get('stop'):
            unreal.unregister_slate_post_tick_callback(s['h']);unreal.EditorPythonScripting.set_keep_python_script_alive(False);return
        path=os.path.abspath(os.path.join(ROOT,q['script']))
        assert os.path.commonpath([ROOT,path])==ROOT
        runpy.run_path(path,run_name='__main__')
        reply={'id':q['id'],'ok':True}
    except Exception:reply={'id':s['last'],'error':traceback.format_exc()}
    with open(OUT,'w',encoding='utf-8') as f:json.dump(reply,f)
s['h']=unreal.register_slate_post_tick_callback(tick)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
