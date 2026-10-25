"""Claude API client + research + the shared writing rules (Money Decoded)."""
import json, os, re, time, requests
from .common import CFG, ROOT

API = 'https://api.anthropic.com/v1/messages'

_MODEL = None
def model():
    """Use the configured model if it exists, else the newest Sonnet available to this key."""
    global _MODEL
    if _MODEL: return _MODEL
    want = CFG['models']['claude']
    try:
        r = requests.get('https://api.anthropic.com/v1/models?limit=100', headers={'x-api-key': os.environ['ANTHROPIC_API_KEY'],
                         'anthropic-version': '2023-06-01'}, timeout=30).json()
        ids = [m['id'] for m in r.get('data', [])]
        _MODEL = want if want in ids else next((i for i in ids if 'sonnet' in i), ids[0] if ids else want)
    except Exception as e:
        print('model list failed', e); _MODEL = want
    print('claude model:', _MODEL)
    return _MODEL

def ask(prompt, system='', max_tokens=16000, web_search=False, retries=4, image_url=None, effort='medium'):
    headers = {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
    content = prompt
    if image_url:   # download ourselves (Pinterest blocks Anthropic's URL fetcher via robots.txt) and send base64
        import base64 as _b64
        ir = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30); ir.raise_for_status()
        mt = ir.headers.get('content-type', 'image/jpeg').split(';')[0]
        if mt not in ('image/jpeg', 'image/png', 'image/gif', 'image/webp'): mt = 'image/jpeg'
        content = [{'type': 'image', 'source': {'type': 'base64', 'media_type': mt, 'data': _b64.b64encode(ir.content).decode()}}, {'type': 'text', 'text': prompt}]
        retries = 1
    body = {'model': model(), 'max_tokens': max_tokens, 'system': system, 'messages': [{'role': 'user', 'content': content}]}
    if web_search:
        body['tools'] = [{'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': 8}]
    # Sonnet 5.5 thinks by default and thinking counts toward max_tokens -> keep it minimal.
    # Try the lowest setting first; fall back for models that don't know these fields.
    variants = [{'thinking': {'type': 'between_tools'}, 'output_config': {'effort': effort}},
                {'output_config': {'effort': 'low'}}, {}]
    for a in range(retries):
        try:
            for v in variants:
                b = {**body, **v}
                r = requests.post(API, headers=headers, json=b, timeout=900)
                if r.status_code == 400 and any(k in r.text for k in ('thinking', 'output_config', 'effort')):
                    print('param not accepted:', r.text[:200]); continue
                break
            r.raise_for_status()
            j = r.json()
            txt = ''.join(b.get('text', '') for b in j.get('content', []) if b.get('type') == 'text')
            from . import cost; cost.claude(j.get('usage'))
            print(f"claude: stop={j.get('stop_reason')} usage={j.get('usage')} blocks={[b.get('type') for b in j.get('content', [])]} chars={len(txt)}", flush=True)
            return txt
        except Exception as e:
            resp = getattr(e, 'response', None)
            print('claude error', e, resp.text[:300] if resp is not None else ''); time.sleep(10 * (a + 1))
    raise RuntimeError('Claude API failed')

def _repair(txt):
    txt = re.sub(r'^```(?:json)?|```$', '', txt.strip(), flags=re.M)
    i, j = txt.find('{'), txt.rfind('}')
    if i < 0 or j < 0: return None
    t = txt[i:j + 1]
    for cand in (t, re.sub(r',\s*([}\]])', r'\1', re.sub(r'(?m)^\s*//.*$|(?<=[,\[{])\s*//[^\n]*', '', t))):
        try: return json.loads(cand)
        except Exception as e: err = e
    # several JSON objects (e.g. the model 'corrects' itself): keep the biggest valid one
    dec, objs, k = json.JSONDecoder(), [], 0
    while True:
        k = txt.find('{', k)
        if k < 0: break
        try:
            o, end = dec.raw_decode(txt, k); objs.append(o); k = end
        except Exception: k += 1
    if objs: return max(objs, key=lambda o: len(json.dumps(o)))
    print('json parse error', err)
    return None

