"""TIMELINE format for Money Decoded (owner approved Oct 24 2026): a money story told on a timeline of time stamps.
Code-drawn only (hologram MONEY MAP + one widget per sentence), so the video itself costs only LLM + voice. One AI image per thumbnail.
build stage: script -> storyboard -> voice (long + 1 Short) -> render props -> thumbnail.   finish: mix audio, QA, package, upload."""
import json, re, shutil, datetime as dt
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from .common import ROOT, WORK, CFG, load, save, sh
from . import llm, tts

FPS = 30
N_SHORTS = 1          # owner (Oct 24): one Short per day, 30 min after the long video
ICONS = ['coin', 'cash', 'bank', 'chartup', 'chartdown', 'house', 'card', 'wallet', 'piggy', 'gold', 'vault', 'briefcase', 'factory',
         'capitol', 'phone', 'clock', 'calendar', 'percent', 'scale', 'warning', 'check', 'cross', 'person', 'people', 'barrel', 'flower',
         'ship', 'laptop', 'crypto', 'rocket', 'fire', 'lock', 'receipt', 'gavel', 'globe', 'printer', 'cart', 'car', 'cap', 'ticket', 'bomb',
         'bubble', 'handshake', 'key', 'dice', 'mask', 'chain', 'bread', 'egg', 'oil']
ALIAS = {'money': 'cash', 'dollar': 'cash', 'bill': 'cash', 'banknote': 'cash', 'cash': 'cash', 'coins': 'coin', 'stock': 'chartup',
         'stocks': 'chartup', 'market': 'chartup', 'crash': 'chartdown', 'loss': 'chartdown', 'home': 'house', 'mortgage': 'house',
         'credit card': 'card', 'debt': 'card', 'loan': 'card', 'savings': 'piggy', 'save': 'piggy', 'safe': 'vault', 'business': 'briefcase',
         'company': 'factory', 'job': 'briefcase', 'salary': 'briefcase', 'government': 'capitol', 'tax': 'receipt', 'taxes': 'receipt',
         'interest': 'percent', 'rate': 'percent', 'law': 'gavel', 'court': 'gavel', 'police': 'gavel', 'world': 'globe', 'country': 'globe',
         'print': 'printer', 'shopping': 'cart', 'prices': 'cart', 'student': 'cap', 'lottery': 'ticket', 'risk': 'dice', 'gamble': 'dice',
         'scam': 'mask', 'fraud': 'mask', 'bitcoin': 'crypto', 'time': 'clock', 'year': 'calendar', 'tulip': 'flower', 'trade': 'ship',
         'computer': 'laptop', 'deal': 'handshake', 'secret': 'key', 'password': 'lock', 'food': 'bread', 'gas': 'oil', 'petrol': 'oil'}
# the signature MONEY MAP: these nodes are always on screen; the one the sentence is about lights up and money flows into it
NODES = ['you', 'bank', 'market', 'central_bank', 'government', 'company', 'home', 'debt', 'gold', 'none']
VISUALS = """Visual widgets (pick the one that best SHOWS the sentence; vary them — never the same type 3 times in a row):
- {"type":"stat","value":number,"prefix":"$|","unit":"%|B|M|T|x|...","label":"what the number is (≤30 chars)","good":true|false}   big counting number
- {"type":"chart","shape":"rise|fall|crash|bubble|recover|zigzag|flat","label":str}          a price/value line that draws itself
- {"type":"growth","years":number,"label":str}                                              a compound-growth curve bending upward over N years
- {"type":"flow","from":"≤14 chars","to":"≤14 chars","label":"amount or what moves (≤24 chars)"}   money visibly travelling from A to B
- {"type":"compare","a":{"label":str,"value":number},"b":{"label":str,"value":number},"unit":str}   two bars (a = the old/bad, b = the new)
- {"type":"meter","label":str,"from":0-1,"to":0-1,"good":true|false}                       a level rising/falling (good=teal, bad=red)
- {"type":"stack","from":0-1,"to":0-1,"label":str}                                          a pile of coins growing or shrinking
- {"type":"wave","label":str,"calm":true|false}                                             a market/price signal calming down or going wild
- {"type":"icon","name":ICON,"cross":true|false,"count":1-8,"label":str}                   an object (cross = removed/stopped; count>1 = many)
- {"type":"clock","from":"HH:MM","to":"HH:MM"}                                              time passing in a day (trading hours, bank runs…)
- {"type":"checklist","items":[2-4 items ≤20 chars],"bad":true|false}                      signs / steps / effects
- {"type":"node","name":NODE,"state":"glow|grow|shrink|crack|frozen","label":str}           close-up of one place in the money system
- {"type":"question","text":"≤60 chars"}                                                    a big question on screen (open loops, hooks)
- {"type":"versus","myth":"≤60 chars","fact":"≤60 chars"}                                   myth vs fact
ICON is one of: """ + ', '.join(ICONS) + """
NODE (also for "node" = the place in the money map that lights up for this sentence) is one of: """ + ', '.join(NODES) + """
(you = a person/household/the viewer; bank = commercial banks; market = stock/bond/crypto markets, traders; central_bank = Fed / Bank of England;
government = state, taxes, treasury, regulators, courts; company = businesses, employers; home = housing, rent, property; debt = loans,
credit cards, IOUs; gold = gold, commodities, hard assets, collectibles; none = nothing specific)"""


