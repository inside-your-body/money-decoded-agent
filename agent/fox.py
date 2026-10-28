"""FINN format (owner Oct 28 2026): the channel's mascot, Finn the clever fox (storybook style "B"), acts out the story in
hand-drawn scenes on cream paper; next to him the motion graphic / typography of the current sentence is shown in a card
(long: right third, Short: top). A new drawing every ~7-11 s, the graphic changes with every sentence.
Scenes are drawn by the OpenAI image API FROM the character sheet so Finn always looks the same."""
import json, shutil, pathlib, concurrent.futures as cf
from .common import ROOT, CFG
from . import llm, images

FPS = 30
SHEET = ROOT / 'assets/finn_sheet.jpg'
FINN = ("FINN, an original cartoon red fox: orange-red fur, white chest and white tail tip, mint-green vest, small round glasses, "
        "small gold coin pendant on a cord. Keep him EXACTLY like the reference character sheet (same colours, outfit, proportions).")
STYLE = ("Warm hand-drawn storybook illustration with soft ink lines and light watercolour shading on cream paper texture "
         "(background colour #F6EEDC), simple uncluttered scene, a few props only. No text, no letters, no numbers, no logos, no real people.")
LAYOUT = {False: "Composition: Finn and the scene stay in the LEFT 60% of the frame; the RIGHT 40% is EMPTY plain cream paper (graphics are added there later).",
          True: "Composition: Finn and the scene stay in the BOTTOM 58% of the frame; the TOP 42% is EMPTY plain cream paper (graphics are added there later)."}


def _ref():
    """images/edits wants PNG files -> cached PNG copy of the sheet."""
    png = ROOT / 'work/finn_sheet.png'
    if not png.exists():
        from PIL import Image
        png.parent.mkdir(parents=True, exist_ok=True); Image.open(SHEET).convert('RGB').save(png)
    return str(png)


def _groups(beats, lo=7.0, hi=11.5):
    """Consecutive beats -> scene groups of about lo..hi seconds (one drawing each)."""
    groups, cur, t = [], [], 0.0
    for k, b in enumerate(beats):
        d = (b['end'] - b['start']) / FPS
        if cur and t + d > hi and t >= lo * 0.6:
            groups.append(cur); cur, t = [], 0.0
        cur.append(k); t += d
        if t >= lo:
            groups.append(cur); cur, t = [], 0.0
    if cur:
        if groups and t < lo * 0.5: groups[-1] += cur
        else: groups.append(cur)
    return groups


def _prompts(texts, context):
    """One Claude call: for every scene group, what Finn does in the drawing."""
    r = llm.ask_json(f"""You direct the drawings of "Money Decoded", a finance explainer whose mascot is Finn, a clever red fox.
Video: {context}
For every scene below (a few narration sentences) describe ONE storybook drawing that shows what the narration says, acted out by Finn:
a concrete everyday situation with a clear emotion (curious, shocked, worried, proud, sneaky, laughing, thinking…), 1-4 simple props
(a bank building, a loan contract, coins, a laptop with a banking app, a house, a piggy bank, a chart on paper, a vault, a crowd queue…),
and a fresh pose every time (never the same pose twice in a row, not always pointing). Other characters may appear as simple generic
cartoon people or animals in the same style (never real or famous people). No text, signs, numbers or logos in the drawing.
One or two sentences per scene, concrete and drawable.
Scenes: {json.dumps({i: t for i, t in enumerate(texts)}, ensure_ascii=False)}
Return JSON: {{"scenes": [{{"i": int, "draw": str}}]}} — one per scene, same order.""", max_tokens=8000)
    out = {s.get('i'): s.get('draw') for s in r.get('scenes', []) if isinstance(s, dict)}
    return [out.get(i) or f"Finn the fox thinking about money while this happens: {t[:200]}" for i, t in enumerate(texts)]


def attach(props, ep_dir, kind, context):
    """Adds 'img': 'ep/broll/<kind>_scene_NN.jpg' (+ 'imgAt' = first frame of its scene) to every beat."""
    vertical = bool(props.get('vertical'))
    beats = props['beats']
    groups = _groups(beats)
    texts = [' '.join(beats[k].get('text', '') for k in g) for g in groups]
    draws = _prompts(texts, context)
    out = pathlib.Path(ep_dir) / 'broll'; out.mkdir(exist_ok=True)
    ref = _ref()

    def one(n):
        dst = out / f'{kind}_scene_{n:03d}.jpg'
        if dst.exists(): return n, dst
        png = out / f'{kind}_scene_{n:03d}.png'
        p = f"{FINN} Scene: {draws[n]} {LAYOUT[vertical]} Style: {STYLE}"
        if images.edit(p, [ref], str(png), size='1024x1536' if vertical else '1536x1024', quality='medium'):
            from PIL import Image
            Image.open(png).convert('RGB').save(dst, quality=88); png.unlink(missing_ok=True)
            return n, dst
        return n, None

    with cf.ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(one, range(len(groups))))
    ok = 0
    last = None
    for n, g in enumerate(groups):
        img = res.get(n) or last            # a failed drawing keeps the previous one on screen
        if res.get(n): ok += 1
        for k in g:
            if img: beats[k]['img'] = 'ep/broll/' + pathlib.Path(img).name; beats[k]['imgAt'] = beats[g[0]]['start']
        last = img or last
    print(f'finn {kind}: {ok}/{len(groups)} drawings for {len(beats)} beats')
    return props
