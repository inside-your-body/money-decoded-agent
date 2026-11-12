"""TIMELINE format for Money Decoded (owner approved Oct 24 2026): a money story told on a timeline of time stamps.
Code-drawn only (hologram MONEY MAP + one widget per sentence), so the video itself costs only LLM + voice. One AI image per thumbnail.
build stage: script -> storyboard -> voice (long + 1 Short) -> render props -> thumbnail.   finish: mix audio, QA, package, upload."""
import json, re, shutil, pathlib, datetime as dt
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from .common import ROOT, WORK, CFG, load, save, sh
from . import llm, tts

FPS = 30
N_SHORTS = 1          # owner (Nov 2): every other day ONE long video + ONE Short (30 min after it)
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


def _tx(l): return l['text'] if isinstance(l, dict) else l


def _wc(lines): return sum(len(x.split()) for x in lines)
def long_lines(ep): return [ln for sc in ep['scenes'] for ln in sc['lines']]
def long_words(ep): return _wc([ln['text'] for ln in long_lines(ep)])


# ---------------- script ----------------
# Owner (Oct 30): vary the format so the channel never looks mass-produced (YouTube's "inauthentic content" rule). The writer picks
# the format that fits the topic best, never one of the last two used. "stage" = the section label of the format (<=10 chars).
FORMATS = {
    'timeline': "TIMELINE STORY — the story moves through time stamps that fit the topic (۹:۳۰ صبح → ظهر → روز دوم, سن ۲۰ → ۴۵ → ۶۵, ۱۶۳۴ → ۱۶۳۷); "
                "at each stamp we see where the money goes and what changes. stage = the time stamp in Persian ('روز سوم', 'سال ۱۹۲۹', 'سن ۴۵').",
    'countdown': "COUNTDOWN LIST — 5 to 7 surprising points counted down to the most surprising one (#1), each point a mini story with its own "
                 "twist; tease #1 in the hook. stage = 'شماره ۷' … 'شماره ۱'.",
    'myths': "MYTH BUSTING — 4 to 6 beliefs most people hold about the topic, each one shown, then broken with the real mechanism and a number; "
             "the last myth is the one that costs viewers the most. stage = 'باور ۱' … 'باور ۶'.",
    'case': "TRUE CASE STORY — one real, well-documented event or person (a bank collapse, a famous fortune or scam, a bubble) told like a "
            "thriller in acts: the setup, the warning signs, the moment it breaks, the aftermath, the lesson for you. stage = 'پرده ۱' … 'پرده ۵' or a date.",
    'whatif': "WHAT-IF EXPERIMENT — follow one concrete scenario step by step (you put $1,000 here, you skip this, you do this every month) "
              "and show what happens at each step with real numbers, then compare it with the alternative. stage = 'قدم ۱' … or 'ماه ۶', 'سال ۱۰'.",
}


def pick_formats():
    """Formats allowed for this episode = all but the last two used (data/history.json)."""
    used = [e.get('fmt') for e in load(ROOT / 'data/history.json', {'episodes': []}).get('episodes', []) if e.get('fmt')][-2:]
    return {k: v for k, v in FORMATS.items() if k not in used} or FORMATS


def write(topic, notes):
    ref = topic.get('ref') or {}
    fmts = pick_formats()
    return llm.ask_json(f"""You are the head writer of the Persian YouTube channel "پول و قدرت" (Persian-speaking adults in Iran and abroad). Write ALL narration
and every viewer-facing field in natural spoken Persian (Farsi) — sentences a Persian narrator says easily, never translated-sounding.
FORMAT: choose the ONE format below that tells THIS topic best (the channel rotates formats so no two episodes in a row feel the
same) and return its key as "fmt":
{chr(10).join('- ' + k + ': ' + v for k, v in fmts.items())}
Visual identity: flat 2D motion graphics with professional Persian kinetic typography — every sentence shows 1-4 key words rising
on screen plus one flat graphic (a number, a chart, money flowing, icons, myth-vs-fact cards); each section has its own colour.
Channel rules:
{llm.RULES}

Topic: "{topic['title']}"
{('This topic is our own Persian version of a proven viral idea: ' + (('"' + str(ref.get('title')) + '" (' + str(ref.get('views', '')) + ' views)') if ref.get('title') else str(ref.get('note', ''))) + '. Same curiosity, our own format, our own words and facts — never a copy.') if ref else ''}
{('Angle: ' + topic['angle']) if topic.get('angle') else ''}
{('Opening idea (verify every number against the notes; change it if the notes disagree): ' + topic['hook']) if topic.get('hook') else ''}
Research notes (use only facts from here; round numbers; be accurate; never investment advice, predictions or get-rich promises):
{notes}

Write the long video: {llm.WORDS_MIN}–{llm.WORDS_MAX} words of narration in total (≈ 8–9 minutes). Count carefully.
Address the viewer as «تو» (friendly, warm spoken Persian). Keep sentences short (about 8–14 words ≈ 4–5 seconds each): the picture changes with every sentence.
On-screen text (stage labels, titles) never contains English words or Latin letters; write foreign names in Persian letters.
{llm.HOOK_RULES}
{llm.STORY_CRAFT}
{llm.SEO_RULES}
WORDPLAY: hook the viewer with intriguing wording, reversals ("the bank didn't lend your money — it created new money"), concrete
everyday images and tension — never with false hope or exaggeration. Every claim must be true.
STRUCTURE: scene 1 = hook (stage null). Then 5–8 scenes in the chosen format, each with its "stage" label (≤14 chars, Persian, as the
format says), 8–16 sentences each, each with its own surprise. Plant an open loop in the hook and pay it off in the last section.
Final scene (stage null): the big picture + one question for the comments. Short spoken sentences, one idea each, every sentence SHOWABLE
with a number, a place in the money map, an object, a flow of money or a change. Max 12 numbers in total. Explain — never advise.

Then write {N_SHORTS} SHORTS (each 88–105 words, ≈ 30–36 s at about 3 words per second — never longer), each a DIFFERENT self-contained moment of the video
(different fact, different twist — never the same point twice), each survives without the long video:
line 1 = a curiosity question or shocking claim that works in the first second; one continuous mini story with a turn in it;
second-to-last line sends viewers to the full video ("داستان کامل رو توی ویدیوی بالا گذاشتم"); last line loops into the first.

Thumbnail fallback (only used if the main thumbnail fails): 1 variant = "number" (big number/time on the thumbnail, ≤8 chars, e.g. "$65B", "۲۴ ساعت", "-۹۰٪"),
"words" (2–3 Persian words that name the topic, e.g. "هجوم به بانک"), "subject" (in ENGLISH: ONE striking, instantly recognisable object/scene
that shows the topic, described for a photo-real image, e.g. "a heavy steel bank vault door half open with stacks of cash inside, dramatic light").

The upload description must end with the line: این ویدیو فقط آموزشی است و توصیه‌ی مالی یا سرمایه‌گذاری نیست.
Return JSON (comments are explanations, do not output them):
{{"fmt": str, "title": str, "main_keyword": str,
 "scenes": [{{"title": "chapter title 2-5 words", "stage": str|null, "node": NODE, "lines": [str, ...]}}],
 "shorts": [{{"title": str, "lines": [str, ...]}}],
 "upload": {{"main_keyword": str, "title": str, "description": str, "tags": [str], "hashtags": [str], "pinned_comment": str}},
 "thumbnail": {{"variants": [{{"number": str, "words": str, "subject": str}}]}},
 "sources": [{{"title": str, "url": str}}]}}
The description must include a "فصل‌ها" section with the placeholder {{CHAPTERS}}. NODE is one of: {', '.join(NODES)}.""", max_tokens=32000)