def _wc(lines): return sum(len(x.split()) for x in lines)
def long_lines(ep): return [ln for sc in ep['scenes'] for ln in sc['lines']]
def long_words(ep): return _wc([ln['text'] for ln in long_lines(ep)])


# ---------------- script ----------------
def write(topic, notes):
    ref = topic.get('ref') or {}
    return llm.ask_json(f"""You are the head writer of the YouTube channel "Money Decoded" (English, adults, US/UK/Canada audience).
FORMAT (every video): a money story told as a TIMELINE — the story moves through time stamps that fit the topic
(e.g. 9:30 AM → NOON → 4 PM → DAY 2 → YEAR 1, or AGE 20 → 30 → 45 → 65, or 1634 → 1636 → FEB 1637) and at each stamp we see
where the money goes and what changes. Visual identity: a glowing hologram MONEY MAP (you, bank, market, central bank, government,
company, home, debt, gold) where the place we talk about lights up and money flows into it, big time stamps, big numbers, simple icons.
Channel rules:
{llm.RULES}

Topic: "{topic['title']}"
{('This topic is our own version of a proven viral idea: ' + (('"' + str(ref.get('title')) + '" (' + str(ref.get('views', '')) + ' views)') if ref.get('title') else str(ref.get('note', ''))) + '. Same curiosity, our timeline format, our own words and facts — never a copy.') if ref else ''}
{('Angle: ' + topic['angle']) if topic.get('angle') else ''}
{('Opening idea (verify every number against the notes; change it if the notes disagree): ' + topic['hook']) if topic.get('hook') else ''}
Research notes (use only facts from here; round numbers; be accurate; never investment advice, predictions or get-rich promises):
{notes}

Write the long video: {llm.WORDS_MIN}–{llm.WORDS_MAX} words of narration in total (≈ 8:30–9:15). Count carefully.
{llm.HOOK_RULES}
{llm.STORY_CRAFT}
{llm.SEO_RULES}
WORDPLAY: hook the viewer with intriguing wording, reversals ("the bank didn't lend your money — it created new money"), concrete
everyday images and tension — never with false hope or exaggeration. Every claim must be true.
STRUCTURE: scene 1 = hook (stage null). Then 5–8 timeline scenes, each = one time stamp ("stage", ≤10 chars, UPPERCASE, e.g. "DAY 3", "1929", "AGE 45"),
in chronological order, 8–16 sentences each, each with its own surprise. Plant an open loop in the hook and pay it off at the last stamp.
Final scene (stage null): the big picture + one question for the comments. Short spoken sentences, one idea each, every sentence SHOWABLE
with a number, a place in the money map, an object, a flow of money or a change. Max 12 numbers in total. Explain — never advise.

Then write {N_SHORTS} SHORT (95–115 words, ≈ 40–50 s — never longer): the single most surprising slice of the timeline, self-contained:
line 1 = a curiosity question or shocking claim that works in the first second; one continuous mini timeline (2–3 stamps);
second-to-last line sends viewers to the full video ("the full story is in the video linked above"); last line loops into the first.

Thumbnail fallback (only used if the main thumbnail fails): 1 variant = "number" (big number/time on the thumbnail, ≤8 chars, e.g. "$65B", "24H", "-90%"),
"words" (2–3 words that name the topic, e.g. "BANK RUN"), "subject" (ONE striking, instantly recognisable object/scene that shows the topic,
described for a photo-real image, e.g. "a heavy steel bank vault door half open with stacks of cash inside, dramatic light").

The upload description must end with the line: Educational content only — not financial advice.
Return JSON (comments are explanations, do not output them):
{{"title": str, "main_keyword": str,
 "scenes": [{{"title": "chapter title 2-5 words", "stage": str|null, "node": NODE, "lines": [str, ...]}}],
 "shorts": [{{"title": str, "lines": [str, ...]}}],
 "upload": {{"main_keyword": str, "title": str, "description": str, "tags": [str], "hashtags": [str], "pinned_comment": str}},
 "thumbnail": {{"variants": [{{"number": str, "words": str, "subject": str}}]}},
 "sources": [{{"title": str, "url": str}}]}}
The description must include a "Chapters" section with the placeholder {{CHAPTERS}}. NODE is one of: {', '.join(NODES)}.""", max_tokens=32000)


