"""UE CSV 프로파일 요약: python csv_perf_summary.py <csv> [상위N]  -> 프레임/게임/렌더/GPU 평균·p95, 스레드/GPU 항목 상위"""
import csv, sys, statistics as st
f = sys.argv[1]; top = int(sys.argv[2]) if len(sys.argv) > 2 else 12
rows = list(csv.reader(open(f, encoding='utf-8', errors='replace')))
hdr = rows[0]; data = []
for r in rows[1:]:
    try: data.append([float(x) if x != '' else 0.0 for x in r[:len(hdr)]])
    except ValueError: continue
data = data[10:] if len(data) > 40 else data   # 처음 몇 프레임(시작 히치) 제외
def col(n): i = hdr.index(n); return [d[i] for d in data if len(d) > i]
def line(n):
    v = col(n); return '%-22s avg %7.2f  median %7.2f  p95 %7.2f  max %7.2f' % (n, st.mean(v), st.median(v), sorted(v)[int(len(v) * .95)], max(v))
print(f, 'frames', len(data))
for n in ('FrameTime', 'GameThreadTime', 'RenderThreadTime', 'RHIThreadTime', 'GPUTime'):
    if n in hdr: print(line(n))
print('avg fps %.1f' % (1000 / st.mean(col('FrameTime'))))
def tops(prefix, k):
    items = [(st.mean(col(n)), n) for n in hdr if n.startswith(prefix)]
    for v, n in sorted(items, reverse=True)[:k]: print('  %7.3f ms  %s' % (v, n))
print('GPU'); tops('GPU/', top)
print('GameThread exclusive'); tops('Exclusive/GameThread/', top)
print('RenderThread exclusive'); tops('Exclusive/RenderThread/', top)
