"""Parallel rendering: the long video is split into N frame ranges rendered by separate GitHub jobs (+ one job per Short),
then concatenated losslessly. usage: python -m agent.shard <index> <count>   (last index = the Short)"""
import os, sys, subprocess
from .common import ROOT, WORK, load, sh

def run(i, n):
    cur = load(WORK / 'current.json')
    ep_dir = WORK / cur['dir']
    parts = ep_dir / 'parts'; parts.mkdir(exist_ok=True)
    return run_tl(i, n, ep_dir, parts)

def run_tl(i, n, ep_dir, parts):
    from .tl import N_SHORTS
    shorts = [k for k in range(N_SHORTS) if (ep_dir / f'props_short{k}.json').exists()]
    n_long = n - N_SHORTS
    conc = os.environ.get('RENDER_CONCURRENCY', str(max(1, os.cpu_count() or 2)))
    if i >= n_long:
        k = i - n_long
        if k not in shorts: return
        out, comp, pf, rng = parts / f'short{k}.mp4', 'TLShort', ep_dir / f'props_short{k}.json', None
    else:
        total = load(ep_dir / 'props_long.json')['frames']; step = -(-total // n_long)
        a, b = i * step, min(total, (i + 1) * step) - 1
        if a > b: return
        out, comp, pf, rng = parts / f'long_{i:02d}.mp4', 'TLLong', ep_dir / 'props_long.json', f'{a}-{b}'
    cmd = ['npx', 'remotion', 'render', 'src/index.ts', comp, str(out), f'--props={pf}', f'--concurrency={conc}', '--muted', '--log=warn']
    if rng: cmd.append(f'--frames={rng}')
    sh(cmd, cwd=ROOT / 'render')
    print('shard done', out)

def concat(ep_dir):
    parts = ep_dir / 'parts'
    if not parts.exists(): return
    longs = sorted(parts.glob('long_*.mp4'))
    if longs and not (ep_dir / 'silent_long.mp4').exists():
        lst = parts / 'list.txt'; lst.write_text(''.join(f"file '{p.resolve()}'\n" for p in longs))
        sh(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(ep_dir / 'silent_long.mp4')])
    for p in parts.glob('short*.mp4'):
        dst = ep_dir / f'silent_{p.stem}.mp4'
        if not dst.exists(): p.rename(dst)

if __name__ == '__main__':
    run(int(sys.argv[1]), int(sys.argv[2]))
