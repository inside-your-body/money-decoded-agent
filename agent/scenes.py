"""SCENE PICTURES for the Persian channel (owner, Nov 12 2026: "the viewer must SEE who and what we are talking about -> make pictures
with the image tool and bring them in with motion graphics").
Every ~6-10 s of narration gets ONE picture made by the OpenAI image model (cinematic editorial illustration: the real company building,
the trading floor, the people of that time, the place, the object), shown full-screen with a slow camera move; the next sentences keep
the picture in the background (darkened) with the flat motion graphic + Persian typography on top. A new graphic every ~4 s stays."""
import json, pathlib, concurrent.futures as cf
from . import llm, images

FPS = 30
SFX = ['bong', 'boom', 'bubble', 'click', 'drip', 'heartbeat', 'impact1', 'impact2', 'impact3', 'pop1', 'pop2', 'pop3', 'pop4', 'reveal', 'riser', 'shield', 'sparkle', 'tick', 'whoosh1', 'whoosh2', 'whoosh3']
STYLE = ("Cinematic semi-realistic editorial illustration (high-end documentary / news-magazine look), dramatic film lighting, rich colour, "
         "shallow depth of field, one clear focal point, uncluttered, readable on a small phone screen. "
         "No captions, no subtitles, no invented writing; the ONLY readable text allowed is the real name or logo of the company/place the "
         "scene is about (e.g. the real sign on its headquarters), when that makes the subject instantly recognisable.")
LAYOUT = {False: "Wide 16:9 composition, the main subject in the centre-right; keep the bottom quarter calm (Persian subtitles go there).",
          True: "Tall 9:16 composition, the main subject in the middle; keep the top third calm (Persian text goes there)."}


def _groups(beats, lo, hi):
    """Consecutive beats -> picture groups of about lo..hi seconds."""
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
    """One Claude call: for every group of sentences, the picture that shows WHO / WHAT / WHERE the narration is about."""
    r = llm.ask_json(f"""You are the picture director of a Persian YouTube documentary about money and financial history.
Video: {context}
For every scene below (Persian narration) write ONE English image prompt for the picture shown while it is spoken. The viewer must
understand at a glance WHO or WHAT we are talking about: show the real company (its real headquarters building with its real name sign,
its trading floor, its employees), the real place (Wall Street, the New York Stock Exchange, a city, a country's streets), the era
(1990s / 2008 clothes, cars, computers), the real objects (stacks of mortgage papers, a foreclosed house with a sign, bank vault, gold bars,
banknotes of that country, a crashing stock-ticker screen), crowds, queues at a bank, a press conference, an empty office after the fall.
Real famous people (a CEO, a central-bank chief, a minister) may be shown as a recognisable documentary-style portrait in their real
setting, never in a humiliating, criminal or invented situation. Concrete and visual: say the subject, the action, the setting,
the time of day and the camera shot (wide establishing shot / close-up / over-the-shoulder / aerial). Vary the shots; never two
similar pictures in a row. Never charts, infographics or text panels (our motion graphics do that).
Also pick the sound effect that fits the moment ("sfx", one of: {', '.join(SFX)}) or null.
Scenes: {json.dumps({i: t for i, t in enumerate(texts)}, ensure_ascii=False)}
Return JSON: {{"scenes": [{{"i": int, "picture": str, "sfx": str|null}}]}} — one per scene, same order.""", max_tokens=12000)
    out = {s.get('i'): s for s in r.get('scenes', []) if isinstance(s, dict)}
    pics = [(out.get(i) or {}).get('picture') or f"A documentary scene that shows: {context}" for i in range(len(texts))]
    sfx = [(out.get(i) or {}).get('sfx') if (out.get(i) or {}).get('sfx') in SFX else None for i in range(len(texts))]
    return pics, sfx


def attach(props, ep_dir, kind, context, lo=6.0, hi=10.0):
    """Adds 'img' (picture file) + 'imgAt' (first frame of its group) to every beat."""
    vertical = bool(props.get('vertical'))
    beats = props['beats']
    groups = _groups(beats, 4.0, 7.0) if vertical else _groups(beats, lo, hi)
    texts = [' '.join(beats[k].get('text', '') for k in g) for g in groups]
    pics, sfx = _prompts(texts, context)
    out = pathlib.Path(ep_dir) / 'broll'; out.mkdir(exist_ok=True)

    def one(n):
        dst = out / f'{kind}_pic_{n:03d}.jpg'
        if dst.exists(): return n, dst
        png = out / f'{kind}_pic_{n:03d}.png'
        p = f"{pics[n]}\n{LAYOUT[vertical]}\nStyle: {STYLE}"
        if images.gen(p, png, size='1024x1536' if vertical else '1536x1024', quality='medium'):
            from PIL import Image
            Image.open(png).convert('RGB').save(dst, quality=88); png.unlink(missing_ok=True)
            return n, dst
        return n, None

    with cf.ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(one, range(len(groups))))
    ok, last = 0, None
    for n, g in enumerate(groups):
        img = res.get(n) or last            # a failed picture keeps the previous one on screen
        if res.get(n): ok += 1
        for k in g:
            if img:
                beats[k]['img'] = 'ep/broll/' + pathlib.Path(img).name
                beats[k]['imgAt'] = beats[g[0]]['start'] if res.get(n) else beats[k].get('imgAt', beats[g[0]]['start'])
        if sfx[n] and not beats[g[0]].get('sfx'): beats[g[0]]['sfx'] = sfx[n]
        last = img or last
    print(f'scene pictures {kind}: {ok}/{len(groups)} pictures for {len(beats)} beats')
    return props
