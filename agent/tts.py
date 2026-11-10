"""Fixed narrator voice (locked in config). engine "elevenlabs" (needs ELEVENLABS_API_KEY) or OpenAI gpt-4o-mini-tts, voice "ballad", storytelling instructions.
Fallback: Kokoro (am_michael 0.55 + am_fenrir 0.45)."""
import os, re, io, difflib, requests
import numpy as np, soundfile as sf, urllib.request, pathlib
from .common import CFG, WORK

V = CFG['voice']
MODEL_DIR = WORK / 'tts_model'

def _model():
    from kokoro_onnx import Kokoro
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    m, v = MODEL_DIR / 'kokoro.onnx', MODEL_DIR / 'voices.bin'
    for url, p in ((V['model_url'], m), (V['voices_url'], v)):
        if not p.exists():
            print('downloading', url); urllib.request.urlretrieve(url, p)
    k = Kokoro(str(m), str(v))
    style = sum(k.get_voice_style(name) * w for name, w in V['blend'].items())
    return k, style

def _trim(a, sr):
    idx = np.where(np.abs(a) > 0.01)[0]
    return a if len(idx) == 0 else a[max(0, idx[0] - int(0.01 * sr)): idx[-1] + int(0.02 * sr)]

def synth_lines_kokoro(lines, out_wav, gap=0.22, long_gap_after=()):
    """lines: list of sentences. Returns list of {text,start,end} in seconds."""
    k, style = _model()
    sr = 24000; chunks = []; segs = []; t = 0.0
    for i, txt in enumerate(lines):
        a, sr = k.create(txt, voice=style, speed=V['speed'], lang='en-us')
        a = _trim(np.asarray(a, np.float32), sr)
        segs.append({'i': i, 'text': txt, 'start': t, 'end': t + len(a) / sr})
        chunks.append(a); t += len(a) / sr
        if i < len(lines) - 1:
            g = 0.45 if i in long_gap_after else gap
            chunks.append(np.zeros(int(g * sr), np.float32)); t += g
    y = np.concatenate(chunks); y = y / max(1e-6, np.abs(y).max()) * 0.95
    sf.write(out_wav, y, sr)
    return segs


# ---------------------------------------------------------------- OpenAI narrator
def _openai_tts(text):
    oa = V.get('openai', {})
    for a in range(4):
        try:
            r = requests.post('https://api.openai.com/v1/audio/speech', timeout=300,
                              headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']},
                              json={'model': oa.get('model', 'gpt-4o-mini-tts'), 'voice': oa.get('voice', 'ballad'), 'input': text,
                                    'instructions': oa.get('instructions', ''), 'response_format': 'wav'})
            r.raise_for_status()
            a_, sr = sf.read(io.BytesIO(r.content), dtype='float32')
            if a_.ndim > 1: a_ = a_.mean(1)
            sp = float(oa.get('speed', 1.0))
            if abs(sp - 1.0) > 0.01: a_ = _tempo(a_, sr, sp)     # owner Oct 28: a bit faster, same pitch
            try:
                from . import cost; cost.tts(len(text))
            except Exception: pass
            return a_, sr
        except Exception as e:
            print('tts error', e, getattr(e, 'response', None) is not None and e.response.text[:200]); import time; time.sleep(5 * (a + 1))
    raise RuntimeError('openai tts failed')

# ---------------------------------------------------------------- ElevenLabs narrator
USAGE = pathlib.Path(__file__).resolve().parents[1] / 'data/eleven_usage.json'


def _usage():
    import json, datetime as dt
    m = dt.datetime.utcnow().strftime('%Y-%m')
    try: u = json.loads(USAGE.read_text())
    except Exception: u = {}
    return u, m


def _count(chars):
    """Owner (Nov 9): the 600k monthly plan is shared with other channels -> this channel keeps its own monthly tally."""
    import json            # counted per run in work/ (the build job's repo copy is thrown away); run.py adds it to data/ at the end
    f = WORK / 'eleven_chars.json'
    try: n = json.loads(f.read_text()).get('chars', 0)
    except Exception: n = 0
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps({'chars': n + int(chars)}))


