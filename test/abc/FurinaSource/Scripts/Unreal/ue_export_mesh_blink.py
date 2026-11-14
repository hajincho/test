import unreal,os,json,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
try:
    if '-nullrhi' in unreal.SystemLibrary.get_command_line().lower():
        raise RuntimeError('FBX skeletal mesh export requires a renderer; run this inspection in the isolated render session.')
    sk=unreal.load_asset('/Game/Furina/SK_Furina')
    task=unreal.AssetExportTask()
    task.object=sk;task.filename=os.path.join(D,'Furina_blink_native_export.fbx')
    task.automated=True;task.prompt=False;task.replace_identical=True
    task.exporter=unreal.SkeletalMeshExporterFBX()
    opt=unreal.FbxExportOption()
    try:opt.set_editor_property('export_morph_targets',True)
    except Exception:pass
    task.options=opt
    R['ok']=unreal.Exporter.run_asset_export_task(task)
    R['errors']=list(task.errors)
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'native_blink_export.json'),'w',encoding='utf-8') as f:json.dump(R,f)
