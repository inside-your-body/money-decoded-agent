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


# ---- Persian channel (owner Nov 9): ElevenLabs "Aran - Parsi", eleven_v4, stability 0.4, similarity 0.75, low style, speed 1.2 ----
FA_VOICE = 'PEdcOLzbXYhL8IKOswXB'
FA_TEXT = ("فکر کن یه روز صبح بیدار می‌شی و می‌بینی پولی که توی حسابته، دیگه نصف چیزایی که دیروز می‌خرید رو نمی‌خره. "
           "هیچ‌کس ازت دزدی نکرده، ولی پولت آب شده. سؤال اینه: این پول دقیقاً کجا رفت؟")


def fa_voice():
    """Connection test with the Persian narrator -> samples/voices/fa_test.mp3 + credits left (samples/voices/fa_test.json)."""
    key = os.environ['ELEVENLABS_API_KEY']; hdr = {'xi-api-key': key}
    d = ROOT / 'samples/voices'; d.mkdir(parents=True, exist_ok=True)
    info = {'voice_id': FA_VOICE, 'chars': len(FA_TEXT)}
    try:
        sub = requests.get('https://api.elevenlabs.io/v1/user/subscription', headers=hdr, timeout=60).json()
        info.update(tier=sub.get('tier'), used=sub.get('character_count'), limit=sub.get('character_limit'),
                    resets=sub.get('next_character_count_reset_unix'))
    except Exception as e: info['subscription_error'] = str(e)
    try:
        v = requests.get(f'https://api.elevenlabs.io/v1/voices/{FA_VOICE}', headers=hdr, timeout=60).json()
        info['voice_name'] = v.get('name')
    except Exception as e: info['voice_error'] = str(e)
    for model in ('eleven_v4', 'eleven_v3', 'eleven_multilingual_v2'):
        body = {'text': FA_TEXT, 'model_id': model,
                'voice_settings': {'stability': 0.4, 'similarity_boost': 0.75, 'style': 0.1, 'use_speaker_boost': True, 'speed': 1.2}}
        r = requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{FA_VOICE}', params={'output_format': 'mp3_44100_128'},
                          headers={**hdr, 'accept': 'audio/mpeg'}, json=body, timeout=300)
        if r.ok:
            (d / 'fa_test.mp3').write_bytes(r.content); info['model'] = model; break
        info.setdefault('errors', {})[model] = r.text[:300]
    (d / 'fa_test.json').write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(json.dumps(info, ensure_ascii=False))

def main():
    if os.environ.get('MODE') == 'fa':
        return fa_voice()
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