def expand(ep, notes, target):
    cur = long_words(ep) if ep['scenes'] and isinstance(ep['scenes'][0]['lines'][0], dict) else _wc([l for s in ep['scenes'] for l in s['lines']])
    plain = [{'title': s['title'], 'stage': s.get('stage'), 'node': s.get('node'), 'lines': [l['text'] if isinstance(l, dict) else l for l in s['lines']]} for s in ep['scenes']]
    out = llm.ask_json(f"""This Persian "پول و قدرت" script is too short: {cur} words. Rewrite it to {target}–{target + 80} words.
Keep the hook, the stamps (you may add one stamp), the story and the style; deepen each stamp with a concrete everyday example, where
the money actually goes, and a surprising fact from the notes. Short spoken Persian sentences. Never investment advice.
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
    return llm.ask_json(f"""You are the editor of a Persian "پول و قدرت" documentary video (like How Money Works / Economics Explained):
real stock-footage B-roll mixed with code-drawn motion graphics, kinetic typography and charts. Video: {context}
For EVERY sentence decide what we SEE:
- "broll": a stock-footage search query (2-5 plain English words) for a REAL video clip that literally shows the sentence — concrete,
  filmable, generic, e.g. "bank building facade", "hands counting dollar bills", "stock exchange trading floor", "people queue outside bank",
  "signing mortgage contract", "money printing press", "city skyline at night", "family moving into house", "credit card payment terminal",
  "worried man looking at bills", "gold bars vault". No brand names, logos, real people's names, no text-heavy scenes. Use null when the
  sentence is about a number, a mechanism or a comparison that a graphic shows better. The query must name money/finance things
  people can film (bank, cash, coins, card, house, office, trader, screen) — never ambiguous words that stock sites misread
  ("leaves", "fan", "drop", "smoke", "run", "flow"): "money leaves the bank" -> "cash withdrawal at bank counter".
- "visual": ALWAYS give a code-drawn widget too (it is shown when "broll" is null, and is the fallback if no clip is found).
Mix (very important, viewers leave when the screen is monotonous): about 55-65% of sentences get a broll clip; never more than 3 broll
sentences in a row and never more than 2 graphic sentences in a row; the first sentence (the hook) gets the most striking footage.
Sentences with a key number or a money flow are graphics (stat, chart, growth, compare, flow, stack, node = the money map).
{VISUALS}
Widget rules: all labels/texts/items are short PERSIAN text with no English words or Latin letters (numbers go in the numeric fields; currency as the word دلار/تومان in "unit"); the widget must literally show what the sentence says; use the sentence's real numbers; vary the widget types; "icon" at most
1 in 4 graphic sentences; "question" only for real open questions; labels are short (≤30 chars).
"words" = 1-3 punchy Persian key words lifted from the sentence (max 3 items, e.g. ["بانک", "پول می‌سازد"]), never the whole sentence.
Owner's rule: a NEW motion graphic about exactly what the narrator says every ~4 seconds. So for every sentence longer than ~10 words also
give "visual2" + "words2": a second, different widget for the SECOND half of the sentence (what is said there), never a repeat of "visual".
All widget labels/texts/items/myth/fact/from/to are short Persian; "unit" may be a symbol (%, x) or a short Persian word (میلیارد, میلیون);
"prefix" may be "$" for dollars.
Sentences (index: text): {json.dumps({i: (t['text'] if isinstance(t, dict) else t) for i, t in enumerate(lines)}, ensure_ascii=False)}
Return JSON: {{"beats": [{{"i": int, "broll": str|null, "node": NODE, "visual": {{...}}, "words": [str], "visual2": {{...}}|null, "words2": [str]|null{stage_key}}}]}} — one per sentence, same order.""", max_tokens=16000)


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
    w2 = [w for w in (b.get('words2') or []) if isinstance(w, str)][:4]
    if isinstance(b.get('visual2'), dict) and w2: out['visual2'] = _fix_visual(b['visual2'], w2, nd); out['words2'] = w2
    if stage: out['stage'] = b.get('stage') or None
    return out


SHORT_CTX = "vertical Short. Also give each sentence a 'stage': the time stamp it is about (≤14 chars Persian, e.g. 'روز سوم'; keep it the same for consecutive sentences about that moment; null only for the hook line)"


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
def voice_text(ep):
    """Owner (Nov 9): the text sent to ElevenLabs gets diacritics ONLY on words a narrator could misread, and every number/symbol
    written out in Persian words; the on-screen text stays without diacritics."""
    from .fa_text import speakable
    groups = [sc['lines'] for sc in ep['scenes']] + [s['lines'] for s in ep.get('shorts', [])]
    flat = [l for g in groups for l in g if isinstance(l, dict)]
    for k in range(0, len(flat), 60):
        part = flat[k:k + 60]
        r = llm.ask_json(f"""Prepare these Persian narration sentences for a Persian text-to-speech voice.
Owner (Nov 12): correct pronunciation is VERY important - a Persian TTS voice guesses every vowel that is not written.
For each sentence return the SAME words and order, except: (1) add Persian diacritics (اعراب: َ ِ ُ ّ ْ) on EVERY word whose vowels a
narrator could read in more than one way: homographs (کُرد/کَرد، مِلک/مُلک، شِکَر/شُکر), the ezafe kasra between linked words
(بانکِ مرکزی، ارزشِ پول) wherever a reader could miss it, rare or Arabic-origin words, and every foreign name or loanword
(مِدوف، لِمان بِرادِرز، بیت‌کوین stays as is when it is common). Common unambiguous words (است، که، این، پول، بانک) get none; (2) write every number,
year, percent, currency symbol and abbreviation fully in Persian words as it should be spoken (۱۹۸۷ -> هزار و نهصد و هشتاد و هفت،
۶۵٪ -> شصت و پنج درصد، $17B -> هفده میلیارد دلار); (3) foreign names in Persian letters. Do not add or remove anything else.
Sentences: {json.dumps([l['text'] for l in part], ensure_ascii=False)}
Return JSON: {{"say": [str]}} with exactly {len(part)} items.""", max_tokens=12000)
        say = r.get('say') or []
        if len(say) == len(part):
            for l, x in zip(part, say): l['say'] = speakable(str(x))
    for l in flat: l.setdefault('say', speakable(l['text']))
    ep['voiced_text'] = True
    return ep



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
                      'visual': ln['visual'], 'words': ln['words'], 'q': ln.get('broll'), 'text': ln['text']})
    total = int(round((segs[-1]['end'] + 1.5) * FPS))
    for k, b in enumerate(beats): b['end'] = beats[k + 1]['start'] if k + 1 < len(beats) else total
    # owner (Nov 10): a new motion graphic every ~4 s -> a sentence that runs longer than 5.5 s is split in two beats; the second half
    # gets its own visual (visual2/words2 from the storyboard) or, failing that, the next sentence's key words as a big type card.
    out = []
    for k, (b, ln) in enumerate(zip(beats, lines)):
        d = b['end'] - b['start']
        if d > 5.5 * FPS:
            n = 3 if d > 11 * FPS else 2
            step = d // n; v2 = ln.get('visual2'); w2 = ln.get('words2')
            for j in range(n):
                x = dict(b); x['start'] = b['start'] + j * step; x['end'] = b['start'] + (j + 1) * step if j < n - 1 else b['end']
                if j == 1 and v2: x['visual'] = v2; x['words'] = w2
                elif j >= 1:            # no second widget: the key words become a big type card (still a change of picture)
                    x['visual'] = {'type': 'question', 'text': ' '.join(w2 or b['words'])[:60]}; x['words'] = []
                out.append(x)
        else:
            out.append(b)
    beats = out
    # owner (Nov 9): every topic gets its own colour palette (rotates with the episode count, never the same twice in a row)
    pal = len(load(ROOT / 'data/history.json', {'episodes': []}).get('episodes', []))
    return {'beats': beats, 'marks': marks, 'frames': total, 'vertical': vertical, 'palette': pal,
            'brand': CFG['channel'].get('name_fa') or CFG['channel']['name']}


def _visuals(pr, ep_dir, kind, context):
    """Owner (Oct 28): style "finn" = Finn the fox in storybook drawings + the sentence's motion graphic beside him;
    otherwise the older documentary style (stock B-roll + full-screen graphics)."""
    if CFG.get('style') == 'flat':        # owner (Nov 8): Persian channel = flat 2D motion graphics + kinetic type
        pr['flat'] = True
        if CFG.get('scene_pictures', True):   # owner (Nov 12): + AI pictures so the viewer SEES who/what we talk about
            from . import scenes
            try: return scenes.attach(pr, ep_dir, kind, context)
            except Exception as e: print('scene pictures failed -> graphics only', e)
        return pr
    if CFG.get('style') == 'finn':
        from . import fox
        pr['finn'] = True
        try: return fox.attach(pr, ep_dir, kind, context)
        except Exception as e: print('finn drawings failed -> graphics only', e); return pr
    from . import broll
    return broll.attach(pr, ep_dir, kind)


def build(topic, ep_dir, dry_run=False, voice_only=False):
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
    if not ep.get('polished'):            # packaging first: the hook must confirm the final title
        try: ep = polish(ep); save(ep_dir / 'episode.json', ep)
        except Exception as e: print('packaging polish failed (keeping the writer\'s title/description):', e)
    if not ep.get('hooked'):
        try: ep = hook_pass(ep); save(ep_dir / 'episode.json', ep)
        except Exception as e: print('hook pass failed:', e)
    if not ep.get('boarded'):
        ep = storyboard(ep); save(ep_dir / 'episode.json', ep)
    if not ep.get('voiced_text'):
        try: ep = voice_text(ep); save(ep_dir / 'episode.json', ep)
        except Exception as e: print('voice text prep failed (numbers are still spelled out):', e)
    # voice: long (length guard) + Shorts
    need = CFG['long_video']['min_seconds'] + 3
    # owner (Nov 12): ElevenLabs credits are limited -> the text is made long enough BEFORE voicing and every line is voiced once
    paid = CFG['voice'].get('engine') == 'elevenlabs'
    if paid and long_words(ep) < llm.WORDS_MIN - 40 and not (ep_dir / 'vo_long.wav').exists():
        ep = expand(ep, notes, llm.WORDS_MIN + 40); ep = storyboard(ep); ep.pop('voiced_text', None)
        try: ep = voice_text(ep)
        except Exception as e: print('voice text prep failed:', e)
        save(ep_dir / 'episode.json', ep)
    for s_ in ep.get('shorts', [])[:N_SHORTS]:
        if paid and _wc([l['text'] for l in s_['lines']]) > 112 and not (ep_dir / 'vo_short0.wav').exists():
            out = llm.ask_json(f"""Shorten this Persian YouTube Short script to 90-104 words (30-36 seconds). Keep line 1 (the hook), the turn,
the line that sends viewers to the full video and the loop. Return ONLY {{"lines": [str]}}.
Lines: {json.dumps([l['text'] for l in s_['lines']], ensure_ascii=False)}""", max_tokens=3000)
            if out.get('lines'):
                bs = board_lines(out['lines'], f"{ep['title']} — {SHORT_CTX}")
                s_['lines'] = [_line(t, b, stage=True) for t, b in zip(out['lines'], bs)]
                from .fa_text import speakable
                for l in s_['lines']: l['say'] = speakable(l['text'])
                save(ep_dir / 'episode.json', ep)
    for attempt in range(1 if paid else 3):
        lines = long_lines(ep)
        segs = _voice([l.get('say') or l['text'] for l in lines], [len(s['lines']) for s in ep['scenes']], ep_dir / 'vo_long.wav', ep_dir / 'segs_long.json')
        print(f"voice long: {segs[-1]['end']:.0f}s (need {need}s), {long_words(ep)} words")
        if segs[-1]['end'] >= need or attempt == (0 if paid else 2): break   # paid voice: never throw a voiced file away
        ep = expand(ep, notes, int(need * long_words(ep) / segs[-1]['end'] * 1.06)); ep = storyboard(ep); save(ep_dir / 'episode.json', ep)
        for f in ('vo_long.wav', 'segs_long.json'): (ep_dir / f).unlink(missing_ok=True)
    # 'narration' view so package.py chapters work
    for sc in ep['scenes']: sc['narration'] = [l['text'] for l in sc['lines']]
    save(ep_dir / 'episode.json', ep)
    if voice_only:                      # batch voicing (owner Nov 12): script + voices now, pictures/render on the build day
        for k, s_ in enumerate(ep.get('shorts', [])[:N_SHORTS]):
            _voice([l.get('say') or l['text'] for l in s_['lines']], [len(s_['lines'])], ep_dir / f'vo_short{k}.wav', ep_dir / f'segs_short{k}.json')
        return ep
    stages = [sc.get('stage') for sc in ep['scenes'] for _ in sc['lines']]
    from . import broll
    save(ep_dir / 'props_long.json', _visuals(props(long_lines(ep), stages, segs, False), ep_dir, 'long', ep['title']))
    for k, s in enumerate(ep.get('shorts', [])[:N_SHORTS]):
        for attempt in range(1 if paid else 3):
            sg = _voice([l.get('say') or l['text'] for l in s['lines']], [len(s['lines'])], ep_dir / f'vo_short{k}.wav', ep_dir / f'segs_short{k}.json')
            print(f'voice short {k}: {sg[-1]["end"]:.0f}s')
            if sg[-1]['end'] <= 41 or attempt == (0 if paid else 2): break          # owner (Nov 9): Shorts 30-40 s; paid voice is never thrown away
            target = int(_wc([l['text'] for l in s['lines']]) * 37 / sg[-1]['end'])
            out = llm.ask_json(f"""Shorten this Persian YouTube Short script to at most {target} words (it must stay under 40 seconds). Keep line 1 (the hook),
the mini timeline, the line that sends viewers to the full video and the loop. Return ONLY {{"lines": [str]}}.
Lines: {json.dumps([l['text'] for l in s['lines']], ensure_ascii=False)}""", max_tokens=3000)
            if out.get('lines'):
                bs = board_lines(out['lines'], f"{ep['title']} — {SHORT_CTX}")
                s['lines'] = [_line(t, b, stage=True) for t, b in zip(out['lines'], bs)]
                save(ep_dir / 'episode.json', ep)
                for f in (f'vo_short{k}.wav', f'segs_short{k}.json'): (ep_dir / f).unlink(missing_ok=True)
        pr = props(s['lines'], [l.get('stage') for l in s['lines']], sg, True)
        pr['cover'] = s.get('cover') or (s.get('title') or '')[:44]
        save(ep_dir / f'props_short{k}.json', _visuals(pr, ep_dir, f'short{k}', ep['title'] + ' (vertical Short)'))
    if not ep.get('polished'):
        try: ep = polish(ep); save(ep_dir / 'episode.json', ep)
        except Exception as e: print('packaging polish failed (keeping the writer\'s title/description):', e)
    if not (ep_dir / 'thumbnail.jpg').exists():
        try: thumbs(ep, ep_dir)
        except Exception as e: print('thumbnail failed:', e)
    return ep


# ---------------- packaging (title, description, Short caption) ----------------
def polish(ep):
    """Owner (Oct 25): the bot must write a strong title and a real caption. Second pass by a 'packaging editor' who sees the finished
    script: 10 title ideas -> picks the best (search keyword + curiosity, honest), rewrites the description's opening, the Short's title
    and caption, and the pinned comment. Facts may only come from the script."""
    up = ep['upload']
    narr = ' '.join(_tx(l) for l in long_lines(ep))[:14000]
    r = llm.ask_json(f"""You are the packaging editor of the Persian finance YouTube channel "پول و قدرت" (Persian-speaking adults in Iran and abroad).
Everything you write is Persian, phrased the way Persian speakers search and talk on YouTube.
The video is finished. Write its packaging so that people who see it WANT to click — through curiosity, never false hope.
Rules: every claim must be true to the script; no clickbait lies, no "get rich", no advice, no predictions, no ALL-CAPS sentences, max one emoji
in the Short caption and none elsewhere. Use concrete, surprising specifics from the script (a number, a twist, a reversal).

Main search keyword: "{up.get('main_keyword') or ep.get('main_keyword', '')}"
Writer's title: "{up.get('title')}"
Script: {narr}
Shorts: {json.dumps([' '.join(_tx(l) for l in x.get('lines', [])) for x in ep.get('shorts', [])], ensure_ascii=False)}

0. "queries": the 3 search queries (what a real person types) this video should win.
1. "title_ideas": 10 different PACKAGES, each = a title + the thumbnail text, written as ONE unit:
   - title ≤ 60 characters, the subject inside the first 40 (mobile feed), the main keyword (or its most natural wording) near the start,
     a number, a name or a date from the script, a curiosity gap (twist, hidden truth, surprising number) — understandable at a glance;
     max 2 ALL-CAPS words, no hype words (amazing, insane, secret, ultimate, best…).
   - thumb: {THUMB_RULE} Write "thumb" as PART A + " " + PART B, and put PART A (exactly as written) in "key".
2. "title": the best one of them (best mix of searchable + curiosity + honest).
3. "hook": the first 2 lines of the description (≤ 220 characters total): they show under the video in search — keyword in sentence 1,
   then an open question or twist that makes people want to watch. No hashtags.
4. "shorts": for EACH Short above, in order: "title" (≤ 55 characters, no hashtags, a curiosity question or shocking true claim from
   that Short; every Short gets a different title) and "caption" (2-3 short lines: line 1 the curiosity hook, line 2 what they'll
   understand, line 3 a question that invites comments; no hashtags, no links — they are added later) and "cover" (2-5 BIG Persian words
   shown on screen in the first 2 seconds and as the Short's cover frame: tells the topic at a glance AND opens a curiosity gap, different
   words from the spoken first line, e.g. "حقوق یکسان، پس‌انداز صفر؟", "بانک تو گاوصندوق ندارد").
6. "pinned_comment": one friendly question to viewers about the video's idea (≤ 140 characters).
Return JSON: {{"queries": [str], "title_ideas": [{{"title": str, "thumb": str, "key": str}}], "title": str, "hook": str, "shorts": [{{"title": str, "caption": str, "cover": str}}], "pinned_comment": str}}""",
                         max_tokens=4000)
    # yt-package / yt-seo checks: lint every title+thumbnail pairing, reward titles whose words cover the search queries
    from . import craft
    queries = [q for q in r.get('queries', []) if isinstance(q, str)][:3]
    cands = [c for c in r.get('title_ideas', []) if isinstance(c, dict) and c.get('title')]
    pick = (r.get('title') or '').strip()
    rows = []
    for c in cands:
        L = craft.title_lint(c['title'], c.get('thumb'))
        gaps = craft.query_gaps(c['title'], r.get('hook', ''), queries)
        rows.append((L['score'] - 6 * len(gaps) + (8 if c['title'].strip() == pick else 0), c, L))
    if rows:
        sc, c, L = max(rows, key=lambda x: x[0])
        up['title'] = c['title'].strip()[:100]
        th = (c.get('thumb') or '').strip()
        if th and len(th.split()) <= 5: ep['thumb_text'] = th; ep['thumb_key'] = (c.get('key') or '').strip()
        print('packaging lint:', sc, L['issues'])
    elif 10 <= len(pick) <= 70: up['title'] = pick
    ep['queries'] = queries
    if r.get('hook'):
        d = up.get('description', '')
        cut = d.find('\n\n')
        up['description'] = r['hook'].strip() + ('\n\n' + d[cut + 2:] if cut > 0 else '\n\n' + d)
    if r.get('pinned_comment'): up['pinned_comment'] = r['pinned_comment'].strip()
    for x, pk in zip(ep.get('shorts', []), r.get('shorts') or []):
        if isinstance(pk, dict):
            if pk.get('title'): x['title'] = pk['title'].strip()
            if pk.get('caption'): x['caption'] = pk['caption'].strip()
            if pk.get('cover'): x['cover'] = pk['cover'].strip()[:44]
    ep['title_ideas'] = r.get('title_ideas', [])
    ep['polished'] = True
    print('packaging:', up['title'], '|', [x.get('title') for x in ep.get('shorts', [])])
    return ep


def hook_pass(ep):
    """yt-script / yt-shorts: the first ~15 s must confirm the title, open a question the viewer cannot close and prove the payoff.
    5 alternative openings are written against proven hook types, scored with craft.hook_score, and the strongest one replaces the
    first two sentences (only if it beats the current one). Same for line 1 of the Short (it must work without the long video)."""
    from . import craft
    sc0 = ep['scenes'][0]
    cur = ' '.join(_tx(l) for l in sc0['lines'][:2])
    shorts = [x for x in ep.get('shorts', []) if x.get('lines')]
    s_cur = ' | '.join(_tx(x['lines'][0]) for x in shorts)
    r = llm.ask_json(f"""Video title: "{ep['upload']['title']}". Current opening (first two sentences): "{cur}"
Next sentences: "{' '.join(_tx(l) for l in sc0['lines'][2:6])}"
First lines of the Shorts (separated by |): "{s_cur}"
Write 5 alternative Persian openings for the long video (each 1-2 short spoken sentences, 12-30 words) using different hook types: {'; '.join(craft.HOOK_TYPES)}.
Every opening must: confirm what the title promises in the first sentence, open a question the viewer cannot close yet, address the viewer ("تو"/"شما") early,
name what is at stake (a concrete number/cost from the script), and flow naturally into the next sentences. Only facts from the script.
For EACH Short (same order) also write 4 alternative Persian FIRST LINES (one sentence, 9-24 words) that work for someone who never saw the
long video and fit that Short's own topic.
Return JSON: {{"long": [str], "shorts": [[str]]}}""", max_tokens=3000)
    best, sc = craft.best_hook(cur, r.get('long', []))
    print('hook:', craft.hook_score(cur)['verdict'], '->', sc)
    if best != cur:
        parts = [x.strip() for x in re.split(r'(?<=[.?!؟])\s+', best) if x.strip()]
        sc0['lines'] = parts + [_tx(l) for l in sc0['lines'][2:]]
        ep['boarded'] = False
    for x, opts in zip(shorts, r.get('shorts') or []):
        cur1 = _tx(x['lines'][0])
        sb, ss = craft.best_hook(cur1, opts if isinstance(opts, list) else [])
        if sb != cur1:
            x['lines'] = [sb] + [_tx(l) for l in x['lines'][1:]]
            ep['boarded'] = False
        print('short hook ->', ss)
    ep['hooked'] = True
    return ep


# ---------------- thumbnails ----------------
THUMB_STYLE = """Style (the channel's approved look): dark navy-blue background with a soft teal/mint glow; one big, clear,
photo-real / glossy 3D image of THIS video's subject (money, a bank vault, a stock chart, coins, a bank building, a price tag, a house…)
with dramatic studio lighting and a glowing rim (often a before -> after change with bright orange arrows between the stages);
HUGE bold condensed sans-serif headline at the top in white with the key word in bright yellow, thick black outline/shadow,
perfectly spelled; high contrast, very clean, easy to read on a phone. No real people's faces, no logos or brand names."""


# Owner (Oct 31): our two best-performing videos had the DARK look (navy background, glossy objects, a clear before -> after with
# an arrow, huge white/yellow headline on top); the cream cartoon thumbnails got almost no clicks -> dark look + Finn small as the brand.
FINN_THUMB = """Style (the channel's best-performing look): dark navy-blue background with a soft teal/mint glow; ONE big, glossy, almost
photo-real subject that shows the topic at a glance (a laptop with a bank screen, a stack of cash, a bank building, coins, a house, a credit
card…), ideally as a clear before -> after or cause -> effect with ONE bright orange arrow; dramatic studio light and a glowing rim.
HUGE bold condensed sans-serif headline across the top in white with the key word in bright yellow, thick dark outline, perfectly spelled.
Finn the fox (the channel mascot) appears SMALL in a lower corner (about 25% of the height), reacting with a strong emotion, drawn as a
clean cartoon so he pops off the dark background. High contrast, very clean, readable at phone size. No real people's faces, no logos."""


def summary(ep):
    lines = [l['text'] for l in long_lines(ep)]
    return llm.ask(f"""Summarise this YouTube video for the person who designs its thumbnail, in 5-7 sentences: what the video is about,
what the viewer will see happen (the timeline / stages), and the 2-3 most surprising moments. Write this summary in plain ENGLISH
(it goes into an image prompt), no markdown.
Title: {ep.get('upload', {}).get('title') or ep.get('title')}
Narration: {' '.join(lines)[:14000]}""", max_tokens=1200).strip()


def _check_thumb(img, title):
    """Claude vision: is every word spelled correctly, readable, and does it tell the topic?"""
    import base64
    content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': base64.b64encode(img.read_bytes()).decode()}},
               {'type': 'text', 'text': f"""YouTube thumbnail for the video "{title}". Check it strictly. Return JSON only:
{{"text": "the exact words on it", "spelling_ok": bool, "readable": bool, "topic_clear": bool, "problem": str}}
spelling_ok=false for any misspelled, garbled or made-up word or letters; readable=false if text is cut off, too small or covered;
topic_clear=false if a viewer who sees this thumbnail TOGETHER WITH the title above could not tell what the video is about
(the thumbnail text is meant to complement the title, not repeat it)."""}]
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


def _bg_check(img, title):
    """Claude vision: the picture must carry NO text/letters (the Persian headline is typeset by us) and show the topic."""
    import base64
    content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': base64.b64encode(img.read_bytes()).decode()}},
               {'type': 'text', 'text': f"""Background picture for a YouTube thumbnail of the video "{title}" (a Persian headline will be added on the
empty top part later). Return JSON only: {{"has_text": bool, "top_clear": bool, "topic_clear": bool, "problem": str}}
has_text=true if letters, words, numbers or fake writing are visible (the real name sign / logo of the video's subject itself does NOT count);
top_clear=false if important objects fill the top third (where the headline goes); topic_clear=false if the picture does not show the topic."""}]
    try:
        return llm._repair(llm.ask(content, max_tokens=600, retries=2)) or {}
    except Exception as e:
        print('bg check failed', e); return {}


