"""Generated music bed (mood per style) + sparse SFX on beats + narration, ducked and loudness-normalised, muxed onto video."""
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly
from .common import ROOT, CFG, WORK, load, sh

SR = 48000
SFX = ROOT / 'render/public/sfx'
rng = np.random.default_rng(11)

MOODS = {  # bpm, kick, hats, bass, arp, pad, timbre
    'warm':   dict(bpm=92,  kick=0.5, hats=0.10, bass=0.25, arp=0.10, pad=0.10, timbre='rhodes', key=50),
    'synth':  dict(bpm=124, kick=0.9, hats=0.25, bass=0.35, arp=0.07, pad=0.06, timbre='square', key=45),
    'light':  dict(bpm=104, kick=0.35, hats=0.12, bass=0.20, arp=0.10, pad=0.08, timbre='pluck', key=48),
    'upbeat': dict(bpm=128, kick=0.95, hats=0.28, bass=0.35, arp=0.08, pad=0.05, timbre='square', key=52),
    'dreamy': dict(bpm=84,  kick=0.25, hats=0.06, bass=0.20, arp=0.09, pad=0.16, timbre='rhodes', key=47),
    'piano':  dict(bpm=80,  kick=0.0,  hats=0.0,  bass=0.18, arp=0.12, pad=0.10, timbre='piano', key=50),
    'bouncy': dict(bpm=112, kick=0.6,  hats=0.18, bass=0.28, arp=0.11, pad=0.05, timbre='marimba', key=53),
    'tense':  dict(bpm=100, kick=0.7,  hats=0.15, bass=0.38, arp=0.06, pad=0.10, timbre='square', key=45),
}
PROG = [[0, 7, 12, 16, 19], [-3, 4, 9, 12, 16], [-7, 0, 5, 9, 12], [-5, 2, 7, 11, 14]]  # I vi IV V (semitones from key)

T = lambda n: np.arange(n) / SR
nf = lambda m: 440 * 2 ** ((m - 69) / 12)
bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], 'bp', fs=SR, output='sos'), x)
lp = lambda x, f: sosfilt(butter(2, f, 'lp', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'hp', fs=SR, output='sos'), x)

def place(buf, x, t, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if 0 <= i < len(buf): buf[i:j] += x[:j - i] * g

def note(f, dur, timbre):
    n = int(dur * SR); t = T(n); att = np.minimum(1, t / 0.004)
    if timbre == 'rhodes':
        x = np.sin(2 * np.pi * f * t + 2 * np.exp(-t / 0.25) * np.sin(2 * np.pi * f * t)) * np.exp(-t / 0.6)
    elif timbre == 'square':
        x = np.tanh(3 * np.sin(2 * np.pi * f * t)) * np.exp(-t / 0.18)
    elif timbre == 'marimba':
        x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.03)) * np.exp(-t / 0.22)
    elif timbre == 'piano':
        x = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.5 for k in (1, 2, 3, 4)) * np.exp(-t / 0.9)
    else:  # pluck
        x = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.15)
    return x * att