def expand(ep, notes, target):
    cur = long_words(ep) if ep['scenes'] and isinstance(ep['scenes'][0]['lines'][0], dict) else _wc([l for s in ep['scenes'] for l in s['lines']])
    plain = [{'title': s['title'], 'stage': s.get('stage'), 'node': s.get('node'), 'lines': [l['text'] if isinstance(l, dict) else l for l in s['lines']]} for s in ep['scenes']]
    out = llm.ask_json(f"""This "Money Decoded" timeline script is too short: {cur} words. Rewrite it to {target}–{target + 80} words.
Keep the hook, the stamps (you may add one stamp), the story and the style; deepen each stamp with a concrete everyday example, where
the money actually goes, and a surprising fact from the notes. Short spoken sentences. Never investment advice.
Notes: {notes[:12000]}
Scenes: {json.dumps(plain, ensure_ascii=False)}
Return ONLY {{"scenes": [{{"title": str, "stage": str|null, "node": str, "lines": [str]}}]}}""", max_tokens=24000)
    if out.get('scenes') and _wc([l for s in out['scenes'] for l in s['lines']]) > cur:
        ep['scenes'] = out['scenes']; ep.pop('boarded', None)
    return ep


def board_lines(lines, context, recent=()):
    """Storyboard: one visual widget + 2-4 key words (+ money-map node) per sentence."""
    try: out = _board_ask(lines, context)
    except Exception as e:
        print('storyboard failed, fallback visuals:', e); out = {}
    got = {b.get('i'): b for b in out.get('beats', []) if isinstance(b, dict)}
    return [got.get(i, {}) for i in range(len(lines))]