def _typeset(bg_jpg, text, key, dst):
    """Persian headline set by code (Vazirmatn Black, RTL, key word yellow) on top of the text-free picture."""
    pub = ROOT / 'render/public/ep'; pub.mkdir(parents=True, exist_ok=True)
    shutil.copy(bg_jpg, pub / 'thumb_bg.jpg')
    pf = pathlib.Path(dst).with_suffix('.json'); save(pf, {'bg': 'ep/thumb_bg.jpg', 'text': text, 'key_word': key or ''})
    sh(['npx', 'remotion', 'still', 'src/index.ts', 'ThumbFa', str(dst), f'--props={pf}', '--log=warn'], cwd=ROOT / 'render')


# owner (Nov 12): the thumbnail headline must make people CURIOUS (an open question / a mystery), understandable by anyone
THUMB_RULE = """the thumbnail headline in TWO parts (owner Nov 12, approved example: «تورم» + «چرا هیچ‌وقت پایین نمیاد؟»):
     PART A = the TOPIC in 1-2 big words that tell at once what the video is about (e.g. «تورم», «برند زارا», «پس‌انداز», «کازینو»);
     PART B = a short clear question or claim (3-6 words) that says what the viewer will find out and makes them curious
     (e.g. «چرا هیچ‌وقت پایین نمیاد؟», «از همبرگر پول درنمیاره!»). Together they must say clearly what the video is about - never
     vague lines like «آخر هفته‌ای که همه سکوت کردند». Simple everyday Persian, no jargon, no unexplained foreign names."""

