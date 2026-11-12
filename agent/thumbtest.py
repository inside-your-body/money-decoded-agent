"""Thumbnail test (owner Nov 12): ChatGPT makes the whole thumbnail with its own Persian typography; all tries -> samples/thumb_test/."""
import os, pathlib, shutil
from .common import ROOT
from . import tl


def main():
    out = ROOT / 'samples/thumb_test'; shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    title = os.environ.get('T_TITLE') or 'چرا تورم هیچ‌وقت پایین نمیاد؟'
    text = os.environ.get('T_TEXT') or ''
    summ = os.environ.get('T_ABOUT') or ('Why prices only go up and never come back down: inflation explained simply for ordinary people - '
                                         'the same shopping basket costs more every year, money printing, wages that lag behind, savings losing value.')
    texts = [text] if os.environ.get('T_TEXT') else []
    if not texts:          # owner (Nov 12): more curious headlines -> Claude proposes them with the channel's thumbnail rule
        from . import llm
        r = llm.ask_json(f"""YouTube video (Persian channel): {title}. About: {summ}
Write 3 thumbnail headlines following this rule: {tl.THUMB_RULE}
Return JSON: {{"headlines": [str]}}""", max_tokens=800)
        texts = [h for h in r.get('headlines', []) if isinstance(h, str)][:2] or ['پول‌ها کجا رفت؟']
    (out / 'headlines.txt').write_text('\n'.join(texts))
    for n, t in enumerate(texts):
        d = out / f'v{n + 1}'; d.mkdir()
        ok = tl._ai_thumb(title, summ, t, d, out / f'thumbnail_{n + 1}.jpg')
        okv = tl._ai_thumb(title, summ, t, d, out / f'short_cover_{n + 1}.jpg', vertical=True)     # owner (Nov 12): Short cover
        print('short cover ok:', okv)
        for f in d.glob('*.png'): f.unlink()
        print('headline', t, '-> correct thumbnail:', ok)


if __name__ == '__main__':
    main()