def _board_ask(lines, context):
    stage_key = ', "stage": str|null' if 'stage' in context else ''
    return llm.ask_json(f"""You are the editor of a "Money Decoded" documentary video (like How Money Works / Economics Explained):
real stock-footage B-roll mixed with code-drawn motion graphics, kinetic typography and charts. Video: {context}
For EVERY sentence decide what we SEE:
- "broll": a stock-footage search query (2-5 plain English words) for a REAL video clip that literally shows the sentence — concrete,
  filmable, generic, e.g. "bank building facade", "hands counting dollar bills", "stock exchange trading floor", "people queue outside bank",
  "signing mortgage contract", "money printing press", "city skyline at night", "family moving into house", "credit card payment terminal",
  "worried man looking at bills", "gold bars vault". No brand names, logos, real people's names, no text-heavy scenes. Use null when the
  sentence is about a number, a mechanism or a comparison that a graphic shows better.
- "visual": ALWAYS give a code-drawn widget too (it is shown when "broll" is null, and is the fallback if no clip is found).
Mix (very important, viewers leave when the screen is monotonous): about 55-65% of sentences get a broll clip; never more than 3 broll
sentences in a row and never more than 2 graphic sentences in a row; the first sentence (the hook) gets the most striking footage.
Sentences with a key number or a money flow are graphics (stat, chart, growth, compare, flow, stack, node = the money map).
{VISUALS}
Widget rules: the widget must literally show what the sentence says; use the sentence's real numbers; vary the widget types; "icon" at most
1 in 4 graphic sentences; "question" only for real open questions; labels are short (≤30 chars).
"words" = 1-3 punchy key words lifted from the sentence (max 3 items, e.g. ["BANK", "CREATES MONEY"]), never the whole sentence.
Sentences (index: text): {json.dumps({i: (t['text'] if isinstance(t, dict) else t) for i, t in enumerate(lines)}, ensure_ascii=False)}
Return JSON: {{"beats": [{{"i": int, "broll": str|null, "node": NODE, "visual": {{...}}, "words": [str]{stage_key}}}]}} — one per sentence, same order.""", max_tokens=16000)


def _num(x):
    return float(str(x).replace(',', '').replace('$', '').replace('%', '').strip())


def _fix_visual(v, words, node):
    t = (v or {}).get('type')
    if t == 'icon':
        n = str(v.get('name', '')).lower().strip()
        n = n if n in ICONS else ALIAS.get(n) or next((ALIAS[k] for k in ALIAS if k in n), None) or next((k for k in ICONS if k in n), None)
        if n: v['name'] = n; return v
        t = None
    ok = {'stat': ('value', 'label'), 'chart': ('shape',), 'growth': ('years',), 'flow': ('from', 'to'), 'meter': ('label', 'from', 'to'),
          'stack': ('from', 'to'), 'wave': ('label',), 'compare': ('a', 'b'), 'clock': ('from', 'to'), 'checklist': ('items',),
          'node': ('name',), 'question': ('text',), 'versus': ('myth', 'fact')}
    if t in ok and all(k in v for k in ok[t]):
        try:
            if t == 'stat': v['value'] = _num(v['value'])
            if t == 'compare': v['a']['value'] = _num(v['a']['value']); v['b']['value'] = _num(v['b']['value'])
            if t == 'growth': v['years'] = max(1, min(80, int(_num(v['years']))))
            if t in ('meter', 'stack'): v['from'] = max(0, min(1, _num(v['from']))); v['to'] = max(0, min(1, _num(v['to'])))
        except Exception:
            return {'type': 'question', 'text': ' '.join(words)[:60]}
        if t == 'chart' and v.get('shape') not in ('rise', 'fall', 'crash', 'bubble', 'recover', 'zigzag', 'flat'): v['shape'] = 'zigzag'
        if t == 'node' and v.get('name') not in NODES: v['name'] = node if node in NODES else 'you'
        return v
    if node and node != 'none':
        return {'type': 'node', 'name': node, 'state': 'glow', 'label': ' '.join(words)[:30]}
    return {'type': 'question', 'text': ' '.join(words)[:60]}


def _node(x, fallback='none'):
    x = str(x or '').lower().replace(' ', '_')
    x = {'fed': 'central_bank', 'federal_reserve': 'central_bank', 'state': 'government', 'business': 'company', 'housing': 'home',
         'loan': 'debt', 'loans': 'debt', 'stocks': 'market', 'stock_market': 'market', 'commodities': 'gold', 'person': 'you'}.get(x, x)
    return x if x in NODES else fallback


def _line(text, b, fallback_node='none', stage=False):
    nd = _node(b.get('node'), fallback_node)
    words = [w for w in (b.get('words') or []) if isinstance(w, str)][:4] or text.split()[:3]
    q = b.get('broll'); q = q.strip()[:60] if isinstance(q, str) and q.strip() and q.strip().lower() not in ('null', 'none') else None
    out = {'text': text, 'node': nd, 'words': words, 'visual': _fix_visual(b.get('visual'), words, nd), 'broll': q}
    if stage: out['stage'] = b.get('stage') or None
    return out


