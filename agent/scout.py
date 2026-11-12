"""Viral topic scout (owner's core strategy): find money/finance videos that ALREADY went viral on YouTube and add our own
timeline version of them to the topic bank (owner's own topics always stay first)."""
import datetime as dt, json, re
from .common import ROOT, load, save
from . import llm

# ---- viral adaptation scout (owner, Oct 24): find videos that already went viral and make OUR timeline version of them ----
VIRAL_SEEDS = ["what happens if you invest", "what happens to your money when", "how much would I have if I invested",
               "what happens if the stock market crashes", "what happens when inflation", "why the rich", "how banks really make money",
               "what happens if you put $1000", "the truth about money", "what happens to your savings", "how compound interest",
               "what happens if the dollar collapses", "why everyone is wrong about money", "how the richest man", "biggest financial scam",
               "stock market crash explained", "how money works", "hyperinflation explained", "how billionaires avoid taxes",
               "financial bubble explained", "why is everything so expensive", "how credit card companies make money"]
# owner (Nov 8): the channel is Persian -> also look at what already works with Persian viewers (searched in Persian)
VIRAL_SEEDS_FA = ["تورم چیست", "چرا دلار گران می شود", "طلا یا دلار", "کلاهبرداری پانزی", "بیت کوین چیست", "سقوط بورس",
                  "ثروتمندان چطور پولدار شدند", "بانک ها چطور پول می سازند", "بزرگترین کلاهبرداری تاریخ", "ابرتورم",
                  "چرا پول ارزش ندارد", "حذف صفر از پول ملی", "اقتصاد به زبان ساده", "سواد مالی"]

