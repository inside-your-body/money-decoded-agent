"""YouTube craft checks (owner Oct 30: use the YouTube skills he installed - yt-package, yt-script, yt-seo, yt-shorts, yt-chapters,
yt-viral - inside the bot). Our own implementation of their rules so every episode is checked automatically:
- title + thumbnail are ONE unit: <=60 chars (desktop), subject inside the first 40 (mobile), <=2 ALL-CAPS words, a number/name/date,
  no vague hype words, subject front-loaded; thumbnail text <=3 words and NEVER repeats the title's words.
- hook (first ~15 s) scored on 5 properties - specificity, address ("you"), stakes, curiosity, brevity - verdict = 60 % mean + 40 % weakest.
- search: 3 queries the video must win; their words must be in the title + first 2 description lines.
- chapters: first 00:00, >= 3, each >= 10 s.
- Shorts: line 1 is a NEW hook that works without the long video; it loops into the last line."""
import re

DESKTOP, MOBILE = 60, 40
VAGUE = {"amazing", "incredible", "insane", "crazy", "huge", "massive", "ultimate", "best", "powerful", "secret", "revolutionary",
         "mindblowing", "epic", "perfect", "complete", "everything", "shocking", "unbelievable"}
STOP = {"the", "a", "an", "of", "for", "to", "in", "on", "and", "or", "is", "are", "with", "your", "you", "my", "i", "this", "that",
        "it", "how", "what", "why", "does", "do", "when", "where", "after"}
HOOK_TYPES = ["the statistic (a number they did not know, then the consequence)", "the mistake (the error the viewer is making right now)",
              "contrarian flip (the accepted belief, then why it is wrong)", "the reveal (promise to show one specific thing, show it soon)",
              "the clock (bound the payoff in time)", "cold open in the middle of the most dramatic moment",
              "direct question the viewer cannot answer", "the cost (what keeping the current belief costs them)",
              "someone else's result (a real named case), then the mechanism", "the comparison (two numbers that should not differ, but do)"]


def _w(t): return re.findall(r"[a-z0-9']+", (t or '').lower())


def title_lint(title, thumb=None):
    t = (title or '').strip(); n = len(t); issues, good = [], []
    if n > DESKTOP: issues.append(f'{n} chars > {DESKTOP} (desktop search cuts it)')
    else: good.append('fits desktop')
    if n > MOBILE:
        head = set(_w(t[:MOBILE])) - STOP
        if not head: issues.append('subject lost in the first 40 chars (mobile feed)')
    caps = [x for x in t.split() if len(x) > 2 and x.isupper()]
    if len(caps) > 2: issues.append('more than 2 ALL-CAPS words')
    v = [x for x in _w(t) if x in VAGUE]
    if v: issues.append('vague words: ' + ', '.join(sorted(set(v))))
    if re.search(r'\d', t) or re.search(r'\b(19|20)\d\d\b', t): good.append('concrete number/date')
    elif not any(x[:1].isupper() for x in t.split()[1:] if x.lower() not in STOP and len(x) > 3): issues.append('no number, name or date')
    if t.endswith('?'): good.append('open question')
    if not [x for x in _w(t)[:3] if x not in STOP]: issues.append('first 3 words are filler')
    if thumb:
        shared = (set(_w(t)) - STOP) & (set(_w(thumb)) - STOP)
        if shared: issues.append('thumbnail repeats title words: ' + ', '.join(sorted(shared)))
        else: good.append('thumbnail adds new words')
        if len(_w(thumb)) > 3: issues.append('thumbnail text > 3 words')
    return {'title': t, 'thumb': thumb, 'score': max(0, min(100, 100 - 14 * len(issues) + 4 * len(good))), 'issues': issues}


_CONCRETE = re.compile(r"(\$\d|\d[\d,.]*\s?(%|k|m|bn|x)?|\b\d+\s?(second|minute|hour|day|week|month|year)s?\b)", re.I)
_YOU = re.compile(r"\b(you|your|you're|yourself)\b", re.I)
_STAKE = re.compile(r"\b(lose|lost|losing|waste|cost|costs|risk|broke|debt|vanish\w*|disappear\w*|stolen|steal\w*|never|before|crash\w*|gone)\b", re.I)
_CUR = re.compile(r"\b(why|how|what|which|until|but|nobody|almost|except|reason|actually|really|where|who)\b", re.I)


def hook_score(t):
    w = _w(t)
    if not w: return {'verdict': 0}
    spec = max(0, min(100, 34 + 22 * len(_CONCRETE.findall(t)) - 16 * sum(x in VAGUE for x in w)))
    addr = max(0, min(100, 26 + 20 * len(_YOU.findall(t)) + (30 if _YOU.search(' '.join(t.split()[:6])) else 0)))
    stak = max(0, min(100, 22 + 26 * len(_STAKE.findall(t)) + (14 if _CONCRETE.search(t) else 0)))
    cur = max(0, min(100, 24 + 17 * len(_CUR.findall(t)) + (18 if t.strip().endswith('?') else 0)
                     - (18 if re.search(r'\b(because|so that|which means)\b', t, re.I) else 0)))
    n = len(w); brev = 100 if 9 <= n <= 30 else (max(30, 100 - (9 - n) * 11) if n < 9 else max(10, 100 - (n - 30) * 6))
    parts = {'specificity': spec, 'address': addr, 'stakes': stak, 'curiosity': cur, 'brevity': brev}
    v = round(0.6 * sum(parts.values()) / 5 + 0.4 * min(parts.values()))
    return {**parts, 'verdict': v, 'weakest': min(parts, key=parts.get)}


def best_hook(current, options):
    """Pick the strongest of the current hook and the options; returns (text, score)."""
    scored = [(hook_score(o)['verdict'], o) for o in [current] + [o for o in options if o]]
    s, o = max(scored, key=lambda x: x[0])
    return o, s


def query_gaps(title, first_lines, queries):
    """Words of each query that are missing from title + first 2 description lines."""
    have = set(_w(title + ' ' + first_lines))
    return {q: sorted(set(_w(q)) - STOP - have) for q in queries if set(_w(q)) - STOP - have}