# owner (Nov 12): ONE fixed thumbnail template, always the same, clean (not busy), text far from the edges
THUMB_TEMPLATE = """FIXED CHANNEL TEMPLATE (owner Nov 12, from his reference) - every thumbnail of the channel must look like the same series:
- STYLE: clean, simple and elegant editorial poster look. Background = light off-white / cream paper with a subtle grunge paper texture.
- SUBJECT: ONE person or object that shows the topic, as a sharp BLACK-AND-WHITE photo cut-out (no background), in the CENTRE, big,
  from the chest up for a person; a clear readable expression (thoughtful, worried or surprised). Never a real famous person.
  If the topic is a brand, show its most famous product / store recognisably instead of a person.
- ONE light accent element around the subject that tells the topic (e.g. a few flying banknotes, coins, price tags or receipts),
  small and airy - never a busy collage.
- HEADLINE IN TWO PARTS: PART A = huge, ultra-bold, condensed, slightly distressed/grunge BLACK letters standing on the cream background on
  ONE side of the subject; PART B = white bold condensed distressed letters on a solid RED (#E4252B) rectangle box on the OTHER side of the
  subject, slightly overlapping it. Same typeface style and the same layout every time.
- Only 3 colours: cream, black, red (+ the grey tones of the photo and the money).
- SAFE MARGINS: every letter at least 7% of the width away from the left/right edges and 14% of the height away from the top and bottom
  edges (the top and bottom 6% may be cropped). The bottom-right corner stays empty (YouTube shows the video length there).
- No other text at all."""


