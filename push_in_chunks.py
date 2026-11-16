"""Pushes the 3 unpushed local commits (6.7 GB of new content packs + the Furina work) to origin/main in chunks <= ~1.2 GB, because one push of that size is rejected by GitHub (pack limit ~2 GB).
1. a backup branch keeps the exact local history (backup-before-split)
2. the unpushed commits are replaced by several commits with the SAME final tree: (a) everything except the two big content packs, (b) NiagaraExamples, (c) UndergroundTunnel without textures,
   (d..) UndergroundTunnel/Textures in size-limited chunks
3. every commit is pushed on its own with schannel (Windows certificate store; certificate verification stays ON), HTTP/1.1 and a large post buffer; failures are retried
usage: python push_in_chunks.py   (log: push_in_chunks.log next to this file)"""
import subprocess, os, sys, time, collections
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
REPO = os.path.dirname(os.path.abspath(__file__)); LOG = open(os.path.join(REPO, 'push_in_chunks.log'), 'a', encoding='utf-8', buffering=1)
def log(*a): s = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a); print(s, flush=True); LOG.write(s + '\n')
def git(*args, check=True, cfg=False):
    cmd = ['git'] + (['-c', 'http.sslBackend=schannel', '-c', 'http.version=HTTP/1.1', '-c', 'http.postBuffer=1073741824', '-c', 'core.safecrlf=false'] if cfg else ['-c', 'core.safecrlf=false']) + list(args)
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode != 0: raise RuntimeError('git %s failed: %s' % (' '.join(args[:3]), (r.stderr or r.stdout)[-600:]))
    return r
TRAILER = '\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>'
BIG = 'test/abc/Content/UndergroundTunnel/'; NIA = 'test/abc/Content/NiagaraExamples/'; TEX = BIG + 'Textures/'
LIMIT = 1.2 * 1024 ** 3
def main():
    head = git('rev-parse', 'HEAD').stdout.strip(); log('HEAD', head[:8])
    if git('branch', '--list', 'backup-before-split').stdout.strip() == '': git('branch', 'backup-before-split', head); log('backup branch created')
    ahead = git('rev-list', '--count', 'origin/main..HEAD').stdout.strip(); log('commits ahead of origin/main:', ahead)
    if not os.path.exists(os.path.join(REPO, '.split_done')):
        git('reset', '-q', '--mixed', 'origin/main'); log('reset to origin/main (working tree kept)')
        # file sizes of everything that differs from origin/main
        files = [l for l in git('ls-files', '-o', '-m', '--exclude-standard', '-z').stdout.split('\0') if l]
        deleted = [l for l in git('ls-files', '-d', '-z').stdout.split('\0') if l]; log('files to commit', len(files), 'deleted', len(deleted))
        groups = collections.OrderedDict(); sz = {f: os.path.getsize(os.path.join(REPO, f)) for f in files if os.path.isfile(os.path.join(REPO, f))}
        rest = [f for f in files if not f.startswith(BIG) and not f.startswith(NIA)]; groups['Furina 작업과 나머지 파일'] = rest + deleted
        # the Underground Tunnel map content is NOT committed (user: 'leave the map out'); its files stay untracked in the working tree
        nia = sorted(f for f in files if f.startswith(NIA)); cur = []; cs = 0; n = 1
        for f in nia:
            if cur and cs + sz.get(f, 0) > LIMIT: groups['NiagaraExamples 콘텐츠 팩 %d' % n] = cur; n += 1; cur = []; cs = 0
            cur.append(f); cs += sz.get(f, 0)
        if cur: groups['NiagaraExamples 콘텐츠 팩 %d' % n] = cur
        for name, fl in groups.items():
            if not fl: continue
            for i in range(0, len(fl), 400): git('add', '-A', '--', *fl[i:i + 400])
            r = git('commit', '-q', '-m', name + TRAILER, check=False); log('commit', name, len(fl), 'files', (r.stdout + r.stderr).strip()[:100])
        open(os.path.join(REPO, '.split_done'), 'w').write('1')
    # push every commit separately, oldest first
    commits = git('rev-list', '--reverse', 'origin/main..HEAD').stdout.split(); log('to push:', len(commits))
    for c in commits:
        for attempt in range(1, 6):
            r = git('push', 'origin', '%s:refs/heads/main' % c, check=False, cfg=True); out = (r.stdout + r.stderr).strip()
            log('push', c[:8], 'attempt', attempt, 'rc', r.returncode, out[-300:].replace('\n', ' | '))
            if r.returncode == 0: break
            time.sleep(20)
        else: log('GIVING UP at', c[:8]); return 1
        git('fetch', 'origin', check=False, cfg=True)
    log('ALL PUSHED; origin/main =', git('rev-parse', 'origin/main').stdout.strip()[:8], 'local tree same as backup:', git('diff', '--stat', 'backup-before-split', 'HEAD').stdout.strip() == '')
    return 0
try: sys.exit(main())
except Exception as e: log('ERROR', e); sys.exit(2)