SHORT_CTX = "vertical Short. Also give each sentence a 'stage': the time stamp it is about (≤10 chars UPPERCASE, e.g. 'DAY 3'; keep it the same for consecutive sentences about that moment; null only for the hook line)"


def storyboard(ep):
    ctx = ep['title']
    for sc in ep['scenes']:
        lines = sc['lines']
        bs = board_lines(lines, f"{ctx} — scene '{sc['title']}' (stage {sc.get('stage') or 'none'}, main place {sc.get('node')})")
        sc['lines'] = [_line(t['text'] if isinstance(t, dict) else t, b, _node(sc.get('node'))) for t, b in zip(lines, bs)]
    for k, s in enumerate(ep.get('shorts', [])):
        lines = s['lines']
        bs = board_lines(lines, f"{ctx} — {SHORT_CTX} #{k + 1} '{s['title']}'")
        s['lines'] = [_line(t['text'] if isinstance(t, dict) else t, b, stage=True) for t, b in zip(lines, bs)]
    ep['boarded'] = True
    return ep


# ---------------- voice + render props ----------------
def _voice(lines, groups, wav, segs_p):
    if not wav.exists() or not segs_p.exists():
        segs = tts.synth_lines(lines, wav, groups=groups); save(segs_p, segs)
    return load(segs_p)


def props(lines, stages, segs, vertical):
    marks = list(dict.fromkeys([s for s in stages if s]))[:8]
    beats = []
    for k, (ln, st, sg) in enumerate(zip(lines, stages, segs)):
        a = int(round(sg['start'] * FPS)) if k else 0
        beats.append({'start': a, 'stage': st, 'stageIdx': marks.index(st) if st in marks else -1, 'node': ln['node'],
                      'visual': ln['visual'], 'words': ln['words'], 'q': ln.get('broll')})
    total = int(round((segs[-1]['end'] + 1.5) * FPS))
    for k, b in enumerate(beats): b['end'] = beats[k + 1]['start'] if k + 1 < len(beats) else total
    return {'beats': beats, 'marks': marks, 'frames': total, 'vertical': vertical}


def build(topic, ep_dir, dry_run=False):
    ep = load(ep_dir / 'episode.json')
    notes = (ep_dir / 'research.md').read_text() if (ep_dir / 'research.md').exists() else ''
    if not ep:
        notes = llm.research(topic['title'] + ' — the full story as a timeline: what happened / happens first, next and in the end, where the money moved, with exact dates and numbers')
        (ep_dir / 'research.md').write_text(notes)
        ep = write(topic, notes); ep['format'] = 'tl'; save(ep_dir / 'episode.json', ep)
        for _ in range(2):
            w = _wc([l for s in ep['scenes'] for l in s['lines']])
            if w >= llm.WORDS_MIN - 60: break
            print('script too short:', w, '-> expanding'); ep = expand(ep, notes, llm.WORDS_MIN + 40); save(ep_dir / 'episode.json', ep)
    if not ep.get('boarded'):
        ep = storyboard(ep); save(ep_dir / 'episode.json', ep)
    # voice: long (length guard) + Shorts
    need = CFG['long_video']['min_seconds'] + 3
    for attempt in range(3):
        lines = long_lines(ep)
        segs = _voice([l['text'] for l in lines], [len(s['lines']) for s in ep['scenes']], ep_dir / 'vo_long.wav', ep_dir / 'segs_long.json')
        print(f"voice long: {segs[-1]['end']:.0f}s (need {need}s), {long_words(ep)} words")
        if segs[-1]['end'] >= need or attempt == 2: break
        ep = expand(ep, notes, int(need * long_words(ep) / segs[-1]['end'] * 1.06)); ep = storyboard(ep); save(ep_dir / 'episode.json', ep)
        for f in ('vo_long.wav', 'segs_long.json'): (ep_dir / f).unlink(missing_ok=True)
    # 'narration' view so package.py chapters work
    for sc in ep['scenes']: sc['narration'] = [l['text'] for l in sc['lines']]
    save(ep_dir / 'episode.json', ep)
    stages = [sc.get('stage') for sc in ep['scenes'] for _ in sc['lines']]
    from . import broll
    save(ep_dir / 'props_long.json', broll.attach(props(long_lines(ep), stages, segs, False), ep_dir, 'long'))
    for k, s in enumerate(ep.get('shorts', [])[:N_SHORTS]):
        for attempt in range(3):
            sg = _voice([l['text'] for l in s['lines']], [len(s['lines'])], ep_dir / f'vo_short{k}.wav', ep_dir / f'segs_short{k}.json')
            print(f'voice short {k}: {sg[-1]["end"]:.0f}s')
            if sg[-1]['end'] <= 57 or attempt == 2: break
            target = int(_wc([l['text'] for l in s['lines']]) * 52 / sg[-1]['end'])
            out = llm.ask_json(f"""Shorten this YouTube Short script to at most {target} words (it must stay under 55 seconds). Keep line 1 (the hook),
the mini timeline, the line that sends viewers to the full video and the loop. Return ONLY {{"lines": [str]}}.
Lines: {json.dumps([l['text'] for l in s['lines']], ensure_ascii=False)}""", max_tokens=3000)
            if out.get('lines'):
                bs = board_lines(out['lines'], f"{ep['title']} — {SHORT_CTX}")
                s['lines'] = [_line(t, b, stage=True) for t, b in zip(out['lines'], bs)]
                save(ep_dir / 'episode.json', ep)
                for f in (f'vo_short{k}.wav', f'segs_short{k}.json'): (ep_dir / f).unlink(missing_ok=True)
        save(ep_dir / f'props_short{k}.json', broll.attach(props(s['lines'], [l.get('stage') for l in s['lines']], sg, True), ep_dir, f'short{k}'))
    if not (ep_dir / 'thumbnail.jpg').exists():
        try: thumbs(ep, ep_dir)
        except Exception as e: print('thumbnail failed:', e)
    return ep


