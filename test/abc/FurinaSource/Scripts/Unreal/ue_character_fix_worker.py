"""Private commandlet worker; accepts local scripts only inside this project."""
import json, os, time, traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
REQUEST = os.path.join(ROOT, 'Data', 'character_fix_request.json')
REPLY = os.path.join(ROOT, 'Data', 'character_fix_reply.json')
last = None
deadline = time.time() + 3600
while time.time() < deadline:
    try:
        if not os.path.isfile(REQUEST):
            time.sleep(.2)
            continue
        with open(REQUEST,encoding='utf-8-sig') as f: request = json.load(f)
        if request.get('id') == last:
            time.sleep(.2)
            continue
        last = request['id']
        if request.get('stop'): break
        path = os.path.abspath(os.path.join(ROOT, request['script']))
        if os.path.commonpath([path,ROOT]) != ROOT: raise ValueError('Script outside FurinaSource')
        namespace = {'__file__':path, '__name__':'__main__'}
        with open(path,encoding='utf-8-sig') as f: code = f.read()
        exec(compile(code,path,'exec'),namespace)
        reply = {'id':last,'ok':True}
    except Exception:
        reply = {'id':last,'ok':False,'error':traceback.format_exc()}
    # Windows readers can briefly hold the previous reply open. Publish atomically
    # and retry sharing violations instead of losing the in-memory editor session.
    reply_tmp=REPLY+'.tmp'
    with open(reply_tmp,'w',encoding='utf-8') as f: json.dump(reply,f)
    for attempt in range(30):
        try:
            os.replace(reply_tmp,REPLY)
            break
        except OSError:
            time.sleep(.1)
