"""Design the channel mascot (owner Oct 28): "Finn", a clever fox who explains money. Three design directions, each with a
character sheet and two test scenes made FROM the sheet (to check that the look stays the same) -> samples/mascot/."""
import shutil
from .common import ROOT
from . import images

BASE = ("Original cartoon mascot for a finance YouTube channel: FINN, a clever, likeable young red fox who explains money. "
        "Signature look that never changes: orange-red fur with a white chest and white tail tip, a mint-green vest (#2EE6A6), small round "
        "glasses, and a small gold coin pendant on a cord around his neck. Expressive face, big readable emotions. Completely original design "
        "(not resembling any existing cartoon character or brand mascot).")
STYLES = {
    'A_clean_lineart': "Clean modern 2D cartoon with bold dark outlines and flat colours, like a premium YouTube explainer; plain white background.",
    'B_storybook': "Warm hand-drawn storybook illustration with soft ink lines and light watercolour shading on cream paper texture.",
    'C_bold_3dlike': "Bold, glossy semi-3D cartoon style (soft shading, rim light) like a modern animated film, plain white background.",
}
SHEET = (" Character model sheet on plain white: the same fox shown 4 times side by side — standing front view, pointing and explaining "
         "(happy), shocked with wide eyes, and worried scratching his head. Full body each time, consistent proportions. No text, no letters.")
SCENES = [
    ('scene_bank', "Finn the fox stands next to a big classic bank building and points at it, raising an eyebrow, curious. Simple clean background."),
    ('scene_coins', "Finn the fox looks shocked as a pile of gold coins on a desk vanishes into thin air with little sparkles. Simple clean background."),
]


def main():
    out = ROOT / 'samples/mascot'
    shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    for key, style in STYLES.items():
        sheet = out / f'{key}_sheet.png'
        if not images.gen(BASE + ' Style: ' + style + SHEET, sheet, size='1536x1024', quality='high'):
            print('sheet failed', key); continue
        for name, sc in SCENES:
            images.edit(f"{sc} Keep Finn EXACTLY like the reference character sheet (same fur colours, mint vest, round glasses, gold coin pendant, "
                        f"same proportions). Style: {style} 2D animation still, no text, no letters.", [str(sheet)], out / f'{key}_{name}.png',
                        size='1536x1024', quality='medium')
        print('done', key)
    # small jpg copies for quick viewing
    from PIL import Image
    for p in out.glob('*.png'):
        Image.open(p).convert('RGB').save(p.with_suffix('.jpg'), quality=85); p.unlink()


if __name__ == '__main__':
    main()
