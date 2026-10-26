"""Draws the PlayStation replacements for the Xbox button images of the
menu/HUD Flash movies (game\\Naruto_clip.SRA) from Kenney's Input Prompts (CC0).

Each replacement is drawn into the bounding box of the original image's
visible pixels and saved as a complete DDS (DXT5, same size and header as
the original), so the output holds only Kenney-based art.

    python compose_clip.py <classes.json> <originals dir> <kenney "PlayStation Series/Double" dir> <out dir>
"""
import hashlib, json, os, struct, sys, zipfile
from PIL import Image, ImageDraw, ImageFilter, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dxt import encode_dxt5

FACE = {'A': 'cross', 'B': 'circle', 'X': 'square', 'Y': 'triangle',
        'gA': 'cross', 'gX': 'square', 'gY': 'triangle'}
WHITE = {'LB': 'playstation_trigger_l1', 'RB': 'playstation_trigger_r1',
         'LT': 'playstation_trigger_l2', 'RT': 'playstation_trigger_r2',
         'L': 'playstation_stick_l', 'R': 'playstation_stick_r',
         'LS': 'playstation_button_l3', 'RS': 'playstation_button_r3',
         'BACK': 'playstation4_touchpad'}

def decode_dxt5(d, w, h):
    out = bytearray(w * h * 4)
    def c565(v): return (((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31)
    bw = (w + 3) // 4
    for by in range((h + 3) // 4):
        for bx in range(bw):
            o = (by * bw + bx) * 16
            a0, a1 = d[o], d[o + 1]; ab = int.from_bytes(d[o + 2:o + 8], 'little')
            ap = [a0, a1] + ([((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)] if a0 > a1 else
                             [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255])
            c0, c1, cb = struct.unpack_from('<HHI', d, o + 8)
            p0, p1 = c565(c0), c565(c1)
            cp = [p0, p1, tuple((2 * a + b) // 3 for a, b in zip(p0, p1)), tuple((a + 2 * b) // 3 for a, b in zip(p0, p1))]
            for i in range(16):
                x, y = bx * 4 + i % 4, by * 4 + i // 4
                if x < w and y < h:
                    q = (y * w + x) * 4
                    out[q:q + 3] = bytes(cp[(cb >> (2 * i)) & 3]); out[q + 3] = ap[(ab >> (3 * i)) & 7]
    return bytes(out)

def face_button(kenney, name, size, grey):
    big = 256
    im = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, big - 7, big - 7), fill=(28, 28, 32, 255), outline=(150, 150, 158, 255), width=10)
    sym = Image.open(os.path.join(kenney, f'playstation_button_color_{name}_outline.png')).convert('RGBA')
    im.alpha_composite(sym.resize((big, big), Image.LANCZOS))
    if grey:
        a = im.split()[3]
        g = ImageOps.grayscale(im).point(lambda v: v * 3 // 4)
        im = Image.merge('RGBA', (g, g, g, a))
    return im.resize((size, size), Image.LANCZOS)

def white_icon(kenney, name, box_w, box_h):
    im = Image.open(os.path.join(kenney, name + '.png')).convert('RGBA')
    im = im.crop(im.getbbox())
    w, h = im.size; pad = max(w, h) // 12
    canvas = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    canvas.alpha_composite(im, (pad, pad))
    alpha = canvas.split()[3]
    # Dark backing: the icon's silhouette with its letter holes filled, grown a little.
    mask = alpha.point(lambda v: 255 if v > 40 else 0)
    flood = mask.copy(); ImageDraw.floodfill(flood, (0, 0), 128)
    solid = flood.point(lambda v: 0 if v == 128 else 255).filter(ImageFilter.MaxFilter(2 * (pad // 2) + 1))
    back = Image.new('RGBA', canvas.size, (24, 24, 28, 255)); back.putalpha(solid)
    back.alpha_composite(canvas)
    cw, ch = back.size
    s = min(box_w / cw, box_h / ch)
    return back.resize((max(1, round(cw * s)), max(1, round(ch * s))), Image.LANCZOS)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
PILL = {'LB': 'L1', 'RB': 'R1', 'BACK': None}

def pill(label, w, h):
    """A white rounded pill like the game's LB/RB/BACK art, holding a label
    (or, for BACK, a small touchpad)."""
    from PIL import ImageFont
    k = 8
    im = Image.new('RGBA', (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = h * k // 2
    d.rounded_rectangle((k, k, w * k - k - 1, h * k - k - 1), radius=r - k, fill=(245, 245, 245, 255),
                        outline=(40, 40, 46, 255), width=max(k, h * k // 10))
    if label:
        font = ImageFont.truetype(FONT, int(h * k * 0.62))
        tb = d.textbbox((0, 0), label, font=font)
        d.text(((w * k - (tb[2] - tb[0])) // 2 - tb[0], (h * k - (tb[3] - tb[1])) // 2 - tb[1]), label,
               font=font, fill=(28, 28, 32, 255))
    else:
        pw, ph = int(h * k * 1.1), int(h * k * 0.5)
        x0, y0 = (w * k - pw) // 2, (h * k - ph) // 2
        d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=ph // 4, fill=(28, 28, 32, 255))
    return im.resize((w, h), Image.LANCZOS)

def main(classes_path, orig_dir, kenney, out_dir):
    classes = json.load(open(classes_path))
    os.makedirs(out_dir, exist_ok=True)
    manifest = {}
    z = zipfile.ZipFile(os.path.join(out_dir, 'clip_icons.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=9)
    for key, cls in sorted(classes.items()):
        k = int(key, 16)
        dds = open(os.path.join(orig_dir, '%08x.dds' % k), 'rb').read()
        h, w = struct.unpack_from('<II', dds, 12)
        assert dds[84:88] == b'DXT5' and len(dds) == 128 + w * h, key
        orig = Image.frombytes('RGBA', (w, h), decode_dxt5(dds[128:], w, h))
        bb = orig.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, w, h)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        if cls in FACE:
            side = min(bw, bh)
            icon = face_button(kenney, FACE[cls], side, cls.startswith('g'))
        elif cls in PILL:
            icon = pill(PILL[cls], bw, bh)
        else:
            icon = white_icon(kenney, WHITE[cls], bw, bh)
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        out.alpha_composite(icon, (bb[0] + (bw - icon.width) // 2, bb[1] + (bh - icon.height) // 2))
        new = dds[:128] + encode_dxt5(out.tobytes(), w, h)
        z.writestr('%08x.dds' % k, new)
        manifest['%08x' % k] = {'class': cls, 'original': hashlib.sha256(dds).hexdigest(),
                                'patched': hashlib.sha256(new).hexdigest(), 'size': len(dds)}
    z.close()
    json.dump(manifest, open(os.path.join(out_dir, 'clip_manifest.json'), 'w'), indent=1, sort_keys=True)
    print(len(manifest), 'images')

if __name__ == '__main__':
    main(*sys.argv[1:5])
