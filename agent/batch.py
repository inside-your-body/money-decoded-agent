"""Monthly voice batch (owner Nov 12): ElevenLabs credits expire at the end of the month, so the month's episodes are researched,
written (with diacritics for the narrator) and VOICED in advance. Each prepared episode is stored as a GitHub release asset
(release "prepared", ep-<topic id>.tar); the daily build downloads it and only makes pictures, renders and uploads.
Nothing is uploaded to YouTube here."""
import json, os, subprocess, tarfile, time, datetime as dt
import soundfile as sf
from .common import ROOT, WORK, load, save, CFG

REL = 'prepared'
KEEP = ('episode.json', 'research.md', 'segs_long.json', 'segs_short0.json')


def _gh(*a):
    return subprocess.run(['gh', *a], capture_output=True, text=True)


def assets():
    r = _gh('release', 'view', REL, '--json', 'assets', '-q', '.assets[].name')
    return set(r.stdout.split()) if r.returncode == 0 else set()


def _pack(ep_dir, tid):
    tar = WORK / f'ep-{tid}.tar'
    with tarfile.open(tar, 'w') as t:
        for n in KEEP:
            if (ep_dir / n).exists(): t.add(ep_dir / n, arcname=n)
        for w in sorted(ep_dir.glob('vo_*.wav')):                 # wav -> flac (half the size, lossless)
            a, sr = sf.read(w); fl = w.with_suffix('.flac'); sf.write(fl, a, sr); t.add(fl, arcname=fl.name)
    if _gh('release', 'view', REL).returncode != 0:
        _gh('release', 'create', REL, '--title', 'Prepared episodes (voices)', '--notes', 'Voiced episodes waiting for their build day. Do not delete.')
    r = _gh('release', 'upload', REL, str(tar), '--clobber')
    if r.returncode != 0: raise RuntimeError('release upload failed: ' + r.stderr[:300])
    return tar.name


def restore(topic, ep_dir):
    """Daily build: unpack a prepared (already voiced) episode into ep_dir. True if found."""
    name = f"ep-{topic.get('id')}.tar"
    if topic.get('id') is None or (ep_dir / 'vo_long.wav').exists(): return (ep_dir / 'vo_long.wav').exists()
    r = _gh('release', 'download', REL, '-p', name, '-D', str(WORK), '--clobber')
    if r.returncode != 0: print('no prepared episode for', topic.get('id'), r.stderr[:200]); return False
    with tarfile.open(WORK / name) as t: t.extractall(ep_dir)
    for fl in ep_dir.glob('vo_*.flac'):
        a, sr = sf.read(fl); sf.write(fl.with_suffix('.wav'), a, sr); fl.unlink()
    print('restored prepared episode', name); return True


def main():
    from . import tl, scout, tts
    limit = int(os.environ.get('LIMIT') or 30)
    budget_s = float(os.environ.get('BUDGET_MIN') or 320) * 60
    t0 = time.time()
    try: scout.run_viral()                    # the month's batch of 30 viral-based topics (once per month)
    except Exception as e: print('scout failed:', e)
    topics = load(ROOT / 'data/topics.json')
    have = assets()
    todo = [t for t in topics if t['status'] in ('todo', 'next') and f"ep-{t['id']}.tar" not in have][:limit]
    print(f'{len(todo)} episodes to voice; credits left this month ≈ {tts.credits_left_this_month()}')
    done = []
    for t in todo:
        left = tts.credits_left_this_month()
        spent = json.loads((WORK / 'eleven_chars.json').read_text()).get('chars', 0) if (WORK / 'eleven_chars.json').exists() else 0
        if left is not None and left - spent < 10000: print('monthly ElevenLabs share used up -> stop'); break
        if time.time() - t0 > budget_s: print('time budget used -> the rest in the next run'); break
        ep_dir = WORK / 'prep' / str(t['id']); ep_dir.mkdir(parents=True, exist_ok=True)
        try:
            print('== voicing', t['id'], t['title'])
            tl.build(t, ep_dir, voice_only=True)
            _pack(ep_dir, t['id']); t['prepared'] = True; done.append(t['id'])
            if len(done) == 1:          # a listening sample for the owner: first minute of the long voice + the Short
                pv = ROOT / 'samples/voice_preview'; pv.mkdir(parents=True, exist_ok=True)
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ep_dir / 'vo_long.wav'), '-t', '75', '-b:a', '96k', str(pv / f"ep-{t['id']}-long.mp3")])
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(ep_dir / 'vo_short0.wav'), '-b:a', '96k', str(pv / f"ep-{t['id']}-short.mp3")])
                (pv / f"ep-{t['id']}.txt").write_text(t['title'] + '\n\n' + '\n'.join(l.get('say') or l['text'] for l in tl.long_lines(load(ep_dir / 'episode.json'))[:12]))
        except Exception as e:
            print('episode failed:', t['id'], e)
            if 'ElevenLabs refused' in str(e): break                     # plan/credit problem: stop, do not burn Claude credits
        save(ROOT / 'data/topics.json', topics)
    tts.commit_usage()
    s = load(ROOT / 'data/prepared.json', {}); s.setdefault('done', []); s['done'] = sorted(set(s['done'] + done))
    s['updated'] = dt.datetime.utcnow().isoformat(timespec='seconds'); save(ROOT / 'data/prepared.json', s)
    print('voiced this run:', done)


if __name__ == '__main__':
    main()