# owner (Nov 12): a Short has no custom thumbnail -> its FIRST frames show the same template as a vertical cover
VERTICAL_COVER = """
VERTICAL SHORT COVER (9:16): the same template, re-arranged for a phone screen: PART A in huge black letters in the upper part, the subject
in the middle, PART B on the red box just below the subject's face. YouTube draws buttons over a Short, so EVERY letter must stay inside the
safe area: at least 16% of the height away from the top, at least 26% of the height away from the bottom, and at least 10% of the width away
from the left and right edges (the left and right 8% may be cropped). Nothing important in the bottom quarter."""


def _text_check(img, text):
    """Claude vision: is the Persian headline in the AI thumbnail spelled exactly right and readable?"""
    import base64
    content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': base64.b64encode(pathlib.Path(img).read_bytes()).decode()}},
               {'type': 'text', 'text': f"""This YouTube thumbnail must show this Persian headline: «{text}».
Read the Persian text in the picture letter by letter. Return JSON only: {{"read": str, "exact": bool, "readable": bool, "margin_ok": bool, "extra_text": bool, "problem": str}}
exact=true only if every word is spelled exactly right (all letters and dots correct, right-to-left, no missing/extra/garbled letters);
readable=true if it is big and clear on a phone; margin_ok=false if any letter is closer than ~5% of the width/height to an edge
or is cut off; extra_text=true if there is any OTHER text besides the headline and the real name/logo of
the subject (e.g. a company name on its building is fine)."""}]
    try:
        return llm._repair(llm.ask(content, max_tokens=500, retries=2)) or {}
    except Exception as e:
        print('text check failed', e); return {}


