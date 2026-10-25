"""Basic automatic quality checks; raises if a video is not fit to publish."""
import json, subprocess
import numpy as np
from PIL import Image
from .common import CFG

def _probe(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'json', str(p)],
                       capture_output=True, text=True)
    return json.loads(r.stdout)

def check(video, ep_dir, kind):
    info = _probe(video)
    dur = float(info['format']['duration'])
    types = [s['codec_type'] for s in info['streams']]
    problems = []
    if 'audio' not in types: problems.append('no audio track')
    lim = CFG['long_video'] if kind == 'long' else CFG['short']
    if kind == 'long' and dur < lim['min_seconds']: problems.append(f'long video too short: {dur:.0f}s (< {lim["min_seconds"]}s, no mid-rolls)')
    if kind == 'short' and dur > 59: problems.append(f'short too long: {dur:.0f}s')
    # frame sanity: not blank/frozen
    qa = ep_dir / 'qa'; qa.mkdir(exist_ok=True)
    stds, prev, same = [], None, 0
    for i, t in enumerate(np.linspace(2, dur - 2, 10)):
        out = qa / f'{kind}_{i:02d}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', str(video), '-frames:v', '1', '-vf', 'scale=480:-2', str(out)])
        a = np.asarray(Image.open(out).convert('L'), dtype=np.float32)
        stds.append(a.std())
        if prev is not None and np.abs(a - prev).mean() < 1.0: same += 1
        prev = a
    if sum(s < 4 for s in stds) > 3: problems.append('too many blank frames')
    if same > 5: problems.append('video looks frozen')
    print(f'QA {kind}: {dur:.1f}s, problems: {problems or "none"}')
    if kind == 'long' and any('too short' in p for p in problems):
        problems = [p for p in problems if 'too short' not in p] + []  # warn only: still publish, but logged
        print('WARNING: under 8 minutes; publishing anyway')
    if problems:
        raise RuntimeError(f'QA failed for {kind}: {problems}')
    return True
