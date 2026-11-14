import sys
src = open(r'Scripts\Tools\gen_fp_view_t3d.py', encoding='utf-8').read()
sys.argv = ['x', 'unused']
ns = {}; exec(src.split('G = Graph()')[0], ns)
Graph, CLS, STR, E = ns['Graph'], ns['CLS'], ns['STR'], ns['E']
G = Graph()
def call(key, owner, func, x, y, self_cls=None, self_link=None):
    G.node(key, '/Script/BlueprintGraph.K2Node_CallFunction', ['bIsPureFunc=True', 'FunctionReference=(MemberParent="%s",MemberName="%s")' % (CLS(owner), func)], x, y)
    if self_cls:
        G.pin(key, 'self', 'object', obj=CLS(self_cls))
        if self_link: G.link(self_link, (key, 'self'))
# air hold: speed + 10000 while not in first person -> an airborne forced-third-person state lasts until landing
G.node('HGetCam', '/Script/BlueprintGraph.K2Node_VariableGet', ['VariableReference=(MemberName="FPCamera",bSelfContext=True)'], 0, 0)
cam = G.pin('HGetCam', 'FPCamera', 'object', obj=CLS(E + 'CameraComponent'), out=True)
call('HIsFP', E + 'ActorComponent', 'IsActive', 250, 0, self_cls=E + 'ActorComponent', self_link=cam); G.pin('HIsFP', 'ReturnValue', 'bool', out=True)
call('HNotFP', E + 'KismetMathLibrary', 'Not_PreBool', 500, 0); G.pin('HNotFP', 'A', 'bool', default='false'); G.link(('HIsFP', 'ReturnValue'), ('HNotFP', 'A')); G.pin('HNotFP', 'ReturnValue', 'bool', out=True)
call('HBias01', E + 'KismetMathLibrary', 'Conv_BoolToDouble', 750, 0); G.pin('HBias01', 'InBool', 'bool', default='false'); G.link(('HNotFP', 'ReturnValue'), ('HBias01', 'InBool')); G.pin('HBias01', 'ReturnValue', 'real', 'double', out=True)
call('HBias', E + 'KismetMathLibrary', 'Multiply_DoubleDouble', 1000, 0); G.pin('HBias', 'A', 'real', 'double', default='0.0'); G.link(('HBias01', 'ReturnValue'), ('HBias', 'A'))
G.pin('HBias', 'B', 'real', 'double', default='10000.0'); G.pin('HBias', 'ReturnValue', 'real', 'double', out=True)
call('HVel', E + 'Actor', 'GetVelocity', 500, 150); G.pin('HVel', 'ReturnValue', 'struct', obj=STR('/Script/CoreUObject.Vector'), out=True)
call('HSpeed', E + 'KismetMathLibrary', 'VSize', 750, 150); G.pin('HSpeed', 'A', 'struct', obj=STR('/Script/CoreUObject.Vector')); G.link(('HVel', 'ReturnValue'), ('HSpeed', 'A')); G.pin('HSpeed', 'ReturnValue', 'real', 'double', out=True)
call('HSum', E + 'KismetMathLibrary', 'Add_DoubleDouble', 1250, 75); G.pin('HSum', 'A', 'real', 'double', default='0.0'); G.link(('HSpeed', 'ReturnValue'), ('HSum', 'A'))
G.pin('HSum', 'B', 'real', 'double', default='0.0'); G.link(('HBias', 'ReturnValue'), ('HSum', 'B')); G.pin('HSum', 'ReturnValue', 'real', 'double', out=True)
open(r'Data\fp_view_hold_nodes.t3d', 'w', encoding='utf-8', newline='\r\n').write(G.text().replace('K2Node_FPV_', 'K2Node_FPVH_'))
print('ok', len(G.order))