def commit_usage():
    import json
    try: n = json.loads((WORK / 'eleven_chars.json').read_text()).get('chars', 0)
    except Exception: return
    u, m = _usage(); u[m] = u.get(m, 0) + n
    USAGE.parent.mkdir(parents=True, exist_ok=True); USAGE.write_text(json.dumps(u, indent=1))
    (WORK / 'eleven_chars.json').unlink(missing_ok=True); print('ElevenLabs credits this month:', u[m])


def credits_left_this_month():
    if V.get('engine') != 'elevenlabs': return None
    u, m = _usage()
    return int(V.get('elevenlabs', {}).get('monthly_credit_cap', 290000)) - u.get(m, 0)


_MODEL = {}


def _eleven_tts(text, prev='', nxt=''):
    """ElevenLabs narrator «Aran - Parsi» (owner Nov 9). Tries the configured models in order (eleven_v4 first); raw 24 kHz PCM."""
    el = V.get('elevenlabs', {})
    vid = el['voice_id']
    models = ([_MODEL['ok']] if _MODEL.get('ok') else []) + [m for m in el.get('models', ['eleven_v4', 'eleven_v3', 'eleven_multilingual_v2']) if m != _MODEL.get('ok')]
    last = None
    for model in models:
        body = {'text': text, 'model_id': model,
                'voice_settings': {'stability': el.get('stability', 0.4), 'similarity_boost': el.get('similarity', 0.75),
                                   'style': el.get('style', 0.1), 'use_speaker_boost': True, 'speed': el.get('speed', 1.2)}}
        if prev and model != 'eleven_v3': body['previous_text'] = prev[-600:]
        if nxt and model != 'eleven_v3': body['next_text'] = nxt[:600]
        for a in range(3):
            r = requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}', params={'output_format': 'pcm_24000'},
                              headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY'], 'accept': 'audio/pcm'}, json=body, timeout=300)
            if r.ok:
                _MODEL['ok'] = model; _count(len(text))
                try:
                    from . import cost; cost.tts(len(text) * 30)
                except Exception: pass
                return np.frombuffer(r.content, dtype='<i2').astype(np.float32) / 32768.0, 24000
            last = r.text[:300]
            if r.status_code in (400, 404, 422) and ('model' in last.lower()): break       # model not available -> next model
            if r.status_code in (401, 402, 403): raise RuntimeError('ElevenLabs refused: ' + last)   # plan/credits/key problem
            import time; time.sleep(5 * (a + 1))
    raise RuntimeError('ElevenLabs failed: ' + str(last))


def _engine():
    if V.get('engine') == 'elevenlabs':
        if not os.environ.get('ELEVENLABS_API_KEY'): raise RuntimeError('ELEVENLABS_API_KEY missing (owner: always the Aran - Parsi voice)')
        return 'elevenlabs'
    if os.environ.get('OPENAI_API_KEY'): return 'openai'
    return 'kokoro'


def _tempo(a, sr, sp):
    """Speed up/down without changing the pitch (ffmpeg atempo)."""
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        i, o = f'{d}/i.wav', f'{d}/o.wav'; sf.write(i, a, sr)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', i, '-filter:a', f'atempo={sp:.3f}', o], check=True)
        b, _ = sf.read(o, dtype='float32')
    return b.mean(1) if b.ndim > 1 else b


_FA = str.maketrans({'ي': 'ی', 'ك': 'ک', 'ى': 'ی', 'ة': 'ه', 'ۀ': 'ه', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', '\u200c': '', '\u064b': '', '\u064c': '', '\u064d': '',
                    '\u064e': '', '\u064f': '', '\u0650': '', '\u0651': '', '\u0652': '', '\u0654': '', '۰': '0', '۱': '1', '۲': '2', '۳': '3',
                    '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'})
