"""열려 있는 언리얼 에디터(프로젝트 설정 bRemoteExecution=True)에 파이썬 파일을 보내 실행한다. 에디터를 끄지 않음.
usage: python ue_remote_run.py <script.py> [args...]   (args 는 sys.argv 로 전달)  /  python ue_remote_run.py -c "<code>"
출력(print)과 결과를 그대로 보여 준다."""
import sys, time, json
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
sys.path.insert(0, r'C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python')
import remote_execution as rx

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return 2
    if a[0] == '-c': code = a[1]
    else:
        import os; path = os.path.abspath(a[0]).replace('\\', '/'); args = [path] + a[1:]   # 에디터의 작업 폴더는 엔진 Binaries
        code = ("import sys, runpy\nsys.argv = %r\nrunpy.run_path(%r, run_name='__main__')" % (args, path))
    cfg = rx.RemoteExecutionConfig(); cfg.multicast_bind_address = '127.0.0.1'
    r = rx.RemoteExecution(cfg); r.start()
    try:
        t0 = time.time()
        while not r.remote_nodes and time.time() - t0 < 8: time.sleep(0.2)
        if not r.remote_nodes: print('NO_EDITOR_FOUND'); return 3
        node = r.remote_nodes[0]['node_id']; r.open_command_connection(node)
        res = r.run_command(code, unattended=True, exec_mode=rx.MODE_EXEC_FILE)
        for o in res.get('output', []): print(o.get('output', '').rstrip())
        print('REMOTE_OK' if res.get('success') else 'REMOTE_FAIL', str(res.get('result', ''))[:2000])
        return 0 if res.get('success') else 1
    finally:
        r.stop()

if __name__ == '__main__':
    sys.exit(main())
