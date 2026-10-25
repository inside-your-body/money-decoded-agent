"""Real stock-footage B-roll from Pixabay (or Pexels) — free, commercial use allowed, no attribution required.
For every beat the storyboard gave a search query: find a clip, cut it to the beat length, scale/crop it to the video format
and store it in <ep>/broll/. Long beats (> 5.5 s) get two different clips so the picture changes every few seconds.
A Claude vision check drops clips that don't fit the sentence. Without PEXELS_API_KEY (or when nothing fits) the beat simply keeps its code-drawn graphic."""
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
        vs = h.get('videos') or {}
        files = [{'file_type': 'video/mp4', 'width': v.get('width'), 'height': v.get('height'), 'link': v.get('url')}
                 for v in vs.values() if v.get('url') and v.get('width')]
        thumb = next((vs[k].get('thumbnail') for k in ('small', 'tiny', 'medium', 'large') if (vs.get(k) or {}).get('thumbnail')), None)
        if not thumb and h.get('picture_id'): thumb = f"https://i.vimeocdn.com/video/{h['picture_id']}_640x360.jpg"   # older API shape
        out.append({'id': 'pb' + str(h.get('id')), 'duration': h.get('duration', 0), 'video_files': files, 'image': thumb,
                    'tags': h.get('tags', '')})
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


def _thumb_b64(url):
    """Small JPEG of a clip's preview frame for the vision check (~100 tokens each)."""
    import base64, io
    from PIL import Image
    r = requests.get(url, timeout=30); r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert('RGB'); im.thumbnail((384, 384))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=70)
    return base64.b64encode(b.getvalue()).decode()


def _vision_pick(jobs):
    """Owner (Oct 25): footage must fit the sentence (no cigarette for 'your money leaves the bank').
    jobs = [(beat_key, sentence, query, [candidates])]. One Claude vision call per batch -> {beat_key: [candidate indexes, best first]}.
    A beat whose candidates are all off-topic gets [] and keeps its motion graphic."""
    from . import llm
    picks = {}
    for i in range(0, len(jobs), 6):
        batch = jobs[i:i + 6]
        content, lines = [], []
        for bk, text, q, cands in batch:
            lines.append(f'BEAT {bk}: "{text}" (search: {q}) — {len(cands)} frames')
            for n, v in enumerate(cands):
                try:
                    content.append({'type': 'text', 'text': f'BEAT {bk} frame {n}:'})
                    content.append({'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': _thumb_b64(v['image'])}})
                except Exception:
                    content.pop()
        content.append({'type': 'text', 'text': """You pick stock footage for a finance documentary (money, banks, markets).
For every beat below you saw preview frames of candidate clips. Keep ONLY frames a viewer would accept as illustrating that sentence
(literally or as a clear, natural visual metaphor: e.g. "the bank" -> a bank building, a teller, a city financial district; "money is created"
-> banknotes, a keyboard, a banking screen). Reject anything unrelated or odd (smoking, sport, random nature, a fan, food, animals, beauty shots),
anything with a visible brand/logo up front, and anything that could mislead. Order the kept frames best first.
""" + '\n'.join(lines) + """
Return JSON only: {"BEAT_KEY": [frame numbers, best first], ...} — include every beat; [] when none fits."""})
        try:
            r = llm._repair(llm.ask(content, max_tokens=1500, retries=2, effort='low')) or {}
        except Exception as e:
            print('vision pick failed -> keep search order', e); r = {}
        for bk, _, _, cands in batch:
            v = r.get(str(bk))
            picks[bk] = [int(x) for x in v if str(x).isdigit() and int(x) < len(cands)] if isinstance(v, list) else list(range(len(cands)))
    return picks


def attach(props, ep_dir, kind):
    """Adds 'clips': ['ep/broll/<file>.mp4', ...] to every beat that has a query and a matching, on-topic clip."""
    if not (os.environ.get('PEXELS_API_KEY') or os.environ.get('PIXABAY_API_KEY')):
        print('no PIXABAY_API_KEY / PEXELS_API_KEY -> graphics only'); return props
    vertical = bool(props.get('vertical'))
    out = pathlib.Path(ep_dir) / 'broll'; out.mkdir(exist_ok=True)
    # 1) candidates per beat
    jobs, meta = [], {}
    for k, b in enumerate(props['beats']):
        q = b.get('q')
        if not q: continue
        dur = (b['end'] - b['start']) / FPS
        parts = 2 if dur > 5.5 else 1
        vids = _search(q, 'portrait' if vertical else 'landscape') or _search(q, 'landscape' if vertical else 'portrait')
        if not vids and len(q.split()) > 2: vids = _search(' '.join(q.split()[:2]), 'landscape')   # broader query
        cands = [v for v in vids if v.get('duration', 0) >= dur / parts + 1 and _pick_file(v, vertical)][:6]
        if not cands: continue
        meta[k] = (dur, parts, cands)
        jobs.append((k, b.get('text') or q, q, cands))
    # 2) vision check: only clips that fit the sentence (needs preview images; without them keep the search order)
    if os.environ.get('ANTHROPIC_API_KEY') and any(c.get('image') for _, _, _, cs in jobs for c in cs):
        jobs = [(k, t, q, [c for c in cs if c.get('image')]) for k, t, q, cs in jobs]
        jobs = [j for j in jobs if j[3]]
        meta = {k: (meta[k][0], meta[k][1], cs) for k, _, _, cs in jobs}
        picks = _vision_pick(jobs)
    else:
        picks = {k: list(range(len(m[2]))) for k, m in meta.items()}
    # 3) cut the chosen clips
    used, n_ok, n_rej = set(), 0, 0
    for k, (dur, parts, cands) in meta.items():
        b = props['beats'][k]; clips = []
        order = picks.get(k, [])
        if not order: n_rej += 1
        for n in order:
            v = cands[n]
            if len(clips) == parts: break
            if v['id'] in used: continue
            name = f'{kind}_{k:03d}_{len(clips)}.mp4'
            try:
                off = min(1.0, max(0, v.get('duration', 0) - dur / parts - 0.5))
                if _cut(_pick_file(v, vertical), out / name, dur / parts, vertical, off):
                    clips.append('ep/broll/' + name); used.add(v['id'])
            except Exception as e:
                print('clip failed', b.get('q'), e)
        if clips:
            b['clips'] = clips; n_ok += 1
    n_q = sum(1 for b in props['beats'] if b.get('q'))
    print(f'broll {kind}: {n_ok}/{n_q} beats with footage, {n_rej} rejected as off-topic ({len(props["beats"])} beats)')
    return props


def stage(ep_dir):
    """Copy the clips where Remotion can serve them (render/public/ep/broll)."""
    src = pathlib.Path(ep_dir) / 'broll'
    if not src.exists(): return
    dst = ROOT / 'render/public/ep/broll'; dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob('*.mp4'):
        t = dst / f.name
        if not t.exists(): t.write_bytes(f.read_bytes())
