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

def _viral(yt, queries):
    ids = {}
    for q in queries:
        for after in (None, (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=730)).strftime('%Y-%m-%dT%H:%M:%SZ')):
            kw = dict(part='snippet', q=q, type='video', order='viewCount', maxResults=25, relevanceLanguage='en')
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
            vids.append({'id': v['id'], 'title': v['snippet']['title'], 'channel': v['snippet']['channelTitle'], 'cid': v['snippet']['channelId'],
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
    vids = [v for v in vids if v['views'] >= 200_000]
    rank = lambda x: x['views'] * min(20, x.get('multiple') or x['outlier'] / 3) ** 0.7
    return sorted(vids, key=lambda x: -rank(x))

def run_viral(force=False, want=4):
    topics = load(ROOT / 'data/topics.json')
    fresh = [t for t in topics if t['status'] in ('todo', 'next') and t.get('format') == 'timeline']
    if len(fresh) >= want and not force:
        return
    from .youtube import client
    yt = client()
    state = load(ROOT / 'data/scout.json', {})
    n = state.get('viral_i', 0)
    queries = [VIRAL_SEEDS[(n + i) % len(VIRAL_SEEDS)] for i in range(4)]       # 8 searches ≈ 800 quota units
    vids = _viral(yt, queries)[:80]
    existing = [t['title'] for t in topics]
    res = llm.ask_json(f"""You find topics for "Money Decoded" (English, adults; US/UK/Canada viewers): educational stories about how money, banks, markets,
debt, inflation, taxes, scams and fortunes REALLY work, explained by our mascot Finn the fox. The channel rotates formats (timeline story,
countdown list, myth busting, true case story, what-if experiment) so topics of every shape are welcome. Strongest angle: hidden / silent processes. The owner's strategy: take topics that ALREADY went viral on YouTube and make our own version.

Viral videos found (title, channel, views, subscribers, outlier = views / subscribers, multiple = views / that channel's median views of its last 15 videos — THE signal: a video at 3x+ its own channel's median proves the IDEA worked, not the channel size; minutes):
{json.dumps(vids, ensure_ascii=False)}

Our existing topics (never repeat or closely duplicate): {json.dumps(existing, ensure_ascii=False)}

Pick the {want + 2} best proven ideas that fit our format (money over time: crashes, bubbles, bank runs, inflation, debt, compound growth,
scams, famous fortunes, taxes, housing, how institutions make money; skip: stock/crypto picks, "get rich quick", trading signals,
price predictions, gambling, MLM, politics-only topics, music, pranks, kids). Prefer high multiples (3x+) first, then big view counts. For each pick, name the hook formula of the original title in 'angle'.
Phrase each title the way people SEARCH, broad and clear, ≤60 chars, main keyword front-loaded, e.g. "How Banks Create Money Out of Thin Air",
"What Happens in the First 24 Hours of a Stock Market Crash", "Why Lottery Winners Go Broke". Not a copy of the original title.
Return JSON: {{"topics": [{{"title": str, "angle": str, "stamps": "e.g. 9:30 AM > NOON > 4 PM > DAY 2 > YEAR 1",
"ref_id": str, "ref_title": str, "ref_views": int}}]}}""", max_tokens=5000)
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
    state.update({'viral_i': (n + 4) % len(VIRAL_SEEDS), 'viral_last': dt.datetime.utcnow().isoformat(timespec='seconds'),
                  'viral_added': [t['title'] for t in new]})
    save(ROOT / 'data/scout.json', state)
    print('viral scout added:', [t['title'] for t in new])
