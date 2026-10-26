"""DualShock 4 button icons for Naruto: Rise of a Ninja (PC port).

Swaps the Xbox button icons in game\naruto.bf (the font's A/B/X/Y, shoulder
and stick glyphs, and the 64x64 HUD buttons) for PlayStation ones. The first
run copies naruto.bf to naruto.bf.ds4bak; "restore" puts that copy back.

    python ds4_icons.py install  "<game folder>"
    python ds4_icons.py restore  "<game folder>"
    python ds4_icons.py status   "<game folder>"
    python ds4_icons.py extract  "<game folder>" <out dir>   (originals, for compose_icons.py)

<game folder> is the folder with narutorise.exe (or its "game" subfolder).
A patched bigfile entry is written back in its own place (the icons compress
better than the Xbox ones, so it fits), with only the changed 128 KB chunks
compressed again; its size in the file table is updated. Nothing moves.
Pure Python 3, no packages needed.
"""
import hashlib
import json
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 0x20000
MAGIC = 0xEEFFC099
INFO_STRIDE = 0x7C


def lzo1x(src):
    ip = 0; out = bytearray(); n = len(src); state = 0
    def cm(d, L):
        s = len(out) - d
        if d >= L: out.extend(out[s:s + L])
        else:
            while L > 0:
                c = min(d, L); out.extend(out[s:s + c]); L -= c
    t = src[0]
    if t > 17:
        t -= 17; ip = 1; out += src[ip:ip + t]; ip += t; state = 4 if t >= 4 else t
        t = src[ip]; ip += 1
        if t < 16 and state == 4:
            d = 1 + 0x800 + (t >> 2) + (src[ip] << 2); ip += 1; cm(d, 3); state = t & 3
            out += src[ip:ip + state]; ip += state
        else:
            ip -= 1
    while ip < n:
        t = src[ip]; ip += 1
        if t < 16:
            if state == 0:
                if t == 0:
                    while src[ip] == 0: t += 255; ip += 1
                    t += 15 + src[ip]; ip += 1
                t += 3; out += src[ip:ip + t]; ip += t; state = 4; continue
            elif state == 4:
                d = 1 + 0x800 + (t >> 2) + (src[ip] << 2); ip += 1; L = 3
            else:
                d = 1 + (t >> 2) + (src[ip] << 2); ip += 1; L = 2
        elif t >= 64:
            d = 1 + ((t >> 2) & 7) + (src[ip] << 3); ip += 1; L = (t >> 5) + 1
        elif t >= 32:
            L = t & 31
            if L == 0:
                while src[ip] == 0: L += 255; ip += 1
                L += 31 + src[ip]; ip += 1
            L += 2; d = 1 + ((src[ip] | (src[ip + 1] << 8)) >> 2); ip += 2; t = src[ip - 2]
        else:
            d = (t & 8) << 11; L = t & 7
            if L == 0:
                while src[ip] == 0: L += 255; ip += 1
                L += 7 + src[ip]; ip += 1
            L += 2; v = src[ip] | (src[ip + 1] << 8); ip += 2; d += v >> 2; t = src[ip - 2]
            if d == 0: return bytes(out)
            d += 0x4000
        cm(d, L); s = t & 3; out += src[ip:ip + s]; ip += s; state = s
    return bytes(out)

def unpack(b):
    tot = struct.unpack_from('<I', b, 0)[0]; p = 4; out = bytearray()
    while p < 4 + tot:
        un, cs = struct.unpack_from('<II', b, p); p += 8
        if un == 0 and cs == 0: break
        out += b[p:p + cs] if cs == un else lzo1x(b[p:p + cs]); p += cs
    return bytes(out)


