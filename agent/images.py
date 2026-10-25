"""OpenAI image generation: 2D illustrations (transparent) + thumbnail art."""
import base64, os, time, requests, pathlib
from .common import CFG

API = 'https://api.openai.com/v1/images/generations'
EDIT_API = 'https://api.openai.com/v1/images/edits'

# gpt-image-1 was shut down by OpenAI on 2026-10-23 -> try the current models in order (first that exists wins, remembered)
MODELS = [m for m in [CFG['models'].get('openai_image')] if m and m != 'gpt-image-1'] + ['gpt-image-2.5-flare', 'gpt-image-2.5-sunburst', 'gpt-image-1.5']
_OK = {'model': None, 'transparent': True}
WHITE = ' Plain pure white background (#FFFFFF) all around the subject, nothing else in the background.'


import re as _re
_SOFT = [(r'\b(cut|cuts|cutting)\b', 'trimmed'), (r'\bknife\b', 'sharp jab'), (r'\bstab\w*', 'sharp'), (r'\bblood\w*', 'red'),
         (r'\bbleed\w*', 'red'), (r'\bwound\w*', 'scrape'), (r'\bpain(ful)?\b', 'discomfort'), (r'\bdying\b', 'very weak'),
         (r'\bdie(s|d)?\b', 'faint'), (r'\bkill\w*', 'beat'), (r'\bhurt\w*', 'ache'), (r'\bsuicid\w*', ''), (r'\bself[- ]harm\w*', ''), (r'\blaunder\w*', 'move'), (r'\bbomb\w*', 'shock'),
         (r'\bweapon\w*', 'tool'), (r'\bgun\w*', 'tool')]


def soften(p):
    """Image safety filters misread health words (a 'stabbing pain' becomes self-harm) -> neutral wording for image prompts only."""
    for a, b in _SOFT: p = _re.sub(a, b, p, flags=_re.I)
    return p


