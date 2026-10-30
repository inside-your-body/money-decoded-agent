"""Upload package: chapters from real scene timings, description, tags, hashtags."""
from .common import load, save

def _ts(s):
    s = int(s); return f'{s // 60:02d}:{s % 60:02d}' if s < 3600 else f'{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}'

def build(ep, ep_dir):
    segs = load(ep_dir / 'segs_long.json')
    up = ep['upload']
    chapters, si = [], 0
    for sc in ep['scenes']:
        t = 0 if si == 0 else segs[si]['start']
        title = sc.get('title') or sc.get('part', '').title()
        if not chapters or t - chapters[-1][0] >= 15:
            chapters.append((t, title))
        si += len(sc['narration'])
    chapters[0] = (0, chapters[0][1])
    # yt-chapters rules (else YouTube silently ignores the list): first 00:00, at least 3, each at least 10 s
    total = segs[-1]['end'] if segs else 0
    chapters = [c for k, c in enumerate(chapters) if (chapters[k + 1][0] if k + 1 < len(chapters) else total) - c[0] >= 10 or k == 0]
    chap = '\n'.join(f'{_ts(t)} {name}' for t, name in chapters) if len(chapters) >= 3 else ''
    desc = up['description']
    if chap: desc = desc.replace('{CHAPTERS}', chap) if '{CHAPTERS}' in desc else desc + '\n\nChapters\n' + chap
    else: desc = desc.replace('Chapters\n{CHAPTERS}', '').replace('{CHAPTERS}', '')
    if ep.get('sources') and 'Sources' not in desc:
        desc += '\n\nSources\n' + '\n'.join(f"- {s['title']}: {s['url']}" for s in ep['sources'][:8])
    tags = list(dict.fromkeys([t.strip() for t in up.get('tags', []) if t.strip()]))
    kw = (up.get('main_keyword') or '').strip().lower()
    if kw:   # SEO: main keyword is the first tag, and tags that appear in the title come right after it
        tags = [kw] + [t for t in tags if t.lower() != kw]
    title_l = up['title'].lower()
    tags = tags[:1] + sorted(tags[1:], key=lambda t: 0 if t.lower() in title_l else 1)
    tl_ = 0; keep = []
    for t in tags[:15]:                       # yt-seo: tags are a weak signal - 15 exact phrases are plenty
        if tl_ + len(t) + 2 > 480: break
        keep.append(t); tl_ += len(t) + 2
    # SEO (TubeBuddy/vidIQ check exact tag phrases in title + description): the main keyword tag must be inside the title, and the
    # top tags must appear word-for-word in the description -> add one natural 'In this video' line with the tags missing from it.
    tl = up['title'].lower()
    in_title = [t for t in keep if t.lower() in tl]
    if not in_title:
        core = up['title'].split(':')[0].split('?')[0].strip().lower()
        if 3 <= len(core) <= 40: keep = [core] + keep[:-1] if len(keep) >= 20 else [core] + keep
    missing = [t for t in keep[:10] if t.lower() not in desc.lower()]
    if missing:
        para = 'In this video: ' + ', '.join(missing) + '.'
        cut = desc.find('\n\n')
        desc = (desc[:cut] + '\n\n' + para + desc[cut:]) if cut > 0 else desc + '\n\n' + para
    hashtags = ' '.join('#' + h.lstrip('#') for h in up.get('hashtags', [])[:5])
    if hashtags and not any(('#' + h.lstrip('#')).lower() in desc.lower() for h in up.get('hashtags', [])[:2]): desc += '\n\n' + hashtags
    pkg = {'title': up['title'][:100], 'description': desc[:4900], 'tags': keep,
           'short_title': (up.get('short_title') or up['title'])[:95] + ('' if '#Shorts' in up.get('short_title', '') else ' #Shorts'),
           'short_description': (up.get('short_description') or '') + '\n\nFull episode: {FULL_URL}' + ('' if '#' in (up.get('short_description') or '') else '\n\n' + hashtags),
           'pinned_comment': up.get('pinned_comment', ''),
           'thumbnail_variants': [p.name for p in sorted(ep_dir.glob('thumbnail*.jpg'))],
           'manual_steps': 'Optional (Studio, 1 min): Details > Thumbnail > Test & compare with thumbnail.jpg + thumbnail_b.jpg + thumbnail_c.jpg; '
                           'Short > Related video = the full episode; pin the comments.'}
    save(ep_dir / 'package.json', pkg)
    return pkg
