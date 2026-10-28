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
            try:
                from . import cost; cost.tts(len(text))
            except Exception: pass
            return a_, sr
        except Exception as e:
            print('tts error', e, getattr(e, 'response', None) is not None and e.response.text[:200]); import time; time.sleep(5 * (a + 1))
    raise RuntimeError('openai tts failed')

# ---------------------------------------------------------------- ElevenLabs narrator
def _eleven_tts(text, prev='', nxt=''):
    """ElevenLabs TTS (owner Oct 28: a lively, engaging narrator). Raw 24 kHz PCM -> float32. prev/next text keep the
    intonation continuous across chunks."""
    el = V.get('elevenlabs', {})
    vid = el.get('voice_id') or 'nPczCjzI2devNBz1zQrb'
    body = {'text': text, 'model_id': el.get('model', 'eleven_multilingual_v2'),
            'voice_settings': {'stability': el.get('stability', 0.4), 'similarity_boost': el.get('similarity', 0.8),
                               'style': el.get('style', 0.35), 'use_speaker_boost': True, 'speed': el.get('speed', 1.0)}}
    if prev: body['previous_text'] = prev[-600:]
    if nxt: body['next_text'] = nxt[:600]
    for a in range(4):
        try:
            r = requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}', params={'output_format': 'pcm_24000'},
                              headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY'], 'accept': 'audio/pcm'}, json=body, timeout=300)
            r.raise_for_status()
            a_ = np.frombuffer(r.content, dtype='<i2').astype(np.float32) / 32768.0
            try:
                from . import cost; cost.tts(len(text) * 30)        # rough: ~$0.17-0.3 per 1k chars vs OpenAI
            except Exception: pass
            return a_, 24000
        except Exception as e:
            print('elevenlabs error', e, getattr(e, 'response', None) is not None and e.response.text[:300]); import time; time.sleep(5 * (a + 1))
    raise RuntimeError('elevenlabs tts failed')


def _engine():
    if V.get('engine') == 'elevenlabs' and os.environ.get('ELEVENLABS_API_KEY'): return 'elevenlabs'
    if os.environ.get('OPENAI_API_KEY'): return 'openai'
    return 'kokoro'


_n = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())

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
            starts[i] = a + (b - a) * ((i - (prev if prev is not None else -1)) / ((nxt if nxt is not None else len(starts)) - (prev if prev is not None else -1)))
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
            while part and n + len(part[0]) < 3500: take.append(part.pop(0)); n += len(take[-1]) + 1
            if not take: take = [part.pop(0)]
            chunks.append(take)
    audio, segs, t, li = [], [], 0.0, 0
    sr0 = 24000
    for ci, ch in enumerate(chunks):
        if eng == 'elevenlabs':
            try:
                a, sr = _eleven_tts(' '.join(ch), ' '.join(chunks[ci - 1]) if ci else '', ' '.join(chunks[ci + 1]) if ci + 1 < len(chunks) else '')
            except Exception as e:
                print('elevenlabs failed -> OpenAI voice for this chunk', e); a, sr = _openai_tts(' '.join(ch))
                if sr != 24000:
                    from scipy.signal import resample_poly; a = resample_poly(a, 24000, sr).astype(np.float32); sr = 24000
        else:
            a, sr = _openai_tts(' '.join(ch))
        sr0 = sr
        a = _trim(a, sr)
        tmp = str(out_wav) + '.part.wav'; sf.write(tmp, a, sr)
        ws = timing.words(tmp)
        st = _align(ch, ws, t)
        dur = len(a) / sr
        for k, txt in enumerate(ch):
            end = (st[k + 1] - 0.05) if k + 1 < len(ch) else t + dur
            segs.append({'i': li, 'text': txt, 'start': round(st[k], 3), 'end': round(end, 3)}); li += 1
        audio.append(a); t += dur
        audio.append(np.zeros(int(gap * sr), np.float32)); t += gap
    y = np.concatenate(audio[:-1]); y = y / max(1e-6, np.abs(y).max()) * 0.95
    sf.write(out_wav, y, sr0)
    return segs
