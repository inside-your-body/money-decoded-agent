"""Money Decoded episode pipeline (timeline format): topic -> research -> script -> storyboard -> voice -> render -> audio -> thumbnail -> upload.
Owner (Oct 24 2026): every day one long video at 20:00 UTC (23:00 Istanbul) + ONE Short at 20:30 UTC, uploaded earlier as scheduled."""
import argparse, datetime as dt, json, os
from .common import ROOT, WORK, load, save, CFG


def pick_topic():
    topics = load(ROOT / 'data/topics.json')
    tl_ = lambda x: x.get('format') == 'timeline'
    return next((x for x in topics if x['status'] == 'next' and tl_(x)), None) \
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
    # cron runs twice a day (main + backup); only one episode per day
    h = load(ROOT / 'data/history.json')
    last = max((e.get('built_at') for e in h['episodes'] if e.get('built_at')), default=None)
    if last and not a.topic and not a.dry_run:
        gap = (dt.datetime.utcnow() - dt.datetime.fromisoformat(last)).total_seconds() / 3600
        if gap < CFG['schedule']['min_hours_between_episodes']:
            print(f'last episode {gap:.0f} h ago -> skip'); return
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
        tl.build(topic, ep_dir)
        if a.stage == 'build':
            print('build stage done:', ep_dir); return
    ep = load(ep_dir / 'episode.json')
    shard.concat(ep_dir)
    long_final, shorts, track = tl.finish(ep, ep_dir)
    pkg = package.build(ep, ep_dir)
    disclaimer = 'Educational content only — not financial advice.'
    desc = '\n'.join(l for l in pkg['description'].split('\n') if not l.strip().lower().startswith('music:'))   # the real credit is added below
    if 'not financial advice' not in desc.lower(): desc += '\n\n' + disclaimer
    pkg['description'] = (desc + '\n\n' + audio.credit(track))[:4900]
    tags = ' '.join('#' + h.lstrip('#') for h in ep['upload'].get('hashtags', [])[:3])
    spk = []
    for k, f, st in shorts:
        s = ep['shorts'][k]
        title = (s.get('title') or ep['upload']['title'])[:85]
        spk.append({'k': k, 'file': str(f), 'title': title + ' #Shorts',
                    'description': (s.get('caption') or s['lines'][0]['text']) + '\n\nThe full story: {FULL_URL}\n\n' + tags + '\n\n' + disclaimer + '\n\n' + audio.credit(st)})
    pkg['shorts'] = spk; save(ep_dir / 'package.json', pkg)
    if a.dry_run:
        print('dry run: outputs in', ep_dir); return
    from . import youtube
    yt = youtube.client()                      # refuses to continue unless the token belongs to Money Decoded
    for old in [x for x in os.environ.get('REPLACE_IDS', '').replace(',', ' ').split() if x]:
        try: yt.videos().delete(id=old).execute(); print('deleted old upload', old)
        except Exception as e: print('could not delete', old, e)
    at = youtube.publish_time(CFG['schedule']['publish_long_utc'])
    thumb = ep_dir / 'thumbnail.jpg'
    vid = youtube.upload(yt, long_final, pkg['title'], pkg['description'], pkg['tags'], thumb if thumb.exists() else None, publish_at=at, synthetic=True)
    try: youtube.add_to_playlist(yt, vid)
    except Exception as e: print('playlist', e)
    sids = []
    for s in spk:
        try:
            # Short #1 30 min after the long video, Short #2 the next afternoon (US morning) so the channel gets a fresh upload every half day
            when = youtube.publish_time(CFG['schedule']['publish_short_utc']) if s['k'] == 0 else youtube.publish_next(CFG['schedule'].get('publish_short2_utc', '14:00'))
            svid = youtube.upload(yt, s['file'], s['title'], s['description'].replace('{FULL_URL}', 'https://youtu.be/' + vid), pkg['tags'][:10],
                                  publish_at=when, synthetic=True)
            sids.append(svid)
            try: youtube.pin_comment_text(yt, svid, 'The full story is here: https://youtu.be/' + vid)
            except Exception as e: print('short comment not posted:', e)
        except Exception as e: print('short upload failed', e)
    try: youtube.pin_comment_text(yt, vid, pkg['pinned_comment'])
    except Exception as e: print('comment not posted (will work once public):', e)
    mark_done(topic['id'], {'topic': topic['title'], 'video_id': vid, 'short_ids': sids, 'publish_at': at, 'format': 'tl', 'fmt': ep.get('fmt'), 'music': track,
                            'built_at': dt.datetime.utcnow().isoformat(timespec='seconds')})
    save(ep_dir / 'result.json', {'video': vid, 'shorts': sids, 'publish_at': at, 'pinned_comment': pkg['pinned_comment']})
    print('DONE', vid, sids, at)


if __name__ == '__main__':
    main()