def music(dur, mood, calm_ranges=()):
    m = MOODS.get(mood, MOODS['warm'])
    N = int(dur * SR); out = np.zeros(N); pad = np.zeros(N)
    beat = 60 / m['bpm']; bar = beat * 4
    kn = int(0.3 * SR); tk = T(kn)
    kick = np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-tk / 0.03)) / SR) * np.exp(-tk / 0.12)
    hn = int(0.05 * SR); hat = hp(rng.standard_normal(hn), 7000) * np.exp(-T(hn) / 0.012)
    for b in range(int(dur / beat) + 1):
        t0 = b * beat
        calm = any(a <= t0 < c for a, c in calm_ranges)
        g = 0.35 if calm else 1.0
        ch = PROG[(b // 8) % 4]
        if m['kick'] and b % 2 == 0: place(out, kick, t0, m['kick'] * g * 0.6)
        if m['hats']:
            for h in (0.5,): place(out, hat, t0 + h * beat, m['hats'] * g)
        if m['bass'] and b % 2 == 0: place(out, note(nf(m['key'] + ch[0] - 12), beat * 1.6, 'pluck'), t0, m['bass'] * g)
        for q in range(2):
            place(out, note(nf(m['key'] + 12 + ch[(b * 2 + q) % 5]), beat * 1.2, m['timbre']), t0 + q * beat / 2, m['arp'] * g)
    for i in range(int(dur / bar) + 1):
        ch = PROG[(i // 2) % 4]; n = int(bar * 2 * SR); t = T(n)
        x = sum(np.sin(2 * np.pi * nf(m['key'] + 12 + c) * t) for c in ch[1:4]) / 3
        x *= np.minimum(1, np.minimum(t / 0.8, (bar * 2 - t) / 0.8))
        place(pad, lp(x, 1500), i * bar * 2, m['pad'])
    x = hp(out + pad, 35)
    ir_n = int(1.5 * SR); ir = rng.standard_normal(ir_n) * np.exp(-T(ir_n) / 0.4); ir = lp(ir, 5000); ir /= np.abs(ir).sum() ** 0.5 * 10
    x = x * 0.8 + fftconvolve(x, ir)[:N] * 0.25
    fade = int(1.5 * SR); x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.abs(x).max() + 1e-9)

def _load(name):
    x, sr = sf.read(SFX / name)
    if x.ndim > 1: x = x.mean(1)
    return resample_poly(x, SR, sr) if sr != SR else x

def finish(video, ep_dir, kind, style):
    p = load(ep_dir / f'props_{kind}.json')
    dur = p['frames'] / p['fps']
    N = int(dur * SR)
    vo, vsr = sf.read(ep_dir / f'vo_{kind}.wav')
    if vo.ndim > 1: vo = vo.mean(1)
    vo = resample_poly(vo, SR, vsr) if vsr != SR else vo
    v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
    mus = music(dur, style.get('music', 'warm'))
    fx = np.zeros(N)
    SF2 = ROOT / 'render/public/sfx2'
    cache = {}
    def snd(name):
        if name not in cache:
            f = SF2 / f'{name}.wav'
            if not f.exists(): f = SFX / f'{name}.wav'
            x, sr = sf.read(f)
            if x.ndim > 1: x = x.mean(1)
            x = resample_poly(x, SR, sr) if sr != SR else x
            x = lp(x, 9000)                                   # soften: no harsh highs
            fade = min(len(x), int(0.08 * SR)); x[-fade:] *= np.linspace(1, 0, fade)
            cache[name] = x / max(1e-6, np.abs(x).max())
        return cache[name]
    VAR = {'whoosh': 3, 'pop': 4, 'impact': 3}
    GAIN = {'whoosh': 0.13, 'pop': 0.22, 'impact': 0.28, 'tick': 0.14, 'reveal': 0.22, 'heartbeat': 0.35, 'drip': 0.25, 'bubble': 0.22,
            'riser': 0.18, 'goo': 0.2, 'shield': 0.16, 'sparkle': 0.18, 'boom': 0.3, 'bong': 0.2, 'click': 0.15,
            'ding': 0.16, 'stamp': 0.22, 'swish': 0.13, 'zip': 0.13}
    # VARIETY (owner's rule): never the same sound again and again. Each request picks the freshest sound of its family,
    # a family member is rested >= 25 s, every sound has a per-video budget, and each play gets a slightly different pitch.
    FAM = {'pop': ['pop', 'click', 'ding', 'tick'], 'click': ['click', 'pop', 'tick'], 'tick': ['tick', 'click'],
           'reveal': ['reveal', 'sparkle', 'bong', 'ding'], 'sparkle': ['sparkle', 'reveal', 'ding'], 'bong': ['bong', 'ding', 'reveal'],
           'impact': ['impact', 'stamp', 'boom'], 'boom': ['boom', 'impact', 'stamp'], 'stamp': ['stamp', 'impact'],
           'whoosh': ['whoosh', 'swish', 'zip'], 'swish': ['swish', 'whoosh', 'zip'], 'zip': ['zip', 'swish', 'whoosh'],
           'drip': ['drip', 'bubble', 'goo'], 'bubble': ['bubble', 'drip', 'goo'], 'goo': ['goo', 'bubble', 'drip'],
           'riser': ['riser'], 'shield': ['shield', 'sparkle'], 'heartbeat': ['heartbeat'], 'ding': ['ding', 'sparkle', 'pop']}
    CAP = {'pop': 7, 'whoosh': 7, 'click': 5, 'heartbeat': 2, 'riser': 3, 'boom': 2}
    used, uses, k = {}, {}, 0
    last_t = -9.0
    def pick(req, te):
        for nm in FAM.get(req, [req]):
            if te - used.get(nm, -99) >= 25 and uses.get(nm, 0) < CAP.get(nm, 4): return nm
        return None
    def play(base, te, t_end):
        nonlocal k, last_t
        k += 1
        nm = f'{base}{1 + k % VAR[base]}' if base in VAR else base
        try: x = snd(nm)
        except Exception: return
        semis = [0, -2, 1, -1, 2, -3][(uses.get(base, 0) + k) % 6]          # each play sounds a little different
        if semis and base not in ('heartbeat', 'riser'):
            up, down = {-3: (6, 5), -2: (9, 8), -1: (18, 17), 1: (17, 18), 2: (8, 9)}[semis]
            x = resample_poly(x, up, down)
        g = GAIN.get(base, 0.2)
        if base == 'riser': place(fx, x, max(0, te - len(x) / SR + 0.1), g)
        elif base == 'heartbeat':
            tt = te
            while tt < min(t_end, te + 4): place(fx, x, tt, g); tt += 0.86
        else: place(fx, x, max(0, te - (0.2 if base in ('whoosh', 'swish', 'zip') else 0)), g)
        used[base] = te; uses[base] = uses.get(base, 0) + 1; last_t = te
    for i, b in enumerate(p['beats']):
        t = b['from'] / p['fps']; t_end = b['to'] / p['fps']
        if b.get('kind') == 'gen':
            # sounds designed together with the animation, synced to its own events
            for e in (b.get('sfx_events') or []):
                te = t + e['p'] * (t_end - t)
                if te - last_t < 2.0: continue
                nm = pick(e['s'], te)
                if nm: play(nm, te, t_end)
            continue
        name = b.get('sfx')
        if name in (None, '', 'none'):
            if i > 0 and t - last_t > (4 if kind == 'short' else 9) and i % 3 == 0: name = 'whoosh'
            else: continue
        nm = pick(name, t)
        if nm: play(nm, t, t_end)
    env = np.convolve(np.abs(v), np.ones(int(0.2 * SR)) / int(0.2 * SR), 'same')
    duck = 1 - 0.6 * np.clip(env / 0.04, 0, 1)
    mix = v * 1.0 + mus * (0.15 if kind == 'long' else 0.2) * duck + fx * 0.55
    mix /= np.abs(mix).max() / 0.95
    wav = ep_dir / f'mix_{kind}.wav'
    sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), SR)
    out = ep_dir / f'final_{kind}.mp4'
    lufs = CFG['audio']['target_lufs']
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(wav), '-map', '0:v', '-map', '1:a',
        '-af', f'loudnorm=I={lufs}:TP=-1.5:LRA=11', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
        '-shortest', '-movflags', '+faststart', str(out)])
    return out


