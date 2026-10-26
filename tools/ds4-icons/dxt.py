"""Small DXT5 (BC3) encoder for icon art."""
import struct

def _565(c):
    r, g, b = c
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)

def _un565(v):
    return (((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31)

def _alpha_block(alphas):
    a0, a1 = max(alphas), min(alphas)
    if a0 == a1:
        return bytes([a0, a1]) + bytes(6)
    pal = [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
    bits = 0
    for i, a in enumerate(alphas):
        j = min(range(8), key=lambda k: abs(pal[k] - a))
        bits |= j << (3 * i)
    return bytes([a0, a1]) + bits.to_bytes(6, 'little')

def _color_block(cols, weights):
    pts = [c for c, w in zip(cols, weights) if w > 0] or cols
    # principal axis by the extreme pair along luminance-weighted spread
    mean = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
    axis = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    # sign of covariance with the widest channel
    k = max(range(3), key=lambda i: axis[i])
    for i in range(3):
        if i != k and sum((p[i] - mean[i]) * (p[k] - mean[k]) for p in pts) < 0:
            axis[i] = -axis[i]
    proj = [sum((p[i] - mean[i]) * axis[i] for i in range(3)) for p in pts]
    hi = pts[max(range(len(pts)), key=lambda i: proj[i])]
    lo = pts[min(range(len(pts)), key=lambda i: proj[i])]
    c0, c1 = _565(hi), _565(lo)
    if c0 < c1: c0, c1 = c1, c0
    if c0 == c1:
        return struct.pack('<HHI', c0, c1, 0)
    p0, p1 = _un565(c0), _un565(c1)
    pal = [p0, p1, tuple((2 * a + b) // 3 for a, b in zip(p0, p1)), tuple((a + 2 * b) // 3 for a, b in zip(p0, p1))]
    bits = 0
    for i, c in enumerate(cols):
        j = min(range(4), key=lambda q: sum((pal[q][t] - c[t]) ** 2 for t in range(3)))
        bits |= j << (2 * i)
    return struct.pack('<HHI', c0, c1, bits)

def encode_dxt5(rgba, w, h):
    """rgba: bytes of w*h*4. Returns linear little-endian DXT5 blocks."""
    out = bytearray()
    for by in range(0, h, 4):
        for bx in range(0, w, 4):
            cols, al = [], []
            for y in range(4):
                for x in range(4):
                    xx, yy = min(w - 1, bx + x), min(h - 1, by + y)
                    o = (yy * w + xx) * 4
                    cols.append(tuple(rgba[o:o + 3])); al.append(rgba[o + 3])
            out += _alpha_block(al) + _color_block(cols, al)
    return bytes(out)