def ask_json(prompt, **kw):
    from .common import WORK
    for a in range(3):
        txt = ask(prompt + '\n\nReturn ONLY one valid JSON object (no comments, no markdown fences, no text before or after).', **kw)
        obj = _repair(txt)
        if obj is not None: return obj
        kw['max_tokens'] = min(64000, int(kw.get('max_tokens', 16000) * 1.5))
        (WORK / f'raw_fail_{a}.txt').write_text(txt or '<empty>')
        print('bad JSON, first chars:', (txt or '')[:300].replace('\n', ' '))
    raise RuntimeError('no JSON from Claude')

def ask_json_image(url, prompt):
    return ask_json(prompt, image_url=url, max_tokens=3000)

RULES = (ROOT / 'config/rules.md').read_text()

def research(topic):
    return ask(f"""Research this topic for an English money/finance explainer video (educational, US/UK/Canada audience): "{topic}".
Use web search. Collect 14–20 accurate, specific, surprising facts with numbers, dates and a clear TIMELINE (what happened / happens
first, next, then…), each with its source URL. Prefer: central banks (Federal Reserve, Bank of England, ECB), IMF, World Bank, BIS,
SEC/FINRA/FCA, FDIC, US Treasury, BLS/ONS, DOJ/court records for scams, Reuters, Bloomberg, FT, WSJ, The Economist, established history books.
Cover: the mechanism step by step (how the money actually moves), the most surprising moments, the people involved (well-documented
public facts only), common myths vs facts, and everyday situations the viewer recognises. If a figure is disputed, say so.
No investment advice or predictions. Output a compact bullet list with URLs.""", web_search=True, max_tokens=7000)

WORDS_MIN, WORDS_MAX = 1200, 1320   # ≈ 8:30–9:15 with pauses (analytics: 10:50 was too long for our retention)

HOOK_RULES = """OPENING = the first 30 seconds (analytics: this is where we lose 1/3 of viewers). The hook scene has 5–7 short sentences:
- Sentence 1 is a COLD OPEN in the middle of the most surprising, most visual moment of the whole story (no "hi", no "in this video", no definition).
- Sentences 2–3 turn it into a burning question the viewer needs answered.
- By ~20 seconds, promise the payoff concretely ("by the end, you'll know exactly where that money went — and it's not where you think").
- No background, history, definitions or statistics before 0:30. Every sentence must be instantly visual."""

STORY_CRAFT = """STORYTELLING CRAFT (apply all six, every episode):
1. HOOK — sentence 1 is one of: a tense moment, an intriguing question, an unexpected statement, or a belief the viewer holds that we are about to break.
2. OPEN LOOPS — raise a question and do NOT answer it yet; answer it later in the story. Keep 1-2 loops open at all times; close each one with a satisfying reveal.
3. EMOTIONAL TRIGGERS — every scene makes the viewer FEEL something: surprise, awe ("they did WHAT with the money?"), outrage at a clever trick, tension, "that's me", nostalgia (everyday moments everyone knows). Name the feeling you are aiming for in each scene to yourself and write for it.
4. PACING — mix deliberately: runs of very short punchy sentences for tension and action, then one longer sentence to let a big idea land. Never three long sentences in a row.
5. CURIOSITY GAP — give enough to hook, never everything at once: tease the answer before giving it ("the culprit isn't what you think…").
6. PATTERN INTERRUPTS — every 60-90 seconds break the rhythm: a shocking one-line fact, a sudden change of tone (whisper → excitement), a direct question to the viewer, a surprising comparison or a format switch (countdown, myth vs fact, "follow the money")."""

SEO_RULES = """SEARCH (viewers find finance videos with concrete searches like "how banks create money", "stock market crash"):
- First decide the MAIN KEYWORD: the most-searched common name of the topic (e.g. "inflation", "ponzi scheme", "compound interest" — not a
  poetic paraphrase like "the silent money thief"). Put it in upload.main_keyword.
- upload.title contains the main keyword word-for-word, front-loaded, ≤ 60 characters, still a plain clear question/statement
  (rewrite the topic-bank wording if it lacks the keyword).
- Tags are the exact high-volume search phrases for the topic (what people really type, e.g. 'inflation', 'what is inflation', 'inflation explained'),
  never invented jargon; at least 3 tags appear word-for-word in the title and the first 5 tags appear word-for-word in the description.
- tags[0] = the main keyword; the first 5 tags are exact search phrases people type (short, lowercase); then related phrases (15–20 tags).
- The first sentence of the description contains the main keyword naturally; the keyword appears 2-3 times in the description in total.
- 3 hashtags: the main keyword (no spaces) first."""