def lzo1x_compress(src):
    """Greedy LZO1X compressor: M2/M3/M4 matches and literal runs, the
    instructions the game's decompressor reads."""
    n = len(src)
    out = bytearray()
    last_match_at = -1   # index in out of the byte carrying the next lits count
    lit_start = 0
    ip = 0
    table = {}
    def emit_literals(end):
        nonlocal last_match_at
        L = end - lit_start
        if L == 0:
            return
        if last_match_at < 0 and not out:
            if L <= 238:
                out.append(17 + L)
            else:
                rest = L - 3 - 15; z = (rest - 1) // 255
                out.append(0); out.extend(bytes(z)); out.append(rest - 255 * z)
        elif L <= 3:
            out[last_match_at] |= L
        elif L <= 18:
            out.append(L - 3)
        else:
            rest = L - 3 - 15; z = (rest - 1) // 255
            out.append(0); out.extend(bytes(z)); out.append(rest - 255 * z)
        out.extend(src[lit_start:end])
    while ip + 3 <= n:
        key = src[ip:ip + 3]
        cand = table.get(key)
        table[key] = ip
        if cand is not None and ip - cand <= 0xBFFF:
            d = ip - cand
            m = 3
            lim = n - ip
            while m < lim and src[cand + m] == src[ip + m]:
                m += 1
            if m < 4 and d > 2048:
                ip += 1; continue
            # Literal runs of 1..3 bytes need a previous match to carry them.
            pending = ip - lit_start
            if 1 <= pending <= 3 and last_match_at < 0 and out:
                ip += 1; continue
            emit_literals(ip)
            if m <= 8 and d <= 2048:
                out.append(((m - 1) << 5) | (((d - 1) & 7) << 2))
                last_match_at = len(out) - 1
                out.append((d - 1) >> 3)
            elif d <= 16384:
                if m - 2 <= 31:
                    out.append(32 | (m - 2))
                else:
                    rest = m - 2 - 31; z = (rest - 1) // 255
                    out.append(32); out.extend(bytes(z)); out.append(rest - 255 * z)
                v = (d - 1) << 2
                last_match_at = len(out)
                out.append(v & 0xFF); out.append(v >> 8)
            else:
                dd = d - 0x4000
                if m - 2 <= 7:
                    out.append(16 | ((dd >> 11) & 8) | (m - 2))
                else:
                    rest = m - 2 - 7; z = (rest - 1) // 255
                    out.append(16 | ((dd >> 11) & 8)); out.extend(bytes(z)); out.append(rest - 255 * z)
                v = (dd & 0x3FFF) << 2
                last_match_at = len(out)
                out.append(v & 0xFF); out.append(v >> 8)
            for k in range(ip + 1, min(ip + m, n - 2)):
                table[src[k:k + 3]] = k
            ip += m
            lit_start = ip
        else:
            ip += 1
    emit_literals(n)
    out += b'\x11\x00\x00'
    return bytes(out)


def chunks(raw):
    """(uncompressed size, stored bytes) of each chunk of a bigfile entry."""
    # [size][chunk: uncompressed size, stored size, bytes]...[0, 0]; size
    # counts everything after it but the last 4 bytes of the end marker.
    p = 4
    out = []
    while True:
        un, cs = struct.unpack_from('<II', raw, p)
        p += 8
        if un == 0 and cs == 0:
            out.append((0, b''))
            break
        out.append((un, raw[p:p + cs]))
        p += cs
    assert p == len(raw), 'unexpected entry size'
    return out


def unpack_chunks(chs):
    out = bytearray()
    for un, data in chs:
        if un:
            out += data if len(data) == un else lzo1x(data)
    return bytes(out)


def repack(chs, old, new):
    """The entry with the chunks whose bytes changed stored again."""
    body = bytearray()
    pos = 0
    for un, data in chs:
        if un == 0:
            body += struct.pack('<II', 0, 0)
            continue
        if old[pos:pos + un] != new[pos:pos + un]:
            data = lzo1x_compress(new[pos:pos + un])
            assert lzo1x(data) == new[pos:pos + un]
            if len(data) >= un:
                raise ValueError('a patched chunk does not compress')
        body += struct.pack('<II', un, len(data)) + data
        pos += un
    assert pos == len(new)
    return struct.pack('<I', len(body) - 4) + bytes(body)


def resources(u):
    p = 0
    while p + 12 <= len(u):
        size, mark, key = struct.unpack_from('<III', u, p)
        if mark != MAGIC:
            return
        yield key, p + 12, size
        p += 12 + size


def sha(b):
    return hashlib.sha256(b).hexdigest()


def find_bf(folder):
    for path in (os.path.join(folder, 'game', 'naruto.bf'), os.path.join(folder, 'naruto.bf')):
        if os.path.isfile(path):
            return path
    sys.exit(f'naruto.bf not found in {folder} or {folder}\\game')


def load_patch():
    """key -> (original sha, patched sha, size, function original -> patched)."""
    manifest = json.load(open(os.path.join(HERE, 'data', 'manifest.json')))
    patch = {}
    for key, entry in manifest.items():
        rects = [(r, open(os.path.join(HERE, 'data', r['file']), 'rb').read()) for r in entry['rects']]

        def apply(original, rects=rects, width=entry['width'], want=entry['patched']):
            out = bytearray(original)
            for r, data in rects:
                for row in range(r['h']):
                    at = 0x24 + 18 + ((r['y'] + row) * width + r['x']) * 4
                    out[at:at + r['w'] * 4] = data[row * r['w'] * 4:(row + 1) * r['w'] * 4]
            out = bytes(out)
            if sha(out) != want:
                raise ValueError('patched texture does not match')
            return out
        patch[int(key, 16)] = (entry['original'], entry['patched'], entry['size'], apply)
    return patch


def read_tables(f):
    f.seek(0)
    head = f.read(0x44)
    if head[:4] != b'BIG\0':
        sys.exit('naruto.bf is not a Jade bigfile')
    count = struct.unpack_from('<I', head, 8)[0]
    max_files, fat_off = struct.unpack_from('<I', head, 0x20)[0], struct.unpack_from('<I', head, 0x34)[0]
    f.seek(fat_off)
    fat = [struct.unpack_from('<II', f.read(8)) for _ in range(count)]
    info_off = fat_off + 8 * max_files
    return fat_off, info_off, fat


