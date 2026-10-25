"""Real stock-footage B-roll from Pixabay (or Pexels) — free, commercial use allowed, no attribution required.
For every beat the storyboard gave a search query: find a clip, cut it to the beat length, scale/crop it to the video format
and store it in <ep>/broll/. Long beats (> 5.5 s) get two different clips so the picture changes every few seconds.
Without PEXELS_API_KEY (or when nothing fits) the beat simply keeps its code-drawn graphic."""
import os, json, subprocess, tempfile, pathlib, requests
from .common import ROOT

API = 'https://api.pexels.com/videos/search'
PIXABAY = 'https://pixabay.com/api/videos/'
FPS = 30
_cache = {}


def _pixabay(q):
    """Pixabay hits converted to the Pexels-like shape the rest of this module uses."""
    try:
        r = requests.get(PIXABAY, params={'key': os.environ['PIXABAY_API_KEY'], 'q': q[:100], 'per_page': 20, 'safesearch': 'true',
                                          'order': 'popular'}, timeout=30)
        r.raise_for_status(); hits = r.json().get('hits', [])
    except Exception as e:
        print('pixabay search failed', q, e); return []
    out = []
    for h in hits:
        files = [{'file_type': 'video/mp4', 'width': v.get('width'), 'height': v.get('height'), 'link': v.get('url')}
                 for v in (h.get('videos') or {}).values() if v.get('url') and v.get('width')]
        out.append({'id': 'pb' + str(h.get('id')), 'duration': h.get('duration', 0), 'video_files': files})
    return out


def _search(q, orientation):
    key = (q.lower(), orientation)
    if key in _cache: return _cache[key]
    if os.environ.get('PIXABAY_API_KEY') and not os.environ.get('PEXELS_API_KEY'):
        _cache[key] = _pixabay(q); return _cache[key]
    try:
        r = requests.get(API, params={'query': q, 'orientation': orientation, 'per_page': 15, 'size': 'medium'},
                         headers={'Authorization': os.environ['PEXELS_API_KEY']}, timeout=30)
        r.raise_for_status(); vids = r.json().get('videos', [])
    except Exception as e:
        print('pexels search failed', q, e); vids = []
    _cache[key] = vids
    return vids


def _pick_file(v, vertical):
    files = [f for f in v.get('video_files', []) if f.get('file_type') == 'video/mp4' and f.get('width') and f.get('height')]
    if not files: return None
    want = 1920 if not vertical else 1080          # the long side we would like (long: width, short: width of a portrait clip)
    side = (lambda f: f['width']) if not vertical else (lambda f: f['width'])
    good = [f for f in files if side(f) >= want * 0.6]
    return min(good or files, key=lambda f: abs(side(f) - want))['link']


def _cut(url, dst, dur, vertical, offset):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            for chunk in r.iter_content(1 << 20): tmp.write(chunk)
        src = tmp.name
    try:
        vf = f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{offset:.2f}', '-i', src, '-t', f'{dur + 0.4:.2f}', '-an', '-vf', vf,
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '27', '-pix_fmt', 'yuv420p', str(dst)], check=True, timeout=300)
    finally:
        os.unlink(src)
    return dst.exists() and dst.stat().st_size > 10000


def attach(props, ep_dir, kind):
    """Adds 'clips': ['ep/broll/<file>.mp4', ...] to every beat that has a query and a matching clip."""
    if not (os.environ.get('PEXELS_API_KEY') or os.environ.get('PIXABAY_API_KEY')):
        print('no PIXABAY_API_KEY / PEXELS_API_KEY -> graphics only'); return props
    vertical = bool(props.get('vertical'))
    out = pathlib.Path(ep_dir) / 'broll'; out.mkdir(exist_ok=True)
    used, n_ok, n_q = set(), 0, 0
    for k, b in enumerate(props['beats']):
        q = b.get('q')
        if not q: continue
        n_q += 1
        dur = (b['end'] - b['start']) / FPS
        parts = 2 if dur > 5.5 else 1
        clips = []
        vids = _search(q, 'portrait' if vertical else 'landscape') or _search(q, 'landscape' if vertical else 'portrait')
        if not vids and len(q.split()) > 2: vids = _search(' '.join(q.split()[:2]), 'landscape')   # broader query
        for v in vids:
            if len(clips) == parts: break
            if v['id'] in used or v.get('duration', 0) < dur / parts + 1: continue
            url = _pick_file(v, vertical)
            if not url: continue
            name = f'{kind}_{k:03d}_{len(clips)}.mp4'
            try:
                off = min(1.0, max(0, v.get('duration', 0) - dur / parts - 0.5))
                if _cut(url, out / name, dur / parts, vertical, off):
                    clips.append('ep/broll/' + name); used.add(v['id'])
            except Exception as e:
                print('clip failed', q, e)
        if clips:
            b['clips'] = clips; n_ok += 1
    print(f'broll {kind}: {n_ok}/{n_q} beats with footage ({len(props["beats"])} beats)')
    return props


def stage(ep_dir):
    """Copy the clips where Remotion can serve them (render/public/ep/broll)."""
    src = pathlib.Path(ep_dir) / 'broll'
    if not src.exists(): return
    dst = ROOT / 'render/public/ep/broll'; dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob('*.mp4'):
        t = dst / f.name
        if not t.exists(): t.write_bytes(f.read_bytes())