# ---- real music bed (Kevin MacLeod / incompetech.com, CC BY 4.0 -> credit line goes into the description) ----
MUSIC_LIB = ROOT / 'assets/music'
TRACKS = {'floating_cities': 'Floating Cities', 'deliberate_thought': 'Deliberate Thought', 'clean_soul': 'Clean Soul',
          'fluidscape': 'Fluidscape', 'inspired': 'Inspired', 'thinking_music': 'Thinking Music', 'investigations': 'Investigations',
          'perspectives': 'Perspectives', 'lasting_hope': 'Lasting Hope', 'healing': 'Healing'}

def credit(key):
    return f'Music: "{TRACKS[key]}" by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0 (creativecommons.org/licenses/by/4.0/)'

def pick_track(avoid=()):
    keys = [k for k in TRACKS if (MUSIC_LIB / f'{k}.mp3').exists()]
    fresh = [k for k in keys if k not in list(avoid)[-4:]] or keys
    return fresh[int(rng.integers(len(fresh)))]

def library_music(dur, key):
    """Track looped with 3 s crossfades to `dur`, RMS-normalised, 2 s fade in / 3 s fade out. Returns mono float array at SR."""
    tmp = WORK / 'music_cache' / f'{key}.wav'; tmp.parent.mkdir(parents=True, exist_ok=True)
    if not tmp.exists():
        sh(['ffmpeg', '-v', 'error', '-y', '-i', str(MUSIC_LIB / f'{key}.mp3'), '-ac', '1', '-ar', str(SR), str(tmp)])
    x, _ = sf.read(tmp)
    x = x[int(0.5 * SR):] if len(x) > 2 * SR else x
    N = int(dur * SR); xf = int(3 * SR); out = np.zeros(N); pos = 0
    while pos < N:
        seg = x.copy()
        if pos > 0: seg[:xf] *= np.linspace(0, 1, xf)
        seg[-xf:] *= np.linspace(1, 0, xf)
        place(out, seg, pos / SR)
        pos += len(x) - xf
    out /= max(1e-6, np.sqrt(np.mean(out[:min(N, 60 * SR)] ** 2))) / 0.1
    out[:2 * SR] *= np.linspace(0, 1, 2 * SR)[:len(out[:2 * SR])]
    out[-3 * SR:] *= np.linspace(1, 0, 3 * SR)[-len(out[-3 * SR:]):]
    return out
