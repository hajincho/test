import unreal,os,json,traceback
D=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','Data'))
R={}
def prop(o,n):
    try:
        v=o.get_editor_property(n)
        return v.export_text() if hasattr(v,'export_text') else str(v)
    except Exception as e:return str(e)
try:
    sk=unreal.load_asset('/Game/Furina/SK_Furina')
    R['mesh']={n:prop(sk,n) for n in ('nanite_settings','morph_targets','post_process_anim_blueprint','lod_info')}
    R['mesh_morphs']=[str(n) for n in sk.get_all_morph_target_names()]
    R['morph_api']=[n for n in dir(unreal.SkeletalMeshEditorSubsystem) if any(k in n.lower() for k in ('morph','lod','vertex'))]
    R['component_api']=[n for n in dir(unreal.SkeletalMeshComponent) if any(k in n.lower() for k in ('morph','curve','skin','vertex','nanite'))]
    sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib=unreal.SubobjectDataBlueprintFunctionLibrary
    bp=unreal.load_asset('/Game/3DPlatformerGameBundle/Demo/ThirdPersonAssets/Blueprints/ThirdPersonCharacter_BP')
    R['components']=[]
    for handle in sub.k2_gather_subobject_data_for_blueprint(bp):
        data=lib.get_data(handle);obj=lib.get_object(data)
        if isinstance(obj,unreal.SkeletalMeshComponent):
            R['components'].append({'name':str(lib.get_variable_name(data)),'path':obj.get_path_name(),'properties':{n:prop(obj,n) for n in ('disable_morph_target','morph_target_curves','allow_anim_curve_evaluation','force_disable_nanite','leader_pose_component','anim_class','post_process_anim_instance')}})
    mat=unreal.load_asset('/Game/Furina/Materials/M_Furina_Opaque')
    R['material']={n:prop(mat,n) for n in ('used_with_morph_targets','automatically_set_usage_in_editor','used_with_skeletal_mesh')}
except Exception:R['error']=traceback.format_exc()
with open(os.path.join(D,'walk_blink_diagnosis.json'),'w',encoding='utf-8') as f:json.dump(R,f,indent=1,ensure_ascii=False,default=str)