def _frame(im):
    """The channel's fixed thumbnail frame (owner Nov 12: always the same template): thin rounded orange line inset from the edges."""
    from PIL import ImageDraw
    im = im.convert('RGB'); d = ImageDraw.Draw(im); w, h = im.size; m = round(w * 0.018)
    d.rounded_rectangle([m, m, w - m - 1, h - m - 1], radius=round(w * 0.022), outline=(251, 133, 0), width=max(4, round(w * 0.006)))
    return im


def _ai_thumb(title, summ, text, out, dst, vertical=False):
    """Owner (Nov 12): ChatGPT designs the WHOLE thumbnail, including the Persian headline in its own viral thumbnail typography
    (no font given by us). Claude checks the spelling; up to 3 tries. Returns True when a correct one was saved to dst."""
    from . import images
    from PIL import Image
    note = ''
    ta, tb = [x.strip() for x in text.split('|', 1)] if '|' in text else (text.split()[0], ' '.join(text.split()[1:]) or text)
    text = f'{ta} {tb}'
    for k in range(3):
        raw = out / (f'vfull{k}.png' if vertical else f'full{k}.png')
        prompt = f"""Design a complete, professional, highly clickable YouTube thumbnail ({'9:16 VERTICAL cover frame of a YouTube Short' if vertical else '16:9'}) for a Persian-language finance documentary.
Video title: {title}
What the video is about: {summ}
1) The viewer must understand at ONE glance what the video is about from the subject + the accent element + the headline.
2) HEADLINE (Persian / Farsi, right-to-left, spelled perfectly letter by letter, Persian digits only):
   PART A (big black letters): «{ta}»
   PART B (white letters on the red box): «{tb}»
Typeset it yourself in the style of the most viral YouTube thumbnails.
{THUMB_TEMPLATE}{VERTICAL_COVER if vertical else ''}{note}"""
        size = '1024x1536' if vertical else '1536x1024'
        style = ROOT / 'assets/thumb_style.jpg'       # the owner-approved thumbnail = the fixed template for every next one
        if style.exists():
            ref = out / 'style_ref.png'; Image.open(style).convert('RGB').save(ref)
            ok = images.edit(prompt + "\nThe reference image is the channel's APPROVED thumbnail template: copy its layout, headline position, "
                             "typeface style, outline, colours and amount of detail exactly - only the subject and the headline text are new "
                             "(never copy the reference's subject or words).", [str(ref)], str(raw), size=size, quality='high')
        else:
            ok = images.gen(prompt, raw, size=size, quality='high')
        if not ok:
            continue
        im = Image.open(raw).convert('RGB')
        if vertical:              # 1024x1536 -> 9:16 (the sides are cropped a little) -> 1080x1920
            w = round(im.height * 9 / 16); x0 = (im.width - w) // 2
            jpg = out / f'vfull{k}.jpg'; im.crop((x0, 0, x0 + w, im.height)).resize((1080, 1920), Image.LANCZOS).save(jpg, quality=92)
        else:
            h = round(im.width * 9 / 16); y0 = (im.height - h) // 2
            jpg = out / f'full{k}.jpg'; im.crop((0, y0, im.width, y0 + h)).resize((1280, 720), Image.LANCZOS).save(jpg, quality=92)   # owner's template has no frame
        r = _text_check(jpg, text); print('ai thumbnail check', k, r)
        if r.get('exact') and r.get('readable', True) and r.get('margin_ok', True) and not r.get('extra_text'):
            shutil.copy(jpg, dst); return True
        note = (f"\nA previous attempt wrote the headline wrongly as «{r.get('read', '')}» ({r.get('problem') or 'misspelled'}). "
                f"Copy every Persian letter of «{text}» exactly.")
    return False


