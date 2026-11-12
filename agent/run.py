"""Money Decoded episode pipeline (timeline format): topic -> research -> script -> storyboard -> voice -> render -> audio -> thumbnail -> upload.
Owner (Oct 24 2026): every day one long video at 20:00 UTC (23:00 Istanbul) + ONE Short at 20:30 UTC, uploaded earlier as scheduled."""
import argparse, datetime as dt, json, os
from .common import ROOT, WORK, load, save, CFG


def pick_topic():
    topics = load(ROOT / 'data/topics.json')
    tl_ = lambda x: x.get('format') == 'timeline'
    prep = next((x for x in topics if x['status'] in ('next', 'todo') and x.get('prepared')), None)   # already voiced (owner Nov 12)
    return prep or next((x for x in topics if x['status'] == 'next' and tl_(x)), None) \
        or next((x for x in topics if x['status'] == 'todo' and x.get('source') == 'user'), None) \
        or next((x for x in topics if x['status'] == 'todo' and tl_(x)), None) \
        or next(x for x in topics if x['status'] in ('next', 'todo'))


def mark_done(topic_id, entry):
    topics = load(ROOT / 'data/topics.json')
    for x in topics:
        if x['id'] == topic_id: x['status'] = 'done'
    if not any(x['status'] == 'next' for x in topics):
        nxt = next((x for x in topics if x['status'] == 'todo'), None)
        if nxt: nxt['status'] = 'next'
    save(ROOT / 'data/topics.json', topics)
    h = load(ROOT / 'data/history.json'); h['episodes'].append(entry)
    if entry.get('music'): h.setdefault('used_music', []).append(entry['music'])
    save(ROOT / 'data/history.json', h)


def next_slot():
    """Next free publish slot: every_days after the latest scheduled long video (never in the past), at publish_long_utc;
    the Short publish_short_utc on the same day. Returns ISO strings for YouTube publishAt."""
    sc = CFG['schedule']; every = int(sc.get('every_days', 2))
    hh, mm = map(int, sc['publish_long_utc'].split(':')); sh, sm = map(int, sc['publish_short_utc'].split(':'))
    now = dt.datetime.utcnow()
    last = max((dt.datetime.fromisoformat(e['publish_at'].rstrip('Z')) for e in load(ROOT / 'data/history.json', {'episodes': []})['episodes']
                if e.get('publish_at')), default=None)
    day = (last + dt.timedelta(days=every)).date() if last else now.date()
    t = dt.datetime.combine(day, dt.time(hh, mm))
    while t < now + dt.timedelta(hours=1): t += dt.timedelta(days=every)
    return t.isoformat() + 'Z', dt.datetime.combine(t.date(), dt.time(sh, sm)).isoformat() + 'Z'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='build everything, do not upload')
    ap.add_argument('--topic', default=None)
    ap.add_argument('--stage', default='all', choices=['all', 'build', 'finish'],
                    help='build = everything up to the render (then shards render in parallel); finish = concat parts + audio + upload')
    a = ap.parse_args()
    cur = load(WORK / 'current.json', {})
    if a.stage == 'finish' and cur:
        return run_tl(a, cur['topic'], WORK / cur['dir'])

    if CFG['schedule'].get('paused') and os.environ.get('GITHUB_EVENT_NAME') == 'schedule':
        print('schedule paused in config/channel.json -> skip'); return
    # owner (Nov 12): build as many episodes per day as the YouTube upload quota allows; each one is scheduled into the next free
    # every-other-day slot (long 17:00 Istanbul, Short 17:30). A cap per day keeps us under the daily API quota.
    h = load(ROOT / 'data/history.json')
    today = dt.datetime.utcnow().strftime('%Y-%m-%d')
    built_today = sum(1 for e in h['episodes'] if (e.get('built_at') or '').startswith(today))
    if not a.topic and not a.dry_run and built_today >= int(CFG['schedule'].get('max_episodes_per_day', 3)):
        print(f'{built_today} episodes built today (daily upload quota) -> skip'); return
    if not a.topic and not a.dry_run and not any(x['status'] in ('next', 'todo') and x.get('prepared') for x in load(ROOT / 'data/topics.json')):
        print('no voiced episode waiting (run the Voice batch workflow) -> skip'); return
    if not a.dry_run:
        from . import tts
        left = tts.credits_left_this_month()
        if left is not None and left < 12000:
            print(f'ElevenLabs: only {left} of this channel\'s monthly credits left -> no new episode this month'); return
    if not a.topic:
        try:
            from . import scout
            scout.run_viral()          # keep >= 4 viral-adapted timeline topics waiting in the bank
        except Exception as e:
            print('scout skipped:', e)
    if a.topic and a.topic.strip().isdigit():          # a topic from the bank by its number (keeps its angle/hook/ref)
        topic = next((t for t in load(ROOT / 'data/topics.json') if str(t.get('id')) == a.topic.strip()), None) or pick_topic()
    else:
        topic = {'id': None, 'title': a.topic} if a.topic else pick_topic()
    ep_dir = WORK / dt.datetime.utcnow().strftime('%Y%m%d'); ep_dir.mkdir(parents=True, exist_ok=True)
    save(WORK / 'current.json', {'dir': ep_dir.name, 'topic': topic, 'format': 'tl'})
    return run_tl(a, topic, ep_dir)


