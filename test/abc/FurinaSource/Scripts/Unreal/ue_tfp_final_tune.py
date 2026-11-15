import runpy,os,unreal
D=r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource'
for script in ['ue_build_cr.py','ue_tfp_zero.py','ue_tfp_save.py']:runpy.run_path(os.path.join(D,'Scripts','Unreal',script),run_name='__main__')