def scan(f, fat, patch, total):
    """Yields (index, key, offset, raw entry, chunks, unpacked, state) for
    each entry holding a patched texture."""
    order = sorted(range(len(fat)), key=lambda i: fat[i][0])
    for n, i in enumerate(order):
        off, key = fat[i]
        size = struct.unpack('<I', (f.seek(off), f.read(4))[1])[0]
        f.seek(off)
        raw = f.read(size + 8)
        try:
            chs = chunks(raw)
            u = unpack_chunks(chs)
        except Exception:
            continue
        found = []
        for k, p, s in resources(u):
            if k in patch and s == patch[k][2]:
                found.append((k, p, s))
        if found:
            yield i, key, off, raw, chs, u, found
        if n % 100 == 0:
            print(f'  scanned {n}/{len(fat)} entries', flush=True)


def exe_folder(folder):
    for path in (folder, os.path.dirname(os.path.abspath(folder))):
        if os.path.isfile(os.path.join(path, 'narutorise.exe')):
            return path
    return None


def set_marker(folder, installed):
    """ds4_icons.installed next to narutorise.exe tells the DS4 prompts code
    mod to keep the (now PlayStation) icons instead of writing button names."""
    exe = exe_folder(folder)
    if not exe:
        return
    marker = os.path.join(exe, 'ds4_icons.installed')
    if installed:
        open(marker, 'w').write('DualShock 4 icon pack installed in naruto.bf\n')
    elif os.path.exists(marker):
        os.remove(marker)


def install(folder):
    bf = find_bf(folder)
    backup = bf + '.ds4bak'
    patch = load_patch()
    if not os.path.exists(backup):
        print(f'Backing up {bf} -> {backup} ...', flush=True)
        shutil.copyfile(bf, backup + '.part')
        os.replace(backup + '.part', backup)
    changed = 0
    with open(bf, 'r+b') as f:
        fat_off, info_off, fat = read_tables(f)
        total = os.path.getsize(bf)
        for i, key, off, raw, chs, u, found in list(scan(f, fat, patch, total)):
            new = bytearray(u)
            todo = 0
            for k, p, s in found:
                original, patched, _, apply = patch[k]
                now = sha(u[p:p + s])
                if now == patched:
                    continue
                if now != original:
                    print(f'  {key:08x}: texture {k:08x} is not the one this mod expects, left alone')
                    continue
                new[p:p + s] = apply(u[p:p + s])
                todo += 1
            if not todo:
                continue
            blob = repack(chs, u, bytes(new))
            assert unpack_chunks(chunks(blob)) == bytes(new)
            if len(blob) > len(raw):
                print(f'  {key:08x}: the patched entry is larger than the original, left alone')
                continue
            f.seek(off)
            f.write(blob + bytes(len(raw) - len(blob)))
            f.seek(info_off + INFO_STRIDE * i)
            f.write(blob[:4])
            changed += 1
            print(f'  patched entry {key:08x} ({todo} textures)', flush=True)
    set_marker(folder, True)
    print(f'Done: {changed} bigfile entries patched.' if changed else 'Nothing to do: the icons are already installed.')


def restore(folder):
    bf = find_bf(folder)
    backup = bf + '.ds4bak'
    if not os.path.exists(backup):
        sys.exit(f'No backup at {backup}')
    shutil.copyfile(backup, bf)
    set_marker(folder, False)
    print(f'Restored {bf} from {backup}.')


def status(folder):
    bf = find_bf(folder)
    patch = load_patch()
    counts = {'original': 0, 'patched': 0, 'other': 0}
    with open(bf, 'rb') as f:
        _, _, fat = read_tables(f)
        for i, key, off, raw, chs, u, found in scan(f, fat, patch, os.path.getsize(bf)):
            for k, p, s in found:
                now = sha(u[p:p + s])
                counts['patched' if now == patch[k][1] else 'original' if now == patch[k][0] else 'other'] += 1
    print(f'Textures: {counts["patched"]} PlayStation, {counts["original"]} Xbox, {counts["other"]} unknown.')
    print('Backup:', 'yes' if os.path.exists(bf + '.ds4bak') else 'no')


def extract(folder, out_dir):
    bf = find_bf(folder)
    patch = load_patch()
    os.makedirs(out_dir, exist_ok=True)
    left = set(patch)
    with open(bf, 'rb') as f:
        _, _, fat = read_tables(f)
        for i, key, off, raw, chs, u, found in scan(f, fat, patch, os.path.getsize(bf)):
            for k, p, s in found:
                if k in left and sha(u[p:p + s]) == patch[k][0]:
                    open(os.path.join(out_dir, f'{k:08x}.bin'), 'wb').write(u[p:p + s])
                    left.discard(k)
            if not left:
                break
    print('Extracted the original textures.' if not left else f'Not found: {sorted(map(hex, left))}')


if __name__ == '__main__':
    commands = {'install': (install, 3), 'restore': (restore, 3), 'status': (status, 3),
                'extract': (extract, 4)}
    if len(sys.argv) < 2 or sys.argv[1] not in commands or len(sys.argv) != commands[sys.argv[1]][1]:
        sys.exit(__doc__)
    commands[sys.argv[1]][0](*sys.argv[2:])
