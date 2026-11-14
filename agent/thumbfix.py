"""Thumbnail repair (owner Nov 14): the Nov 16 video went out without its cover, the Nov 18 one got «تورم» on a money-printing topic, and
the Shorts had no cover. For every pair "LONG_ID:SHORT_ID" in FIX_IDS: a new two-part headline for THIS topic (checked by Claude),
ChatGPT makes the 16:9 thumbnail and the 9:16 Short cover in the approved template, both are set on YouTube (nothing is deleted or
re-uploaded). Pictures -> samples/thumb_fix/, report -> data/thumb_repair.json, history.json gets thumb_key / thumb status."""
import os, random, datetime as dt
from .common import ROOT, load, save
from . import tl, youtube


def main():
    yt = youtube.client()                       # refuses unless the token belongs to this channel
    out = ROOT / 'samples/thumb_fix'; out.mkdir(parents=True, exist_ok=True)
    hist = load(ROOT / 'data/history.json')
    used = [e.get('thumb_key') for e in hist['episodes'] if e.get('thumb_key')]
    report = []
    for pair in [x for x in os.environ.get('FIX_IDS', '').replace(' ', ',').split(',') if x]:
        vid, _, sid = pair.partition(':')
        e = next((x for x in hist['episodes'] if x.get('video_id') == vid), {})
        sn = (yt.videos().list(part='snippet', id=vid).execute().get('items') or [{}])[0].get('snippet', {})
        title = sn.get('title') or e.get('topic', '')
        topic = e.get('topic') or title
        summ = (sn.get('description') or '')[:700]
        r = {'video': vid, 'short': sid, 'topic': topic, 'title': title}
        h = tl.new_headline(topic, title, [u for u in used if u != e.get('thumb_key')] + ['تورم'])
        if not h:
            r['error'] = 'no headline'; r['tries'] = tl.TRIES[-6:]; report.append(r); print(r); continue
        text, key = h; r['headline'] = text; used.append(key)
        d = out / vid; d.mkdir(exist_ok=True)
        rest = text[len(key):].strip() if text.startswith(key) else ''
        ta, tb = (key, rest) if rest else (text.split()[0], ' '.join(text.split()[1:]))
        ht = ta + '|' + tb
        long_jpg, cov = out / f'{vid}_thumbnail.jpg', out / f'{sid or vid}_short_cover.jpg'
        subj = random.choice([s for s in tl.SUBJECTS if 'NO person' not in s]); r['subject'] = subj   # owner: a new face each time
        r['thumb_made'] = tl._ai_thumb(title, summ, ht, d, long_jpg, subject=subj)
        if r['thumb_made']: youtube.set_thumb(yt, vid, long_jpg)
        r['thumb'] = youtube.THUMBS.get(vid, 'not made')
        if sid:
            r['cover_made'] = tl._ai_thumb(title, summ, ht, d, cov, vertical=True, subject=subj) or tl.vertical_from(long_jpg, cov)
            if r['cover_made']: youtube.set_thumb(yt, sid, cov)
            r['short_thumb'] = youtube.THUMBS.get(sid, 'not made')
        for f in d.glob('*.png'): f.unlink()
        if e:
            e['thumb_key'] = key; e['thumb'] = r['thumb']
            if sid: e['short_thumbs'] = [r['short_thumb']]
        report.append(r); print(r)
    save(ROOT / 'data/history.json', hist)
    save(ROOT / 'data/thumb_repair.json', {'at': dt.datetime.utcnow().isoformat(timespec='seconds'), 'items': report})


if __name__ == '__main__':
    main()
