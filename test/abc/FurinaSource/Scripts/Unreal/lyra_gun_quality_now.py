"""Lyra 에디터: 소총 선명도 관련 콘솔 변수를 지금 실행 중인 에디터에도 즉시 적용(ini 는 재시작 때 적용). -> Data/lyra_gun_quality_now.json"""
import unreal, json
R = {}
for c in ('r.MaxAnisotropy 16', 'r.Streaming.PoolSize 2500'): unreal.SystemLibrary.execute_console_command(None, c)
for c in ('r.MaxAnisotropy', 'r.Streaming.PoolSize'): R[c] = unreal.SystemLibrary.get_console_variable_float_value(c)
json.dump(R, open(r'C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\lyra_gun_quality_now.json', 'w')); print('LYRA_GUN_QUALITY', R)