def _viral(yt, queries):
    ids = {}
    for q in queries:
        for after in (None, (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=730)).strftime('%Y-%m-%dT%H:%M:%SZ')):
            fa = bool(re.search(r'[\u0600-\u06FF]', q))
            kw = dict(part='snippet', q=q, type='video', order='viewCount', maxResults=25, relevanceLanguage='fa' if fa else 'en')
            if after: kw['publishedAfter'] = after
            try:
                for i in yt.search().list(**kw).execute().get('items', []): ids[i['id']['videoId']] = q
            except Exception as e: print('search failed', q, e)
    vids, chans = [], {}
    keys = list(ids)
    for k in range(0, len(keys), 50):
        for v in yt.videos().list(part='snippet,statistics,contentDetails', id=','.join(keys[k:k + 50])).execute().get('items', []):
            m = re.search(r'(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', v['contentDetails'].get('duration', 'PT0S'))
            sec = int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0)
            vids.append({'id': v['id'], 'title': v['snippet']['title'], 'persian': bool(re.search(r'[\u0600-\u06FF]', v['snippet']['title'])), 'channel': v['snippet']['channelTitle'], 'cid': v['snippet']['channelId'],
                         'views': int(v['statistics'].get('viewCount', 0)), 'minutes': round(sec / 60, 1)})
    cids = list({v['cid'] for v in vids})
    uploads = {}
    for k in range(0, len(cids), 50):
        for c in yt.channels().list(part='statistics,contentDetails', id=','.join(cids[k:k + 50])).execute().get('items', []):
            chans[c['id']] = int(c['statistics'].get('subscriberCount', 0) or 0)
            uploads[c['id']] = (c.get('contentDetails', {}).get('relatedPlaylists') or {}).get('uploads')
    # yt-viral: raw views rank channel SIZE, not ideas -> rank by how far a video beat its own channel's median (last 15 uploads)
    med = {}
    for cid in cids[:60]:
        try:
            pl = uploads.get(cid)
            if not pl: continue
            items = yt.playlistItems().list(part='contentDetails', playlistId=pl, maxResults=15).execute().get('items', [])
            ids_ = [i['contentDetails']['videoId'] for i in items]
            if len(ids_) < 4: continue
            vs = sorted(int(x['statistics'].get('viewCount', 0)) for x in yt.videos().list(part='statistics', id=','.join(ids_)).execute().get('items', []))
            if len(vs) >= 4: med[cid] = vs[len(vs) // 2]
        except Exception as e: print('median failed', cid, e)
    for v in vids:
        cid = v.pop('cid')
        v['subs'] = chans.get(cid, 0); v['outlier'] = round(v['views'] / max(1000, v['subs']), 1)
        if cid in med: v['multiple'] = round(v['views'] / max(1000, med[cid]), 1)
    vids = [v for v in vids if v['views'] >= (30_000 if v.get('persian') else 200_000)]   # the Persian YouTube market is smaller
    rank = lambda x: x['views'] * min(20, x.get('multiple') or x['outlier'] / 3) ** 0.7
    return sorted(vids, key=lambda x: -rank(x))

def run_viral(force=False, want=4):
    topics = load(ROOT / 'data/topics.json')
    fresh = [t for t in topics if t['status'] in ('todo', 'next') and t.get('format') == 'timeline']
    state = load(ROOT / 'data/scout.json', {})
    month = dt.datetime.utcnow().strftime('%Y-%m')
    monthly = state.get('batch_month') != month          # owner (Nov 9): a batch of 30 topics at the start of every month
    if not monthly and len(fresh) >= want and not force:
        return
    if monthly: want = 30
    from .youtube import client
    yt = client()
    n = state.get('viral_i', 0)
    k = 6 if monthly else 2                      # 2 searches per seed ≈ 100 quota units each
    queries = [VIRAL_SEEDS[(n + i) % len(VIRAL_SEEDS)] for i in range(k)] + [VIRAL_SEEDS_FA[(n + i) % len(VIRAL_SEEDS_FA)] for i in range(k)]
    vids = _viral(yt, queries)[:150 if monthly else 80]
    existing = [t['title'] for t in topics]
    res = llm.ask_json(f"""You find topics for the Persian YouTube channel "پول و قدرت" (Persian-speaking adults in Iran and abroad): educational
stories about how money, banks, markets, debt, inflation, currencies, gold, crypto, taxes, scams and fortunes REALLY work, told with flat 2D
motion graphics and Persian kinetic typography. Pick ideas that Persian speakers care about and search for (inflation and rising prices, the dollar, gold and coins,
savings losing value, crypto, famous scams and fortunes, crashes and bubbles) - global stories told for a Persian audience are welcome. The channel rotates formats (timeline story,
countdown list, myth busting, true case story, what-if experiment) so topics of every shape are welcome. Strongest angle: hidden / silent processes. The owner's strategy: take topics that ALREADY went viral on YouTube and make our own version.

Viral videos found (English ones = proven ideas to remake in Persian; Persian ones = proof that Persian viewers want this; title, channel, views, subscribers, outlier = views / subscribers, multiple = views / that channel's median views of its last 15 videos — THE signal: a video at 3x+ its own channel's median proves the IDEA worked, not the channel size; minutes):
{json.dumps(vids, ensure_ascii=False)}

Our existing topics (never repeat or closely duplicate): {json.dumps(existing, ensure_ascii=False)}

OWNER'S TOPIC RULES (Nov 12): Persian viewers do not know foreign bank/finance names (e.g. Lehman Brothers) or jargon (bonds, mining,
deflation, interest-rate policy) - such topics are OUT. Topics must touch the viewer's OWN life in simple everyday Persian: money in daily life
(inflation, prices, savings losing value, gold/dollar/coins, banks, where money comes from), making money (income, side income, money mistakes,
businesses that earn while you sleep), stories of famous BRANDS everyone knows (always write «برند» before the name, e.g. «برند زارا ...»),
how the rich think and spend, scams, and the psychology of buying. Titles are a clear, curious question or claim that says exactly what the
viewer will see, e.g. «چرا کازینوها همیشه برنده‌ان و ریاضی پشت باختِ ما چیه؟», «برند مک‌دونالد در اصل از همبرگر پول درنمیاره!».
Never topics that tell people loans/debt are bad or good (opinions differ).
Pick the {want + 2} best proven ideas that fit our format (money over time: crashes, bubbles, bank runs, inflation, debt, compound growth,
scams, famous fortunes, taxes, housing, how institutions make money; skip: stock/crypto picks, "get rich quick", trading signals,
price predictions, gambling, MLM, party politics, music, pranks, kids). Prefer high multiples (3x+) first, then big view counts. For each pick, name the hook formula of the original title in 'angle'.
Phrase each title in PERSIAN the way Persian speakers SEARCH, broad and clear, ≤60 chars, main keyword front-loaded, e.g.
"بانک‌ها چطور پول را از هیچ می‌سازند؟", "۲۴ ساعت اول سقوط بازار بورس", "چرا برندگان لاتاری ورشکست می‌شوند؟". Not a translation of the original title.
Return JSON: {{"topics": [{{"title": str, "angle": str, "stamps": "e.g. ۹:۳۰ صبح > ظهر > روز دوم > سال اول",
"ref_id": str, "ref_title": str, "ref_views": int}}]}}""", max_tokens=16000 if monthly else 5000)
    low = {t.lower() for t in existing}
    new = [t for t in res.get('topics', []) if t.get('title') and t['title'].lower() not in low]
    nid = max([t['id'] for t in topics if isinstance(t.get('id'), int)] + [0]) + 1
    pos = max([i for i, t in enumerate(topics) if t.get('source') == 'user' and t['status'] != 'done'] + [
        max([i for i, t in enumerate(topics) if t['status'] == 'done'] + [-1])]) + 1
    for k, t in enumerate(new):
        topics.insert(pos + k, {'id': nid + k, 'title': t['title'], 'angle': (t.get('angle') or '') + (' | stamps: ' + t['stamps'] if t.get('stamps') else ''),
                                'format': 'timeline', 'status': 'todo', 'source': 'viral',
                                'ref': {'title': t.get('ref_title'), 'views': t.get('ref_views'), 'url': 'https://youtu.be/' + str(t.get('ref_id', ''))}})
    save(ROOT / 'data/topics.json', topics)
    if monthly: state['batch_month'] = month
    state.update({'viral_i': (n + k) % len(VIRAL_SEEDS), 'viral_last': dt.datetime.utcnow().isoformat(timespec='seconds'),
                  'viral_added': [t['title'] for t in new]})
    save(ROOT / 'data/scout.json', state)
    print('viral scout added:', [t['title'] for t in new])
