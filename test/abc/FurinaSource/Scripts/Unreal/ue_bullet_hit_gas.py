"""BP_FurinaBullet: Lyra 호환 히트판정(GAS). PIE stopped.
 - 변수 FurinaDamage(float, 기본 0.0 = 피해량), FurinaDamageEffect(GameplayEffect 클래스, 기본 Lyra의 /Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller).
 - 도탄이 아닌 일반 적중 경로(FRC_Branch.else -> Mark 사이)에 노드 FHG_* 삽입:
   Other의 AbilitySystemComponent(GetAbilitySystemComponent) 가 유효하고 GE 클래스가 유효하면
   ASC.MakeEffectContext -> EffectContextAddHitResult(Hit) -> ASC.MakeOutgoingSpec(GE, 1, Context)
   -> AssignTagSetByCallerMagnitude(SetByCaller.Damage, FurinaDamage) -> ASC.ApplyGameplayEffectSpecToSelf  (Lyra LyraHealthComponent.DamageSelfDestruct 와 같은 패턴)
 -> Data/bullet_hit_gas.json"""
import unreal, json, traceback
D = r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data'
R = {'log': []}
def main():
    bp = unreal.load_asset('/Game/Furina/FP/BP_FurinaBullet')
    ed = unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, 'EventGraph')
    nodes = {n.get_name(): n for n in ed.list_all_nodes()}
    BEL = unreal.BlueprintEditorLibrary
    have = [str(n) for n in BEL.list_member_variable_names(bp)]
    if 'FurinaDamage' not in have:
        for tname in ('float', 'double', 'real'):
            try:
                ed.add_member_variable('FurinaDamage', BEL.get_basic_type_by_name(tname), '0.0'); R['log'].append('FurinaDamage as ' + tname); break
            except Exception as e: R['log'].append('FurinaDamage ' + tname + ' failed ' + str(e)[:80])
        try: BEL.set_blueprint_variable_instance_editable(bp, 'FurinaDamage', True); BEL.set_blueprint_variable_expose_on_spawn(bp, 'FurinaDamage', True)
        except Exception as e: R['log'].append('damage flags ' + str(e)[:80])
    if 'FurinaDamageEffect' not in have:
        try:
            ct = BEL.get_class_reference_type(unreal.GameplayEffect.static_class())
            ed.add_member_variable('FurinaDamageEffect', ct, '/Game/GameplayEffects/Damage/GE_Damage_Basic_SetByCaller.GE_Damage_Basic_SetByCaller_C'); R['log'].append('FurinaDamageEffect created')
            try: BEL.set_blueprint_variable_instance_editable(bp, 'FurinaDamageEffect', True)
            except Exception as e: R['log'].append('effect flag ' + str(e)[:80])
        except Exception as e: R['log'].append('FurinaDamageEffect failed ' + traceback.format_exc()[-300:])
    R['vars'] = [str(n) for n in BEL.list_member_variable_names(bp)]
    def link(a, b): assert a.is_valid() and b.is_valid(), (a, b); b.break_pin_links(); assert unreal.BlueprintGraphPinLibrary.try_create_connection(a, b), 'link'
    def mk(name, *paths):
        if name in nodes: return nodes[name]
        last = None
        for p in paths:
            try:
                n = ed.add_call_function_node(p)
                if n: n.rename(name); nodes[name] = n; R['log'].append(name + ' <- ' + p); return n
            except Exception as e: last = e
        raise RuntimeError('no node for ' + name + ' ' + str(paths) + ' ' + str(last))
    G = '/Script/GameplayAbilities.'; K = '/Script/Engine.KismetSystemLibrary:'; ML = '/Script/Engine.KismetMathLibrary:'
    hit = nodes['K2Node_FPB_Hit']; br_else = nodes['FRC_Branch']; mark = nodes['K2Node_FPB_Mark']
    if True:
        asc = mk('FHG_ASC', G + 'AbilitySystemBlueprintLibrary:GetAbilitySystemComponent')
        link(hit.find_output_pin('Other'), asc.find_input_pin('Actor'))
        v1 = mk('FHG_IsValidAsc', K + 'IsValid'); link(asc.find_result_pin(), v1.find_input_pin('Object'))
        ge = nodes.get('FHG_GetEffect')
        if ge is None: ge = ed.add_get_member_variable_node('FurinaDamageEffect'); ge.rename('FHG_GetEffect'); nodes['FHG_GetEffect'] = ge
        v2 = mk('FHG_IsValidClass', K + 'IsValidClass'); link(ge.find_output_pin('FurinaDamageEffect'), v2.find_input_pin('Class'))
        an = mk('FHG_And', ML + 'BooleanAND'); link(v1.find_result_pin(), an.find_input_pin('A')); link(v2.find_result_pin(), an.find_input_pin('B'))
        br = nodes.get('FHG_Branch')
        if br is None: br = ed.add_branch_node(); br.rename('FHG_Branch'); nodes['FHG_Branch'] = br
        link(an.find_result_pin(), br.find_input_pin('Condition'))
        ctx = mk('FHG_MakeCtx', G + 'AbilitySystemComponent:MakeEffectContext'); link(asc.find_result_pin(), ctx.find_self_pin() if hasattr(ctx, 'find_self_pin') else ctx.find_input_pin('self'))
        addhit = mk('FHG_AddHit', G + 'AbilitySystemBlueprintLibrary:EffectContextAddHitResult')
        link(hit.find_output_pin('Hit'), addhit.find_input_pin('HitResult'))
        spec = mk('FHG_MakeSpec', G + 'AbilitySystemComponent:MakeOutgoingSpec')
        link(asc.find_result_pin(), spec.find_self_pin() if hasattr(spec, 'find_self_pin') else spec.find_input_pin('self'))
        link(ge.find_output_pin('FurinaDamageEffect'), spec.find_input_pin('GameplayEffectClass')); spec.find_input_pin('Level').set_pin_value('1.0')
        link(ctx.find_result_pin(), spec.find_input_pin('Context'))
        setc = mk('FHG_SetByCaller', G + 'AbilitySystemBlueprintLibrary:AssignTagSetByCallerMagnitude')
        link(spec.find_result_pin(), setc.find_input_pin('SpecHandle')); setc.find_input_pin('DataTag').set_pin_value('(TagName="SetByCaller.Damage")')
        dm = nodes.get('FHG_GetDamage')
        if dm is None: dm = ed.add_get_member_variable_node('FurinaDamage'); dm.rename('FHG_GetDamage'); nodes['FHG_GetDamage'] = dm
        link(dm.find_output_pin('FurinaDamage'), setc.find_input_pin('Magnitude'))
        getctx = mk('FHG_GetCtx', G + 'AbilitySystemBlueprintLibrary:GetEffectContext')
        link(setc.find_result_pin(), getctx.find_input_pin('SpecHandle')); link(getctx.find_result_pin(), addhit.find_input_pin('EffectContext'))
        app = mk('FHG_Apply', G + 'AbilitySystemComponent:BP_ApplyGameplayEffectSpecToSelf', G + 'AbilitySystemComponent:ApplyGameplayEffectSpecToSelf')
        link(asc.find_result_pin(), app.find_self_pin() if hasattr(app, 'find_self_pin') else app.find_input_pin('self'))
        link(setc.find_result_pin(), app.find_input_pin('SpecHandle'))
        # exec: Branch.else -> FHG_Branch ; true: ctx -> addhit -> spec -> setc -> app -> mark ; false -> mark
        def ep(n): return n.find_input_pin('execute')
        def tp(n): return n.find_output_pin('then')
        for n in (ctx, addhit, spec, setc, app, br, getctx): R.setdefault('pins_pre', {})[n.get_name()] = [str(p.get_pin_name()) for p in n.list_all_pins()]
        link(br_else.find_output_pin('else'), ep(br))
        chain = [n for n in (setc, addhit, app) if n.find_input_pin('execute').is_valid()]
        R['exec_chain'] = [n.get_name() for n in chain]
        prev = br.find_output_pin('then')
        for n in chain: link(prev, ep(n)); prev = tp(n)
        link(prev, ep(mark))
        link(br.find_output_pin('else'), ep(mark))
    for n in nodes.values():
        if n.get_name().startswith('FHG_'):
            R.setdefault('pins', {})[n.get_name()] = [str(p.get_pin_name()) for p in n.list_all_pins()]
    BEL.compile_blueprint(bp)
    R['status'] = str(bp.get_editor_property('status')) if hasattr(bp, 'get_editor_property') else ''
    R['saved'] = unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
try: main()
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(D + r'\bullet_hit_gas.json', 'w'), indent=1, default=str); print('BULLET_HIT_GAS', R.get('saved'), R.get('error', '')[-300:])