# normalised token for matching script words with whisper words (Latin AND Persian letters; owner Nov 8: Persian channel)
_n = lambda w: re.sub(r'[^\w]', '', w.lower().translate(_FA)).replace('_', '')

def _align(lines, words, t0):
    """Map each script line to its start time using whisper words (difflib over normalised tokens)."""
    script = []
    for li, l in enumerate(lines):
        for w in l.split():
            if _n(w): script.append((li, _n(w)))
    heard = [_n(w['w']) for w in words]
    sm = difflib.SequenceMatcher(a=[x[1] for x in script], b=heard, autojunk=False)
    first = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            li = script[blk.a + k][0]
            first.setdefault(li, (blk.a + k, words[blk.b + k]['s']))
    starts = []
    for li in range(len(lines)):
        if li in first:
            # correct for unmatched leading words of the line
            idx, s = first[li]; lead = idx - next(i for i, x in enumerate(script) if x[0] == li)
            starts.append(max(0.0, s - lead * 0.35))
        else:
            starts.append(None)
    # fill gaps by interpolation on word counts
    for i in range(len(starts)):
        if starts[i] is None:
            prev = next((j for j in range(i - 1, -1, -1) if starts[j] is not None), None)
            nxt = next((j for j in range(i + 1, len(starts)) if starts[j] is not None), None)
            a = starts[prev] if prev is not None else 0.0
            b = starts[nxt] if nxt is not None else (words[-1]['e'] if words else a + 2)
            lo = prev if prev is not None else -1; hi = nxt if nxt is not None else len(starts)
            # spread by characters, not by line count
            span = sum(len(lines[j]) for j in range(max(0, lo), hi)) or 1
            starts[i] = a + (b - a) * (sum(len(lines[j]) for j in range(max(0, lo), i)) / span)
    starts[0] = 0.0
    return [s + t0 for s in starts]

def synth_lines(lines, out_wav, groups=None, gap=0.35, **kw):
    """lines: sentences; groups: list of line counts per paragraph (scene). Returns segs [{i,text,start,end}]."""
    eng = _engine()
    if eng == 'kokoro':
        return synth_lines_kokoro(lines, out_wav, **kw)
    print('narrator engine:', eng)
    from . import timing
    groups = groups or [len(lines)]
    # keep each request well under the API input limit
    chunks, i = [], 0
    for g in groups:
        part = lines[i:i + g]; i += g
        while part:
            take, n = [], 0
            while part and n + len(part[0]) < 2400: take.append(part.pop(0)); n += len(take[-1]) + 1
            if not take: take = [part.pop(0)]
            chunks.append(take)
    audio, segs, t, li = [], [], 0.0, 0
    sr0 = 24000
    for ci, ch in enumerate(chunks):
        from .fa_text import speakable
        say = [speakable(x) for x in ch] if CFG['channel'].get('language') == 'fa' else ch     # numbers/symbols as words for the narrator
        if eng == 'elevenlabs':     # owner: never another voice -> no fallback, a failure stops the episode
            a, sr = _eleven_tts(' '.join(say), ' '.join(chunks[ci - 1]) if ci else '', ' '.join(chunks[ci + 1]) if ci + 1 < len(chunks) else '')
        else:
            a, sr = _openai_tts(' '.join(say))
        sr0 = sr
        a = _trim(a, sr)
        tmp = str(out_wav) + '.part.wav'; sf.write(tmp, a, sr)
        ws = timing.words(tmp)
        st = _align(say, ws, t)
        dur = len(a) / sr
        for k, txt in enumerate(ch):
            end = (st[k + 1] - 0.05) if k + 1 < len(ch) else t + dur
            segs.append({'i': li, 'text': txt, 'start': round(st[k], 3), 'end': round(end, 3)}); li += 1
        audio.append(a); t += dur
        audio.append(np.zeros(int(gap * sr), np.float32)); t += gap
    y = np.concatenate(audio[:-1]); y = y / max(1e-6, np.abs(y).max()) * 0.95
    sf.write(out_wav, y, sr0)
    return segs
