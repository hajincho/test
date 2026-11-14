import os,runpy
HERE=os.path.dirname(__file__)
runpy.run_path(os.path.join(HERE,'ue_probe_walk_blink.py'),run_name='__main__')
runpy.run_path(os.path.join(HERE,'ue_apply_walk_loop.py'),run_name='__main__')