def _typeset_plain(text, key, dst):
    """No usable picture: Persian headline on the dark navy card (no Latin letters/digits ever)."""
    pf = pathlib.Path(dst).with_suffix('.json'); save(pf, {'bg': '', 'text': text, 'key_word': key or ''})
    sh(['npx', 'remotion', 'still', 'src/index.ts', 'ThumbFa', str(dst), f'--props={pf}', '--log=warn'], cwd=ROOT / 'render')


def thumbs(ep, ep_dir):
    _thumbs_main(ep, ep_dir)
    try: short_cover(ep, ep_dir)
    except Exception as e: print('short cover failed', e)


def short_cover(ep, ep_dir):
    """Owner (Nov 12): the Short starts with the video's cover in the approved thumbnail template (vertical, safe margins), so the
    viewer sees what it is about in the first second and YouTube can use it as the Short's cover frame."""
    for k in range(N_SHORTS):
        pf = ep_dir / f'props_short{k}.json'
        if not pf.exists(): continue
        text = (ep.get('thumb_text') or ep.get('title') or '').strip()
        if '|' not in text and ep.get('thumb_key') and ep['thumb_key'] in text:
            rest = ' '.join(text.replace(ep['thumb_key'], ' ').split())
            if rest: text = ep['thumb_key'] + '|' + rest
        out = ep_dir / 'thumbs'; out.mkdir(exist_ok=True)
        (ep_dir / 'broll').mkdir(exist_ok=True)
        dst = ep_dir / 'broll' / f'short{k}_cover.jpg'
        title = ep.get('upload', {}).get('title') or ep.get('title')
        summ = (out / 'summary.txt').read_text() if (out / 'summary.txt').exists() else summary(ep)
        if dst.exists() or _ai_thumb(title, summ, text, out, dst, vertical=True):
            pr = load(pf); pr['coverImg'] = f'ep/broll/short{k}_cover.jpg'; save(pf, pr); print('short cover:', text)


