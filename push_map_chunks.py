"""Pushes the Underground Tunnel map content (5.3 GB, untracked in the working tree) to origin/main in chunks <= ~1.2 GB (one push of that size is rejected by GitHub). Waits until push_in_chunks.py has
finished (log line ALL PUSHED / GIVING UP / ERROR) so that two pushes never run at the same time. Each chunk = one commit = one push (schannel, certificate verification stays ON, HTTP/1.1, big post buffer, 5 retries).
log: push_map_chunks.log"""
import subprocess, os, sys, time
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
REPO = os.path.dirname(os.path.abspath(__file__)); LOG = open(os.path.join(REPO, 'push_map_chunks.log'), 'a', encoding='utf-8', buffering=1)
def log(*a): s = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a); print(s, flush=True); LOG.write(s + '\n')
def git(*args, check=True, cfg=False):
    pre = ['-c', 'http.sslBackend=schannel', '-c', 'http.version=HTTP/1.1', '-c', 'http.postBuffer=1073741824', '-c', 'core.safecrlf=false'] if cfg else ['-c', 'core.safecrlf=false']
    r = subprocess.run(['git'] + pre + list(args), cwd=REPO, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode != 0: raise RuntimeError('git %s failed: %s' % (' '.join(args[:3]), (r.stderr or r.stdout)[-600:]))
    return r
TRAILER = '\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>'
BIG = 'test/abc/Content/UndergroundTunnel/'; TEX = BIG + 'Textures/'; LIMIT = 1.2 * 1024 ** 3
def first_done():
    p = os.path.join(REPO, 'push_in_chunks.log')
    t = open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else ''
    return any(k in t for k in ('ALL PUSHED', 'GIVING UP', 'ERROR'))
def main():
    log('waiting for push_in_chunks.py to finish')
    while not first_done(): time.sleep(15)
    log('first script finished; origin/main =', git('rev-parse', 'origin/main').stdout.strip()[:8], 'HEAD =', git('rev-parse', 'HEAD').stdout.strip()[:8])
    files = [l for l in git('ls-files', '-o', '--exclude-standard', '-z').stdout.split('\0') if l.startswith(BIG)]
    log('tunnel files untracked:', len(files))
    sz = {f: os.path.getsize(os.path.join(REPO, f)) for f in files if os.path.isfile(os.path.join(REPO, f))}
    groups = []; groups.append(('UndergroundTunnel 맵 (텍스처 제외)', [f for f in files if not f.startswith(TEX)]))
    cur = []; cs = 0; n = 1
    for f in sorted(f for f in files if f.startswith(TEX)):
        if cur and cs + sz.get(f, 0) > LIMIT: groups.append(('UndergroundTunnel 텍스처 %d' % n, cur)); n += 1; cur = []; cs = 0
        cur.append(f); cs += sz.get(f, 0)
    if cur: groups.append(('UndergroundTunnel 텍스처 %d' % n, cur))
    for name, fl in groups:
        if not fl: continue
        for i in range(0, len(fl), 400): git('add', '-A', '--', *fl[i:i + 400])
        r = git('commit', '-q', '-m', name + TRAILER, check=False); log('commit', name, len(fl), 'files', round(sum(sz.get(f, 0) for f in fl) / 1048576), 'MB', (r.stdout + r.stderr).strip()[:80])
        c = git('rev-parse', 'HEAD').stdout.strip()
        for attempt in range(1, 6):
            r = git('push', 'origin', '%s:refs/heads/main' % c, check=False, cfg=True); out = (r.stdout + r.stderr).strip()
            log('push', name, c[:8], 'attempt', attempt, 'rc', r.returncode, out[-250:].replace('\n', ' | '))
            if r.returncode == 0: break
            time.sleep(30)
        else: log('GIVING UP at', name); return 1
        git('fetch', 'origin', check=False, cfg=True)
    log('ALL MAP CHUNKS PUSHED; origin/main =', git('rev-parse', 'origin/main').stdout.strip()[:8]); return 0
try: sys.exit(main())
except Exception as e: log('ERROR', e); sys.exit(2)
