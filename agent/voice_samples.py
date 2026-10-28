"""Voice audition (owner Oct 28): the same 30-second paragraph read by several ElevenLabs narrators (+ 2 OpenAI voices),
saved as samples/voices/NN_name.mp3 with samples/voices/README.md, so the owner can pick the channel's narrator."""
import os, io, json, subprocess, pathlib, requests
import numpy as np, soundfile as sf
from .common import ROOT, CFG

TEXT = ("A loan officer taps a key, and three hundred thousand dollars appears in your account. One second earlier, that money "
        "did not exist. Nobody printed it. Nobody carried it in from a vault. So where did it come from? Most of us were taught a "
        "comforting story about this... and the Bank of England says it's not quite how it works. Here's the twist: when you pay "
        "that loan back, the money doesn't go to another borrower. It simply disappears.")
# premade narrators known to work well for documentaries (used if the account list can't be read)
KNOWN = {'Brian': 'nPczCjzI2devNBz1zQrb', 'George': 'JBFqnCBsd6RMkjVDRZzb', 'Daniel': 'onwK4e9ZLuTAKqWW03F9',
         'Adam': 'pNInz6obpgDQGcFmaJgB', 'Liam': 'TX3LPaxmHKxFdv7VOQHJ', 'Bill': 'pqHfZKP75CvOlQylNhV4',
         'Eric': 'cjVigY5qzO86Huf0OWal', 'Chris': 'iP95p4xoKVk53GoZ742B'}
GOOD_USE = ('narration', 'narrative', 'informative', 'documentary', 'educational', 'story', 'news', 'conversational')


def _mp3(a, sr, dst):
    wav = str(dst) + '.wav'; sf.write(wav, a / max(1e-6, np.abs(a).max()) * 0.95, sr)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-b:a', '128k', str(dst)], check=True); os.unlink(wav)


def candidates():
    key = os.environ['ELEVENLABS_API_KEY']
    out = {}
    try:
        r = requests.get('https://api.elevenlabs.io/v1/voices', headers={'xi-api-key': key}, timeout=60); r.raise_for_status()
        for v in r.json().get('voices', []):
            lab = {k: str(x).lower() for k, x in (v.get('labels') or {}).items()}
            txt = ' '.join(lab.values()) + ' ' + (v.get('description') or '').lower()
            if v.get('category') in ('premade', 'professional', 'cloned', 'generated') and any(u in txt for u in GOOD_USE):
                out[v['name']] = (v['voice_id'], ', '.join(f'{k}: {x}' for k, x in lab.items()))
    except Exception as e:
        print('voice list failed', e)
    for n, vid in KNOWN.items():
        if not any(i == vid for i, _ in out.values()): out.setdefault(n, (vid, 'premade narrator'))
    return dict(list(out.items())[:12])


def channel_voice():
    """Just the configured channel narrator (current settings) -> samples/voices/channel_voice.mp3"""
    from . import tts
    d = ROOT / 'samples/voices'; d.mkdir(parents=True, exist_ok=True)
    a, sr = tts._openai_tts(TEXT); _mp3(a, sr, d / 'channel_voice.mp3')
    print('channel voice:', tts.V['openai'].get('voice'), 'speed', tts.V['openai'].get('speed'), f'{len(a) / sr:.1f}s')


def main():
    if os.environ.get('MODE') == 'channel':
        return channel_voice()
    from . import tts
    d = ROOT / 'samples/voices'; d.mkdir(parents=True, exist_ok=True)
    rows = []
    for k, (name, (vid, desc)) in enumerate(candidates().items(), 1):
        try:
            tts.V.setdefault('elevenlabs', {})['voice_id'] = vid
            a, sr = tts._eleven_tts(TEXT)
            f = d / f'{k:02d}_{name.split()[0].lower()}.mp3'; _mp3(a, sr, f)
            rows.append(f'| {k:02d} | ElevenLabs — {name} | `{vid}` | {desc} |'); print('ok', name)
        except Exception as e:
            print('sample failed', name, e)
    for j, voice in enumerate(['ash', 'verse'], len(rows) + 1):
        try:
            tts.V.setdefault('openai', {})['voice'] = voice; tts.V['openai']['speed'] = 1.0
            a, sr = tts._openai_tts(TEXT)
            f = d / f'{j:02d}_openai_{voice}.mp3'; _mp3(a, sr, f)
            rows.append(f'| {j:02d} | OpenAI — {voice} | — | cheap option |')
        except Exception as e:
            print('openai sample failed', voice, e)
    (d / 'README.md').write_text('# Narrator audition\n\n| # | voice | id | labels |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n')
    print('\n'.join(rows))


if __name__ == '__main__':
    main()
