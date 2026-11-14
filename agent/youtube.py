"""YouTube Data API v3 upload (scheduled publish, thumbnail, playlist).
Credentials: env YT_TOKEN_JSON = authorized-user JSON {client_id, client_secret, refresh_token, token_uri}."""
import json, os, datetime as dt
from .common import CFG

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube',
          'https://www.googleapis.com/auth/youtube.force-ssl']

def client():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    info = json.loads(os.environ['YT_TOKEN_JSON'])
    creds = Credentials.from_authorized_user_info(info, info.get('scopes'))   # scopes as granted (never ask for more on refresh)
    if not creds.valid: creds.refresh(Request())
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)
    # safety: never upload to another channel (the owner also runs Inside Your Body and Dokum TV)
    want = CFG['channel'].get('id')
    if want:
        mine = [c['id'] for c in yt.channels().list(part='id', mine=True).execute().get('items', [])]
        if want not in mine:
            raise RuntimeError(f'YT_TOKEN_JSON belongs to channel {mine}, not Money Decoded ({want}) -> refusing to upload')
    return yt

def publish_time(hhmm):
    """Today at hh:mm UTC; if that moment is already past (or <15 min away), publish now (None)."""
    h, m = map(int, hhmm.split(':'))
    now = dt.datetime.utcnow()
    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return None if t < now + dt.timedelta(minutes=15) else t.isoformat() + 'Z'

def publish_next(hhmm):
    """The next hh:mm UTC that is at least 6 h away (tomorrow afternoon for a build that finishes in the evening)."""
    h, m = map(int, hhmm.split(':'))
    now = dt.datetime.utcnow()
    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
    while t < now + dt.timedelta(hours=6): t += dt.timedelta(days=1)
    return t.isoformat() + 'Z'

def upload(yt, video, title, description, tags, thumb=None, publish_at=None, synthetic=False):
    from googleapiclient.http import MediaFileUpload
    status = {'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': synthetic}
    if publish_at: status.update(privacyStatus='private', publishAt=publish_at)
    else: status.update(privacyStatus='public')
    body = {'snippet': {'title': title[:100], 'description': description[:4900], 'tags': tags[:30],
                        'categoryId': CFG['channel']['category_id'], 'defaultLanguage': CFG['channel'].get('language', 'en'), 'defaultAudioLanguage': CFG['channel'].get('language', 'en')},
            'status': status}
    req = yt.videos().insert(part='snippet,status', body=body,
                             media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True, mimetype='video/mp4'))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st: print(f'  upload {int(st.progress() * 100)}%')
    vid = resp['id']; print('  uploaded https://youtu.be/' + vid)
    if thumb: set_thumb(yt, vid, thumb)
    return vid


THUMBS = {}      # video id -> 'ok' / 'error: ...' (owner Nov 14: a video went out without its cover and nobody knew)


def set_thumb(yt, vid, thumb):
    """Sets the custom thumbnail (re-encoded under YouTube's 2 MB limit), 3 tries; the result is kept in THUMBS for the history."""
    import time, pathlib
    from googleapiclient.http import MediaFileUpload
    from PIL import Image
    thumb = pathlib.Path(thumb)
    if not thumb.exists(): THUMBS[vid] = 'error: no file'; print('  thumbnail error: no file'); return False
    up = thumb
    if thumb.stat().st_size > 1_900_000 or thumb.suffix.lower() not in ('.jpg', '.jpeg'):
        up = thumb.with_name(thumb.stem + '_yt.jpg'); q = 90
        im = Image.open(thumb).convert('RGB')
        while True:
            im.save(up, quality=q)
            if up.stat().st_size < 1_900_000 or q < 50: break
            q -= 10
    err = ''
    for k in range(3):
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(up), mimetype='image/jpeg')).execute()
            THUMBS[vid] = 'ok'; print('  thumbnail set', vid); return True
        except Exception as e:
            err = str(e)[:300]; print('  thumbnail error', vid, err); time.sleep(15)
    THUMBS[vid] = 'error: ' + err; return False

def add_to_playlist(yt, vid, name=None):
    name = name or CFG['channel']['playlist_name']
    pls = yt.playlists().list(part='snippet', mine=True, maxResults=50).execute().get('items', [])
    pid = next((p['id'] for p in pls if p['snippet']['title'] == name), None)
    if not pid:
        pid = yt.playlists().insert(part='snippet,status', body={'snippet': {'title': name}, 'status': {'privacyStatus': 'public'}}).execute()['id']
    yt.playlistItems().insert(part='snippet', body={'snippet': {'playlistId': pid, 'resourceId': {'kind': 'youtube#video', 'videoId': vid}}}).execute()

def pin_comment_text(yt, vid, text):
    # API can post a comment as the channel; pinning must be done in Studio (API has no pin endpoint)
    yt.commentThreads().insert(part='snippet', body={'snippet': {'videoId': vid, 'topLevelComment': {'snippet': {'textOriginal': text}}}}).execute()