def _thumbs_main(ep, ep_dir):
    """Owner (Nov 8): Persian channel. The image model cannot spell Persian, so it draws the picture WITHOUT any text (dark navy look,
    one glossy subject, Finn small in a corner, empty top band) and our code typesets the Persian headline (ep['thumb_text'])."""
    from . import images
    out = ep_dir / 'thumbs'; out.mkdir(exist_ok=True)
    summ = summary(ep); (out / 'summary.txt').write_text(summ)
    title = ep.get('upload', {}).get('title') or ep.get('title')
    text = (ep.get('thumb_text') or ((ep.get('thumbnail') or {}).get('variants') or [{}])[0].get('words') or title).strip()
    if '|' not in text and ep.get('thumb_key') and ep['thumb_key'] in text:        # big black key word | the rest on the red box
        rest = ' '.join(text.replace(ep['thumb_key'], ' ').split())
        if rest: text = ep['thumb_key'] + '|' + rest
    try:
        if CFG.get('thumb_ai_text', True) and _ai_thumb(title, summ, text, out, ep_dir / 'thumbnail.jpg'):
            print('thumbnail (ChatGPT, own typography):', text); return
    except Exception as e: print('ai thumbnail failed', e)
    note, best, last = '', None, None
    for k in range(3):
        raw = out / f'bg{k}.png'
        prompt = f"""You are a top YouTube thumbnail designer. Design the PICTURE of the thumbnail (16:9) for this finance documentary video.
Title: {title}
What the video is about: {summ}
The viewer must understand at ONE glance WHO or WHAT the video is about: show the real subject in a recognisable way (for a company: its real
famous headquarters building with its real name sign or logo; for a person: a recognisable documentary portrait; for a country or currency:
its famous landmark / real banknotes; for an event: its most iconic moment - e.g. employees carrying boxes out of the bank, a crashing market
screen, people queueing at a bank), plus ONE dramatic element that creates curiosity (a crack through the building, money burning or
flying away, a giant red down-arrow, a shocked face). Cinematic, high contrast, saturated, glossy, dramatic light, very clean, readable
at phone size.
Leave the TOP 35% of the frame calm and dark (a Persian headline is added there later by a designer). Apart from the subject's own real
name/logo, NO text: no captions, no letters, no numbers, no fake writing.{note}"""
        if CFG.get('style') == 'finn':
            from . import fox
            ok = images.edit(prompt + '\nFinn the fox (the channel mascot) appears SMALL in a lower corner, reacting with a strong emotion: ' + fox.FINN,
                             [fox._ref()], str(raw), size='1536x1024', quality='high')
        else:
            ok = images.gen(prompt, raw, size='1536x1024', quality='high')
        if not ok: continue
        jpg = out / f'bg{k}.jpg'; _to_16x9(raw, jpg)
        r = _bg_check(jpg, title); print('thumb bg check', k, r)
        if not r.get('has_text', False) and r.get('top_clear', True) and r.get('topic_clear', True):
            best = jpg; break
        if not r.get('has_text', False) and not best: best = jpg
        last = jpg
        note = f"\nA previous attempt had this problem, avoid it: {r.get('problem') or 'it contained text'}."
    best = best or last      # owner (Nov 12): never the Latin code-made card; a little text in the picture is hidden under our headline band
    if best:
        try:
            _typeset(best, text, ep.get('thumb_key'), ep_dir / 'thumbnail.jpg'); print('thumbnail:', text); return
        except Exception as e: print('typeset failed', e)
    if CFG.get('language') == 'fa':
        try:
            _typeset_plain(text, ep.get('thumb_key'), ep_dir / 'thumbnail.jpg'); print('thumbnail (no picture):', text); return
        except Exception as e: print('plain typeset failed', e)
    print('picture failed -> code-made fallback')
    v = ((ep.get('thumbnail') or {}).get('variants') or [{}])[0]
    from PIL import Image
    pub = ROOT / 'render/public/ep'; pub.mkdir(parents=True, exist_ok=True)
    img = out / 'subject0.png'
    if v.get('subject') and not img.exists():
        images.gen(f"{v['subject']}. Photo-real, crisp, dramatic cinematic lighting, centred single subject, no text, isolated on a transparent background",
                   img, size='1024x1024', transparent=True, quality='high')
    props = {'number': v.get('number', ''), 'words': v.get('words') or text, 'v': 0}
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
    mus = np.zeros(N); m_ = audio.library_music(frames / FPS, track, fade_out=0)[:N]; mus[:len(m_)] = m_
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
            if b.get('sfx'):                     # Finn style: the sound chosen for this drawing (coins, crash, tension…)
                audio.place(fx, snd(b['sfx']), t + 0.05, 0.3); last_t, last_n = t, b['sfx']
            elif b['stage'] and b['stage'] != prev_stage:
                audio.place(fx, snd('whoosh1' if k % 2 else 'whoosh2'), max(0, t - 0.15), 0.35)
                audio.place(fx, snd('impact2' if k % 3 else 'impact3'), t + 0.1, 0.3); last_t = t
            elif t - last_t >= (2.5 if pr.get('vertical') else 4.5):
                opts = [n for n in SFX_FOR.get(b['visual'].get('type'), ['pop1']) if n != last_n] or ['pop1']
                n = opts[k % len(opts)]
                audio.place(fx, snd(n), t + 0.08, 0.22 if n in ('tick', 'click', 'pop1', 'pop2', 'pop3', 'pop4') else 0.28)
                last_t, last_n = t, n
        except Exception as e: print('sfx', e)
        prev_stage = b['stage']
    # owner's fixed audio rule (Nov 12): voice untouched; music at 0.30 ducked under the voice by a sidechain compressor; soft sound
    # effects (0.2-0.4); one loudness pass (I=-15, TP=-1.5); music fades out over the last 2.5 s; WAV until ONE final AAC 192k encode.
    d = out.parent; dur = N / SR
    vw, mw, fw = d / f'{out.stem}_vo.wav', d / f'{out.stem}_mus.wav', d / f'{out.stem}_fx.wav'
    sf.write(vw, v.astype(np.float32), SR); sf.write(mw, mus.astype(np.float32), SR); sf.write(fw, fx.astype(np.float32), SR)
    graph = (f"[1:a]volume=0.30[m];[0:a]asplit=2[v][vk];[m][vk]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
             f"[md]afade=t=out:st={max(0.0, dur - 2.5):.2f}:d=2.5[mf];[v][mf][2:a]amix=inputs=3:normalize=0:duration=first[mx];"
             f"[mx]loudnorm=I=-15:TP=-1.5,aformat=channel_layouts=stereo[a]")
    tmp = out.with_suffix('.wav')
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(vw), '-i', str(mw), '-i', str(fw), '-filter_complex', graph, '-map', '[a]',
        '-ar', '48000', '-c:a', 'pcm_s16le', str(tmp)])
    sh(['ffmpeg', '-v', 'error', '-y', '-i', str(silent), '-i', str(tmp), '-map', '0:v', '-map', '1:a',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', str(out)])
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
