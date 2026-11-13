"""Short-lived local script queue for this editor verification session."""
import os, json, time, runpy, traceback, unreal
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
REQ=os.path.join(ROOT,'Data','hair_live_request.json')
OUT=os.path.join(ROOT,'Data','hair_live_reply.json')
session={'last':None,'deadline':time.monotonic()+1800,'next':0}
def poll(delta):
    if time.monotonic()<session['next']:return
    session['next']=time.monotonic()+.3
    if time.monotonic()>session['deadline']:
        unreal.unregister_slate_post_tick_callback(session['handle']);return
    if not os.path.isfile(REQ):return
    try:
        with open(REQ,encoding='utf-8-sig') as f:q=json.load(f)
        if q['id']==session['last']:return
        session['last']=q['id']
        if q.get('stop'):
            unreal.unregister_slate_post_tick_callback(session['handle']);return
        path=os.path.abspath(os.path.join(ROOT,q['script']))
        assert os.path.commonpath([path,ROOT])==ROOT
        runpy.run_path(path,run_name='__main__')
        result={'id':q['id'],'ok':True}
    except Exception:result={'id':session['last'],'ok':False,'error':traceback.format_exc()}
    with open(OUT,'w',encoding='utf-8') as f:json.dump(result,f)
session['handle']=unreal.register_slate_post_tick_callback(poll)
runpy.run_path(os.path.join(os.path.dirname(__file__),'ue_verify_soft_hair_runtime.py'),run_name='__main__')
