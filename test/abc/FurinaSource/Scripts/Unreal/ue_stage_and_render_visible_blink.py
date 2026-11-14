import os,runpy
HERE=os.path.dirname(__file__)
runpy.run_path(os.path.join(HERE,'ue_stage_visible_blink.py'),run_name='__main__')
runpy.run_path(os.path.join(HERE,'ue_diagnose_face_render.py'),run_name='__main__')
