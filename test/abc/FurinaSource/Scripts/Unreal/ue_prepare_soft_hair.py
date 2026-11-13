"""Compile and verify the complete hair change before saving any locked packages."""
import os, runpy, json
HERE=os.path.dirname(__file__)
D=os.path.abspath(os.path.join(HERE,'..','..','Data'))
runpy.run_path(os.path.join(HERE,'ue_build_cr.py'),run_name='__main__')
report=json.load(open(os.path.join(D,'ue_build_cr.json'),encoding='utf-8'))
assert not report.get('error') and not report.get('fail'),report
runpy.run_path(os.path.join(HERE,'ue_apply_soft_hair.py'),run_name='__main__')
assert json.load(open(os.path.join(D,'soft_hair_applied.json')))['ok']
runpy.run_path(os.path.join(HERE,'ue_validate_soft_hair.py'),run_name='__main__')
