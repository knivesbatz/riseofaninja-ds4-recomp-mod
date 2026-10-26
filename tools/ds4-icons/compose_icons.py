"""Builds the DualShock 4 icon textures from Kenney's Input Prompts (CC0).

Reads the game's original font atlas (Jade resource 0x2f00e652) and the four
64x64 HUD buttons, draws the PlayStation icons over the Xbox ones and writes
the icons as raw pixel rectangles plus manifest.json, which ds4_icons.py
pastes into the player's own textures (no game art is redistributed).

    python compose_icons.py <originals dir> <kenney "PlayStation Series/Double" dir> <out dir>
"""
import hashlib
import json
import os
import struct
import sys

from PIL import Image, ImageDraw

ATLAS_KEY = 0x2F00E652
HUD_KEYS = {0x1900001F: 'cross', 0x19000024: 'circle', 0x1900004E: 'square', 0x1900004F: 'triangle'}

# Font glyph -> (icon, drawn box in the top-down atlas: x0, y0, size).
# The boxes are the original glyphs' own, bottom-aligned on the text baseline.
GLYPHS = {
    0xB9: ('cross', 46, 105, 22),     # <a>
    0xBA: ('circle', 71, 105, 22),    # <b>
    0xBB: ('square', 96, 105, 22),    # <x>
    0xBC: ('triangle', 121, 105, 22),  # <y>
    0xBD: ('l2', 147, 107, 19),       # shoulder L: <lt> (and <lb> without the code mod)
    0xBE: ('r2', 173, 107, 19),       # shoulder R: <rt> (and <rb> without the code mod)
    0xB5: ('stick_l', 197, 106, 20),  # left stick
    0xB6: ('stick_r', 222, 106, 20),  # right stick
    # The French/Spanish/Italian shoulder glyphs (G, I, D, sx, dx). The code
    # mod points <lb>/<rb> of English texts at 0x8B/0x8E.
    0x8B: ('l1', 48, 140, 17),
    0x8D: ('l1', 73, 140, 17),
    0x8E: ('r1', 98, 140, 17),
    0x8F: ('l1', 124, 140, 17),
    0x90: ('r1', 149, 140, 17),
}
# Cells (top-down) cleared before drawing, from the font's FONTDESC.
CELLS = {
    0xB9: (45, 104, 70, 129), 0xBA: (70, 104, 95, 129), 0xBB: (95, 104, 120, 129),
    0xBC: (120, 104, 145, 129), 0xBD: (145, 107, 170, 129), 0xBE: (170, 107, 195, 129),
    0xB5: (195, 104, 219, 129), 0xB6: (219, 104, 245, 129), 0x8B: (46, 138, 69, 159),
    0x8D: (71, 138, 94, 159), 0x8E: (95, 138, 119, 159), 0x8F: (120, 138, 144, 159),
    0x90: (145, 138, 168, 159),
}


def face_button(kenney, name, size):
    """A DualShock 4 face button: dark cap, coloured symbol."""
    big = 256
    im = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, big - 7, big - 7), fill=(28, 28, 32, 255), outline=(150, 150, 158, 255), width=10)
    sym = Image.open(os.path.join(kenney, f'playstation_button_color_{name}_outline.png')).convert('RGBA')
    sym = sym.resize((big, big), Image.LANCZOS)
    im.alpha_composite(sym)
    return im.resize((size, size), Image.LANCZOS)