def run_tl(a, topic, ep_dir):
    from . import tl, package, audio, shard
    print('== topic:', topic['title'])
    if a.stage != 'finish':
        try:
            from . import batch; batch.restore(topic, ep_dir)        # voices made in the monthly batch
        except Exception as e: print('restore failed:', e)
        tl.build(topic, ep_dir)
        if a.stage == 'build':
            print('build stage done:', ep_dir); return
    ep = load(ep_dir / 'episode.json')
    shard.concat(ep_dir)
    long_final, shorts, track = tl.finish(ep, ep_dir)
    pkg = package.build(ep, ep_dir)
    disclaimer = CFG.get('disclaimer') or 'این ویدیو فقط آموزشی است و توصیه‌ی مالی یا سرمایه‌گذاری نیست.'
    desc = '\n'.join(l for l in pkg['description'].split('\n') if not l.strip().lower().startswith('music:') and 'توصیه‌ی مالی' not in l and 'توصیه مالی' not in l)
    desc += '\n\n' + disclaimer          # owner's exact disclaimer line, always last before the music credit
    pkg['description'] = (desc + '\n\n' + audio.credit(track))[:4900]
    tags = ' '.join('#' + h.lstrip('#').replace(' ', '_') for h in ep['upload'].get('hashtags', [])[:3])
    spk = []
    for k, f, st in shorts:
        s = ep['shorts'][k]
        title = (s.get('title') or ep['upload']['title'])[:85]
        spk.append({'k': k, 'file': str(f), 'title': title + ' #Shorts',
                    'description': (s.get('caption') or s['lines'][0]['text']) + '\n\nداستان کامل: {FULL_URL}\n\n' + tags + '\n\n' + disclaimer + '\n\n' + audio.credit(st)})
    pkg['shorts'] = spk; save(ep_dir / 'package.json', pkg)
    if a.dry_run:
        print('dry run: outputs in', ep_dir); return
    from . import youtube
    yt = youtube.client()                      # refuses to continue unless the token belongs to Money Decoded
    for old in [x for x in os.environ.get('REPLACE_IDS', '').replace(',', ' ').split() if x]:
        try: yt.videos().delete(id=old).execute(); print('deleted old upload', old)
        except Exception as e: print('could not delete', old, e)
    at, short_at = next_slot()
    thumb = ep_dir / 'thumbnail.jpg'
    vid = youtube.upload(yt, long_final, pkg['title'], pkg['description'], pkg['tags'], thumb if thumb.exists() else None, publish_at=at, synthetic=True)
    try: youtube.add_to_playlist(yt, vid)
    except Exception as e: print('playlist', e)
    sids = []
    for s in spk:
        try:
            # Short #1 30 min after the long video, Short #2 the next afternoon (US morning) so the channel gets a fresh upload every half day
            when = short_at
            svid = youtube.upload(yt, s['file'], s['title'], s['description'].replace('{FULL_URL}', 'https://youtu.be/' + vid), pkg['tags'][:10],
                                  publish_at=when, synthetic=True)
            sids.append(svid)
            try: youtube.pin_comment_text(yt, svid, 'داستان کامل اینجاست: https://youtu.be/' + vid)
            except Exception as e: print('short comment not posted:', e)
        except Exception as e: print('short upload failed', e)
    try: youtube.pin_comment_text(yt, vid, pkg['pinned_comment'])
    except Exception as e: print('comment not posted (will work once public):', e)
    try: from . import tts; tts.commit_usage()
    except Exception as e: print('usage tally', e)
    mark_done(topic['id'], {'topic': topic['title'], 'video_id': vid, 'short_ids': sids, 'publish_at': at, 'format': 'tl', 'fmt': ep.get('fmt'), 'music': track,
                            'built_at': dt.datetime.utcnow().isoformat(timespec='seconds')})
    save(ep_dir / 'result.json', {'video': vid, 'shorts': sids, 'publish_at': at, 'pinned_comment': pkg['pinned_comment']})
    print('DONE', vid, sids, at)


if __name__ == '__main__':
    main()
