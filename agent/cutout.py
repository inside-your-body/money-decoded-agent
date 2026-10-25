"""Cut-out helpers: trim transparent PNGs to their content, detect figures cut by the image edge, keep files small."""
from PIL import Image


def touches_edge(path, side_px=3, frac=0.004):
    """True when opaque pixels touch the top/left/right edge (the figure was cut off by the generator)."""
    im = Image.open(path).convert('RGBA'); a = im.getchannel('A'); w, h = im.size
    def cnt(box):
        return sum(1 for v in a.crop(box).getdata() if v > 40)
    return (cnt((0, 0, w, side_px)) > w * side_px * frac or cnt((0, 0, side_px, h)) > h * side_px * frac
            or cnt((w - side_px, 0, w, h)) > h * side_px * frac)


def trim(src, dst, max_h=900, pad=0.04):
    """Crop to the alpha bounding box (+ small padding), scale to max_h tall. Returns aspect ratio w/h."""
    im = Image.open(src).convert('RGBA')
    bb = im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
    if bb:
        im = im.crop(bb)
    w, h = im.size
    p = int(max(w, h) * pad)
    canvas = Image.new('RGBA', (w + 2 * p, h + 2 * p), (0, 0, 0, 0)); canvas.paste(im, (p, p)); im = canvas
    if im.height > max_h:
        im = im.resize((int(im.width * max_h / im.height), max_h), Image.LANCZOS)
    im.save(dst, optimize=True)
    return round(im.width / im.height, 4)