def kenney_icon(kenney, name, size):
    files = {
        'l1': 'playstation_trigger_l1', 'r1': 'playstation_trigger_r1',
        'l2': 'playstation_trigger_l2', 'r2': 'playstation_trigger_r2',
        'stick_l': 'playstation_stick_l', 'stick_r': 'playstation_stick_r',
    }
    im = Image.open(os.path.join(kenney, files[name] + '.png')).convert('RGBA')
    im = im.crop(im.getbbox())
    w, h = im.size
    side = max(w, h)
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(im, ((side - w) // 2, side - h))
    # A dark rim so the white icons read on bright backgrounds, like the originals.
    rim = Image.new('RGBA', (side + 16, side + 16), (0, 0, 0, 0))
    alpha = sq.split()[3]
    shadow = Image.new('RGBA', sq.size, (20, 20, 24, 255))
    for dx in (0, 8, 16):
        for dy in (0, 8, 16):
            rim.paste(shadow, (dx, dy), alpha)
    rim.alpha_composite(sq, (8, 8))
    return rim.resize((size, size), Image.LANCZOS)


def icon(kenney, name, size):
    if name in ('cross', 'circle', 'square', 'triangle'):
        return face_button(kenney, name, size)
    return kenney_icon(kenney, name, size)


def read_tga_resource(blob):
    # Jade texture: 0x24-byte header, then an 18-byte TGA header and BGRA pixels.
    t = 0x24
    w, h = struct.unpack_from('<HH', blob, t + 12)
    bpp, desc = blob[t + 16], blob[t + 17]
    assert bpp == 32, bpp
    px = blob[t + 18:t + 18 + w * h * 4]
    im = Image.frombytes('RGBA', (w, h), px, 'raw', 'BGRA')
    flip = not desc & 0x20
    if flip:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im, flip


def write_tga_resource(blob, im, flip):
    if flip:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    px = im.tobytes('raw', 'BGRA')
    t = 0x24 + 18
    out = blob[:t] + px + blob[t + len(px):]
    assert len(out) == len(blob)
    return out


def rects_of(blob, new_blob, width, boxes, key, out_dir):
    """The changed pixels as raw BGRA rectangles in the stored (file) row
    order, so the installer rebuilds the texture from the player's own copy."""
    height = (len(blob) - 0x24 - 18) // (width * 4)
    rects = []
    for n, (x0, y0, x1, y1) in enumerate(boxes):
        # Top-down box -> stored rows (bottom-up).
        sy0, sy1 = height - y1, height - y0
        data = bytearray()
        for y in range(sy0, sy1):
            row = 0x24 + 18 + (y * width + x0) * 4
            data += new_blob[row:row + (x1 - x0) * 4]
        name = f'{key:08x}_{n:02d}.raw'
        open(os.path.join(out_dir, name), 'wb').write(data)
        rects.append({'x': x0, 'y': sy0, 'w': x1 - x0, 'h': sy1 - sy0, 'file': name})
    return rects


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main(orig_dir, kenney, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = {}
    blob = open(os.path.join(orig_dir, f'{ATLAS_KEY:08x}.bin'), 'rb').read()
    atlas, flip = read_tga_resource(blob)
    for glyph, (name, x, y, size) in GLYPHS.items():
        x0, y0, x1, y1 = CELLS[glyph]
        atlas.paste((0, 0, 0, 0), (x0, y0, x1, y1))
        atlas.alpha_composite(icon(kenney, name, size), (x, y))
    new_blob = write_tga_resource(blob, atlas, flip)
    manifest[f'{ATLAS_KEY:08x}'] = {
        'original': sha256(blob), 'patched': sha256(new_blob), 'size': len(blob),
        'width': atlas.size[0],
        'rects': rects_of(blob, new_blob, atlas.size[0], CELLS.values(), ATLAS_KEY, out_dir)}
    for key, name in HUD_KEYS.items():
        blob = open(os.path.join(orig_dir, f'{key:08x}.bin'), 'rb').read()
        im, flip = read_tga_resource(blob)
        new = Image.new('RGBA', im.size, (0, 0, 0, 0))
        new.alpha_composite(face_button(kenney, name, im.size[0] - 2), (1, 1))
        new_blob = write_tga_resource(blob, new, flip)
        w, h = im.size
        manifest[f'{key:08x}'] = {
            'original': sha256(blob), 'patched': sha256(new_blob), 'size': len(blob), 'width': w,
            'rects': rects_of(blob, new_blob, w, [(0, 0, w, h)], key, out_dir)}
    with open(os.path.join(out_dir, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)


if __name__ == '__main__':
    main(*sys.argv[1:4])
