import runpy,os,json
HERE=os.path.dirname(__file__)
D=os.path.abspath(os.path.join(HERE,'..','..','Data'))
runpy.run_path(os.path.join(HERE,'ue_apply_walk_loop.py'),run_name='__main__')
runpy.run_path(os.path.join(HERE,'ue_apply_visible_blink.py'),run_name='__main__')
assert json.load(open(os.path.join(D,'visible_blink_applied.json')))['ok']
