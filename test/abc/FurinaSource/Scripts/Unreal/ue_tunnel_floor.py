"""Editor (level open): vertical line traces on a grid to find the walkable floor of the underground tunnel: for each (x, y) trace down from z0 to z0-700 and up from z0 to z0+700 (Visibility channel, complex)
-> Data/tunnel_floor.json   usage: py ue_tunnel_floor.py [z0] [x_from x_to x_step] [y_from y_to y_step]"""
import unreal, json, sys, traceback
a = sys.argv[1:]
Z0 = float(a[0]) if len(a) > 0 else 0.0
XF, XT, XS = (float(a[1]), float(a[2]), float(a[3])) if len(a) > 3 else (-7000.0, 2000.0, 500.0)
YF, YT, YS = (float(a[4]), float(a[5]), float(a[6])) if len(a) > 6 else (-600.0, 600.0, 200.0)
R = {'z0': Z0, 'hits': []}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    x = XF
    while x <= XT:
        y = YF
        while y <= YT:
            row = [x, y]
            for end in (Z0 - 700.0, Z0 + 700.0):
                r = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, Z0), unreal.Vector(x, y, end), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                hit = r[1] if isinstance(r, tuple) else None; ok = r[0] if isinstance(r, tuple) else r
                if ok and hit is not None:
                    try: row.append(round(hit.to_tuple()[4][2]) if False else round(hit.impact_point.z))
                    except Exception: row.append(round(hit.get_editor_property('impact_point').z))
                else: row.append(None)
            R['hits'].append(row); y += YS
        x += XS
except Exception: R['error'] = traceback.format_exc()
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\tunnel_floor.json', 'w'), indent=0); print('TUNNEL_FLOOR', len(R['hits']), R.get('error', '')[-300:])
