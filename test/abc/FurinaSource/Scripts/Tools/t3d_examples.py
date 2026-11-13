import re, sys
src = open(sys.argv[1], encoding='utf-8-sig').read()
lines = src.splitlines()
objs, cur, depth = [], [], 0
for l in lines:
    if l.startswith('Begin Object'):
        cur = [l]; depth = 1; continue
    if cur:
        cur.append(l)
        if l.startswith('End Object'): objs.append('\n'.join(cur)); cur = []
def short(t):
    t = re.sub(r'PinToolTip="(?:[^"\\]|\\.)*",', '', t)
    t = re.sub(r'PinFriendlyName=[^,]*\),', '', t)
    t = t.replace('PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,', '~')
    t = t.replace('PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,', '')
    return '\n'.join(x[:400] for x in t.splitlines() if 'ExportPath' not in x)
def first(pred, title):
    for o in objs:
        if pred(o): print('=====', title); print(short(o)); return
    print('===== (none)', title)
first(lambda o: 'K2Node_EnhancedInputAction' in o.splitlines()[0], 'EnhancedInputAction')
first(lambda o: 'K2Node_VariableGet' in o.splitlines()[0] and 'bSelfContext=True' in o and 'object' in o, 'VarGet self object')
first(lambda o: 'K2Node_VariableGet' in o.splitlines()[0] and 'MemberParent' in o, 'VarGet member of other class')
first(lambda o: 'K2Node_VariableSet' in o.splitlines()[0] and 'MemberParent' in o, 'VarSet member of other class')
first(lambda o: 'K2Node_CallFunction' in o.splitlines()[0] and 'KismetMathLibrary' in o, 'Math call')
