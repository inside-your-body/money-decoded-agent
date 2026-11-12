"""One-minute voice test with the owner's FIXED VOICE RULE (Nov 12): ElevenLabs Aran - Parsi, speed 1.0, best format,
ONE computed speed-up (tts.pace). Output -> samples/voice_test/voice_test.mp3 (192k, encoded once) + report.json."""
import json, shutil
import numpy as np, soundfile as sf
from .common import ROOT
from . import tts

TEXT = [
    "پونزدهِ سپتامبرِ دو هزار و هشت، ساعتِ یکِ بامداد.",
    "یکی از بزرگ‌ترین بانک‌های دنیا، رسماً اعلامِ وَرشِکَستگی کرد.",
    "اسمش لیمن برادرز بود. بانکی که صد و پنجاه و هشت سال عُمر کرده بود.",
    "از جنگِ داخلیِ آمریکا جون سالم به در بُرده بود، از بحرانِ بزرگِ هزار و نهصد و بیست و نه هم گذشته بود.",
    "ولی این بار، فقط توی یک آخرِ هفته، همه‌چیز تموم شد.",
    "صبحِ دوشنبه، هزاران کارمند با جعبه‌های مُقَوّایی از ساختمونِ بانک بیرون اومدن.",
    "بعضی‌هاشون حتی نمی‌دونستن دقیقاً چه اتفاقی افتاده.",
    "بدهیِ این بانک به ششصد و سی و نه میلیارد دلار رسیده بود. عددی که از اقتصادِ خیلی از کشورها بزرگ‌تره.",
    "حالا سؤال اینجاست: چطور بانکی به این بزرگی، یک‌شبه از بین رفت؟",
    "و چرا دولتِ آمریکا که چند ماه قبل بانکِ دیگه‌ای رو نجات داده بود، این بار دست روی دست گذاشت؟",
    "جوابش توی یک تصمیمِ ساده‌ست که سال‌ها قبل گرفته شد.",
    "تصمیمی که اولش همه رو پولدار کرد، و آخرش همه‌چیز رو نابود کرد.",
    "تو این ویدیو قدم به قدم می‌ریم جلو تا ببینیم پول‌ها دقیقاً کجا رفت.",
]


def main():
    out = ROOT / 'samples/voice_test'; shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    a, sr = tts._eleven_tts(' '.join(TEXT))
    a = tts._trim(a, sr); a = a / max(1e-6, np.abs(a).max()) * 0.95
    raw = out / 'raw.wav'; sf.write(raw, a, sr)
    words = sum(len(x.split()) for x in TEXT)
    rep = tts.pace(str(raw), str(out / 'voice.wav'), words)
    rep['format_from_elevenlabs'] = tts._FMT.get('ok'); rep['model'] = tts._MODEL.get('ok')
    rep['sample_rate_raw'] = sr
    import subprocess
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(out / 'voice.wav'), '-c:a', 'libmp3lame', '-b:a', '192k', str(out / 'voice_test.mp3')], check=True)
    (out / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    (out / 'text.txt').write_text('\n'.join(TEXT))
    raw.unlink(); (out / 'voice.wav').unlink()
    tts.commit_usage()
    print(rep)


if __name__ == '__main__':
    main()
