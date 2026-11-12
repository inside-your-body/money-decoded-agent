"""Thumbnail test (owner Nov 12): ChatGPT makes the whole thumbnail with its own Persian typography; all tries -> samples/thumb_test/."""
import os, pathlib, shutil
from .common import ROOT
from . import tl


def main():
    out = ROOT / 'samples/thumb_test'; shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    title = os.environ.get('T_TITLE') or 'سقوط لیمن برادرز؛ ۶۳۹ میلیارد دلار و صفر پول نقد'
    text = os.environ.get('T_TEXT') or 'بانکی که یک شبه مُرد'
    summ = os.environ.get('T_ABOUT') or ('The 2008 collapse of Lehman Brothers, the 158-year-old Wall Street investment bank: huge bets on US home '
                                         'mortgages, hidden debt, the weekend nobody saved it, employees leaving its New York headquarters with '
                                         'cardboard boxes, the biggest bankruptcy in history (639 billion dollars) and the global crash that followed.')
    ok = tl._ai_thumb(title, summ, text, out, out / 'thumbnail.jpg')
    for f in out.glob('*.png'): f.unlink()
    print('correct thumbnail:', ok)


if __name__ == '__main__':
    main()