# ---------------- thumbnails ----------------
THUMB_STYLE = """Style (the channel's approved look): dark navy-blue background with a soft teal/mint glow; one big, clear,
photo-real / glossy 3D image of THIS video's subject (money, a bank vault, a stock chart, coins, a bank building, a price tag, a house…)
with dramatic studio lighting and a glowing rim (often a before -> after change with bright orange arrows between the stages);
HUGE bold condensed sans-serif headline at the top in white with the key word in bright yellow, thick black outline/shadow,
perfectly spelled; high contrast, very clean, easy to read on a phone. No real people's faces, no logos or brand names."""


def summary(ep):
    lines = [l['text'] for l in long_lines(ep)]
    return llm.ask(f"""Summarise this YouTube video for the person who designs its thumbnail, in 5-7 sentences: what the video is about,
what the viewer will see happen (the timeline / stages), and the 2-3 most surprising moments. Plain English, no markdown.
Title: {ep.get('upload', {}).get('title') or ep.get('title')}
Narration: {' '.join(lines)[:14000]}""", max_tokens=1200).strip()


def _check_thumb(img, title):
    """Claude vision: is every word spelled correctly, readable, and does it tell the topic?"""
    import base64
    content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': base64.b64encode(img.read_bytes()).decode()}},
               {'type': 'text', 'text': f"""YouTube thumbnail for the video "{title}". Check it strictly. Return JSON only:
{{"text": "the exact words on it", "spelling_ok": bool, "readable": bool, "topic_clear": bool, "problem": str}}
spelling_ok=false for any misspelled, garbled or made-up word or letters; readable=false if text is cut off, too small or covered;
topic_clear=false if a viewer could not tell what the video is about."""}]
    try:
        r = llm._repair(llm.ask(content, max_tokens=800, retries=2)) or {}
        return r
    except Exception as e:
        print('thumb check failed', e); return {}