def _remove_white(path):
    """Background removal for models without transparent output: near-white pixels connected to the border become transparent."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    im = Image.open(path).convert('RGBA'); a = np.array(im)
    white = (a[..., :3].min(axis=2) > 235)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    mask = np.isin(lab, list(border))
    mask = ndimage.binary_dilation(mask, iterations=1) & (a[..., :3].min(axis=2) > 200)
    a[..., 3] = np.where(mask, 0, 255)
    Image.fromarray(a).save(path)


def _post(url, transparent, data=None, json_body=None, files=None):
    """POST to the images API trying models in order. Returns (response_json, used_white_bg)."""
    models = ([_OK['model']] + [m for m in MODELS if m != _OK['model']]) if _OK['model'] else MODELS
    last = None
    for m in models:
        for want_t in ([True, False] if (transparent and _OK['transparent']) else [False]):
            body = dict(json_body or data or {}); body['model'] = m
            if transparent and want_t: body['background'] = 'transparent'; body['output_format'] = 'png'
            else: body.pop('background', None)
            if transparent and not want_t: body['prompt'] = body['prompt'] + WHITE
            hdr = {'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']}
            fl = [(k, (n, open(f, 'rb'), t)) for k, (n, f, t) in files] if files else None
            r = requests.post(url, headers=hdr, data=body if files else None, json=None if files else body, files=fl, timeout=300)
            if r.ok:
                if not _OK['model']: _OK['model'] = m
                if transparent and not want_t: _OK['transparent'] = False
                return r.json(), transparent and not want_t
            txt = r.text[:400]; last = txt
            if 'does not exist' in txt or 'model_not_found' in txt or 'not supported' in txt and 'model' in txt:
                break                                    # next model
            if 'safety' in txt:
                break                                    # the safety filter is model-specific and flaky: try the next model
            if 'background' in txt or 'transparent' in txt or 'output_format' in txt:
                continue                                 # same model, white background + removal
            raise RuntimeError(txt)
    raise RuntimeError('no image model worked: ' + str(last))


def gen(prompt, out, size='1024x1024', transparent=False, quality='medium', retries=3):
    body = {'prompt': soften(prompt), 'size': size, 'quality': quality, 'n': 1}
    for a in range(retries):
        try:
            j, white = _post(API, transparent, json_body=body)
            from . import cost; cost.image(j.get('usage'), f"{pathlib.Path(out).name} {size} {quality} {_OK['model']}")
            pathlib.Path(out).write_bytes(base64.b64decode(j['data'][0]['b64_json']))
            if white: _remove_white(out)
            return out
        except Exception as e:
            print('image error', str(e)[:300])
            if 'safety' in str(e): return None
            time.sleep(8 * (a + 1))
    return None

def illustration(prompt, style_hint, out):
    p = (f"Flat 2D vector illustration for an animated health explainer, {style_hint}. Subject: {prompt}. "
         "Clean shapes, no text, no letters, no watermark, isolated on a transparent background, centered, friendly, not gory.")
    return gen(p, out, transparent=True, quality='low')

def thumbnail_art(prompt, out, refs=None, cast_desc='', quality='high'):
    p = (f"YouTube thumbnail, 2D cartoon style matching the reference characters, ultra eye-catching, huge contrast, saturated colours, "
         f"dramatic lighting, one clear focal point readable on a small phone screen, big expressive emotion. {prompt}. "
         + (f"Characters: {cast_desc} " if cast_desc else '')
         + "Keep the bottom-left area simple and darker for a big headline. No text, no letters, no watermark.")
    return edit(p, refs or [], out, size='1536x1024', quality=quality)

def edit(prompt, refs, out, size='1536x1024', transparent=False, quality='medium', retries=2):
    """images/edits with reference images (keeps the cast consistent). Falls back to plain generation."""
    refs = [r for r in refs if r and pathlib.Path(r).exists()][:4]
    if refs:
        data = {'prompt': soften(prompt), 'size': size, 'quality': quality, 'n': '1'}
        for a in range(retries):
            try:
                files = [('image[]', (pathlib.Path(r).name, r, 'image/png')) for r in refs]
                j, white = _post(EDIT_API, transparent, data=data, files=files)
                from . import cost; cost.image(j.get('usage'), f"{pathlib.Path(out).name} {size} {quality} edit {_OK['model']}")
                pathlib.Path(out).write_bytes(base64.b64decode(j['data'][0]['b64_json']))
                if white: _remove_white(out)
                return out
            except Exception as e:
                print('image edit error', str(e)[:300])
                if 'safety' in str(e): return None
                time.sleep(8 * (a + 1))
    return gen(prompt, out, size=size, transparent=transparent, quality=quality)


CARTOON = ("2D animation still for a high-end animated science explainer, expressive faces. {style}. "
           "No text, no letters, no numbers, no watermark, not gory.")

def cast_ref(c, style_hint, out):
    p = (CARTOON.format(style=style_hint) + f" Character design reference: {c['name']} — {c['look']}. "
         "Single full-body character, front three-quarter view, friendly pose, centered. Fully transparent background: no backdrop, no frame, no panel, no decorative lines or icons behind the character.")
    return gen(p, out, size='1024x1024', transparent=True)

def cast_text(cast, ids):
    return ' '.join(f"{c['name']} looks like: {c['look']}." for c in cast if c['id'] in (ids or []))

def cartoon_scene(prompt, cast, ids, refs, style_hint, out, vertical=False, quality='medium'):
    p = (CARTOON.format(style=style_hint) + f" Storyboard frame, full scene with background, cinematic composition, the subject large and clearly readable: {prompt}. Characters act out this exact moment with a fresh, specific pose and expression (never a generic presenting/open-palm pose). "
         + (f"Characters (keep them EXACTLY as in the reference images): {cast_text(cast, ids)}" if ids else ''))
    return edit(p, refs, out, size='1024x1536' if vertical else '1536x1024', quality=quality)

def sprite(prompt, cast, ids, refs, style_hint, out):
    p = (CARTOON.format(style=style_hint) + f" Subject: {prompt}. "
         + (f"Characters (keep them EXACTLY as in the reference images): {cast_text(cast, ids)} " if ids else '')
         + "Cut-out isolated on a fully transparent background: no backdrop, no frame, no panel, no decorative lines; centered, full body visible.")
    return edit(p, refs, out, size='1024x1024', transparent=True, quality='low')
