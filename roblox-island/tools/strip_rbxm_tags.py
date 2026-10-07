"""Drop the (empty) Tags property chunks from a binary .rbxm so Lune's rbx-dom can read it.

    python3 -I tools/strip_rbxm_tags.py in.rbxm out.rbxm
"""
import struct, sys
def lz4(src, n):
    out = bytearray(); i = 0
    while i < len(src):
        t = src[i]; i += 1
        l = t >> 4
        if l == 15:
            while True:
                b = src[i]; i += 1; l += b
                if b != 255: break
        out += src[i:i+l]; i += l
        if i >= len(src): break
        off = src[i] | src[i+1] << 8; i += 2
        m = t & 15
        if m == 15:
            while True:
                b = src[i]; i += 1; m += b
                if b != 255: break
        m += 4
        for _ in range(m): out.append(out[-off])
    assert len(out) == n
    return bytes(out)
data = open(sys.argv[1], 'rb').read()
out = bytearray(data[:32]); p = 32
while p < len(data):
    name = data[p:p+4]; cl, ul = struct.unpack('<II', data[p+4:p+12]); p += 16
    raw = data[p:p+(cl or ul)]; p += cl or ul
    body = lz4(raw, ul) if cl else raw
    if name == b'PROP':
        nl = struct.unpack('<I', body[4:8])[0]; pn = body[8:8+nl]
        if pn in (b'Tags',):
            print('dropped Tags for class', struct.unpack('<I', body[:4])[0]); continue
    out += name + struct.pack('<III', 0, len(body), 0) + body
    if name == b'END\0': break
open(sys.argv[2], 'wb').write(out)