def _to_16x9(src, dst):
    """3:2 image -> 1280x720 without cropping anything: fitted to the height; the side bars take the colour of the image's own
    edges (dark navy background) and the seam is feathered, so nothing of the headline is ever cut."""
    from PIL import Image
    im = Image.open(src).convert('RGB')
    w = round(im.width * 720 / im.height); fg = im.resize((w, 720), Image.LANCZOS)
    x0 = (1280 - w) // 2
    a = np.asarray(fg).astype(np.float32)
    border = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    dark = border[border.sum(1) < np.percentile(border.sum(1), 50)]          # the background, not the objects touching the edge
    bg = np.zeros((720, 1280, 3), np.float32); bg[:] = np.median(dark, axis=0)
    F = 60; m = np.ones(w, np.float32); m[:F] = np.linspace(0, 1, F); m[-F:] = np.linspace(1, 0, F)
    bg[:, x0:x0 + w] = bg[:, x0:x0 + w] * (1 - m[None, :, None]) + a * m[None, :, None]
    Image.fromarray(bg.clip(0, 255).astype(np.uint8)).save(dst, quality=92)


def thumbs(ep, ep_dir):
    """Owner (Oct 25): ONE thumbnail made by ChatGPT (image API) from a summary of the video: the text on it must tell what the video
    is about AND make people curious. Vision check for spelling; up to 3 tries; the old code-made design is only the fallback."""
    from . import images
    from PIL import Image
    out = ep_dir / 'thumbs'; out.mkdir(exist_ok=True)
    summ = summary(ep); (out / 'summary.txt').write_text(summ)
    title = ep.get('upload', {}).get('title') or ep.get('title')
    note = ''
    for k in range(3):
        raw = out / f'gpt{k}.png'
        prompt = f"""Design ONE YouTube thumbnail (16:9 landscape) for this video.
Video title: {title}
What the video shows: {summ}

The text on the thumbnail must tell the viewer clearly what the video is about AND make them curious enough to click — not vague,
not too short to understand, not the full title either: one short headline of 3-6 words (it may have one highlighted key word).
Choose the single most striking visual that shows the topic at a glance. {THUMB_STYLE}
Keep it SIMPLE and uncluttered like a top finance explainer channel: one main subject (or a clear 2-3 step change with arrows), no people's faces,
no more than one small number badge besides the headline. Keep a small margin around the headline. Spell every word correctly.{note}"""
        if not images.gen(prompt, raw, size='1536x1024', quality='high'): continue
        jpg = out / f'gpt{k}.jpg'; _to_16x9(raw, jpg)
        r = _check_thumb(jpg, title)
        print('thumb check', k, r)
        if r.get('spelling_ok', True) and r.get('readable', True) and r.get('topic_clear', True):
            shutil.copy(jpg, ep_dir / 'thumbnail.jpg'); return
        note = f"\nA previous attempt had this problem, avoid it: {r.get('problem') or 'misspelled text'}."
    print('ChatGPT thumbnail failed the checks -> code-made fallback')
    v = ((ep.get('thumbnail') or {}).get('variants') or [{}])[0]
    pub = ROOT / 'render/public/ep'; pub.mkdir(parents=True, exist_ok=True)
    img = out / 'subject0.png'
    if v.get('subject') and not img.exists():
        images.gen(f"{v['subject']}. Photo-real, crisp, dramatic cinematic lighting, centred single subject, no text, isolated on a transparent background",
                   img, size='1024x1024', transparent=True, quality='high')
    props = {'number': v.get('number', ''), 'words': v.get('words', title), 'v': 0}
    if img.exists():
        try:
            from . import cutout; cutout.trim(img, img)
        except Exception: pass
        shutil.copy(img, pub / 'tl_subject0.png'); w, h = Image.open(img).size
        props.update(subject='ep/tl_subject0.png', ar=w / h)
    pf = out / 'fallback.json'; save(pf, props)
    sh(['npx', 'remotion', 'still', 'src/index.ts', 'ThumbTL', str(ep_dir / 'thumbnail.jpg'), f'--props={pf}', '--log=warn'], cwd=ROOT / 'render')


# ---------------- audio ----------------
SFX_FOR = {'stat': ['tick', 'pop2'], 'chart': ['whoosh2', 'sparkle'], 'growth': ['riser', 'sparkle'], 'flow': ['whoosh3', 'bubble'],
           'compare': ['whoosh1', 'pop3'], 'meter': ['whoosh2', 'pop1'], 'stack': ['click', 'pop4'], 'wave': ['sparkle', 'whoosh3'],
           'icon': ['pop1', 'pop4', 'pop2'], 'clock': ['tick'], 'checklist': ['click', 'pop3'], 'node': ['reveal', 'shield'],
           'question': ['reveal', 'bong'], 'versus': ['bong', 'impact1']}


