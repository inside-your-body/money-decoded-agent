"""Word-level timings with faster-whisper (base.en)."""
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

def words(wav):
    from faster_whisper import WhisperModel
    a, sr = sf.read(wav, dtype='float32')
    if a.ndim > 1: a = a.mean(1)
    if sr != 16000:
        from math import gcd
        g = gcd(sr, 16000); a = resample_poly(a, 16000 // g, sr // g).astype(np.float32)
    m = WhisperModel('base.en', compute_type='int8')
    segs, _ = m.transcribe(a, word_timestamps=True, language='en')
    out = []
    for s in segs:
        for w in s.words:
            st, en = float(w.start), float(w.end)
            if en - st > 0.45: st = en - 0.35   # whisper absorbs pauses into the next word
            out.append({'w': w.word.strip(), 's': round(st, 3), 'e': round(en, 3)})
    return out