def mix(silent, wav, pr, out, track):
    from . import audio
    SR = 48000
    frames = pr['frames']; N = int(frames / FPS * SR)
    vo, vsr = sf.read(wav)
    if vo.ndim > 1: vo = vo.mean(1)
    vo = resample_poly(vo, SR, vsr); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
    mus = audio.library_music(frames / FPS, track)[:N]
    fx = np.zeros(N); last_t, last_n = -9, None
    cache = {}
    def snd(n):
        if n not in cache:
            x, sr = sf.read(ROOT / f'render/public/sfx2/{n}.wav')
            if x.ndim > 1: x = x.mean(1)
            x = resample_poly(x, SR, sr); cache[n] = x / max(1e-6, np.abs(x).max())
        return cache[n]
    prev_stage = None
    for k, b in enumerate(pr['beats']):
        t = b['start'] / FPS
        try:
            if b['stage'] and b['stage'] != prev_stage:
                audio.place(fx, snd('whoosh1' if k % 2 else 'whoosh2'), max(0, t - 0.15), 0.35)
                audio.place(fx, snd('impact2' if k % 3 else 'impact3'), t + 0.1, 0.3); last_t = t
            elif t - last_t >= (2.5 if pr.get('vertical') else 4.5):
                opts = [n for n in SFX_FOR.get(b['visual'].get('type'), ['pop1']) if n != last_n] or ['pop1']
                n = opts[k % len(opts)]
                audio.place(fx, snd(n), t + 0.08, 0.22 if n in ('tick', 'click', 'pop1', 'pop2', 'pop3', 'pop4') else 0.28)
                last_t, last_n = t, n
        except Exception as e: print('sfx', e)
        prev_stage = b['stage']
    env = np.convolve(np.abs(v), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
    m = v + mus * 0.13 * (1 - 0.55 * np.clip(env / 0.04, 0, 1)) + fx * 0.5
    m /= np.abs(m).max() / 0.95
    tmp = out.with_suffix('.wav'); sf.write(tmp, np.stack([m, m], 1).astype(np.float32), SR)
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(silent), '-i', str(tmp), '-map', '0:v', '-map', '1:a', '-af', f"loudnorm=I={CFG['audio']['target_lufs']}:TP=-1.5",
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', str(out)])
    return out


def render_local(ep_dir, kind):
    """Fallback when shard jobs did not render a part (single-runner mode)."""
    comp = 'TLLong' if kind == 'long' else 'TLShort'
    out = ep_dir / f'silent_{kind}.mp4'
    if not out.exists():
        from . import broll; broll.stage(ep_dir)
        sh(['npx', 'remotion', 'render', 'src/index.ts', comp, str(out), f'--props={ep_dir / f"props_{kind}.json"}', '--muted', '--log=warn'], cwd=ROOT / 'render')
    return out


def finish(ep, ep_dir):
    from . import audio, qa
    hist = load(ROOT / 'data/history.json')
    track = audio.pick_track(hist.get('used_music', []))
    long_final = mix(render_local(ep_dir, 'long'), ep_dir / 'vo_long.wav', load(ep_dir / 'props_long.json'), ep_dir / 'final_long.mp4', track)
    qa.check(long_final, ep_dir, 'long')
    shorts = []
    for k in range(N_SHORTS):
        if not (ep_dir / f'props_short{k}.json').exists(): continue
        try:
            st = audio.pick_track([track] + hist.get('used_music', []))
            f = mix(render_local(ep_dir, f'short{k}'), ep_dir / f'vo_short{k}.wav', load(ep_dir / f'props_short{k}.json'), ep_dir / f'final_short{k}.mp4', st)
            qa.check(f, ep_dir, 'short'); shorts.append((k, f, st))
        except Exception as e: print('short', k, 'failed:', e)
    return long_final, shorts, track
