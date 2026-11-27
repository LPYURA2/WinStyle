"""WS-02B1: non-executable PE layout model, not a runtime or security approval."""
from dataclasses import dataclass
import struct
from pecheck import Image, require, support

MAX_MODEL = 32 * 1024 * 1024

@dataclass(frozen=True)
class Layout:
    base: int
    data: bytes
    entry_rva: int
    relocations: int
    execution_allowed: bool = False

def model(raw: bytes, base: int | None = None, *, allow_dll: bool = False) -> Layout:
    # Immutable snapshot; validate on every call, do not accept mutable Image metadata.
    require(type(raw) is bytes, 'immutable input required')
    img = Image(raw, allow_dll=allow_dll)
    require(img.headers <= img.size <= MAX_MODEL, 'model size limit')
    base = img.base if base is None else base
    require(type(base) is int and base >= 65536 and base % 65536 == 0
            and base + img.size <= 2**47, 'model base')
    delta = base - img.base
    r, z = img.directory(5)
    support(not delta or (z and img.reloc_count), 'cannot rebase image')
    data = bytearray(img.size)
    data[:img.headers] = raw[:img.headers]
    for s in img.sections:
        if s.raw_size:
            data[s.rva:s.rva+s.raw_size] = raw[s.raw_offset:s.raw_offset+s.raw_size]
    count = 0
    if delta:
        pos = 0
        # Read relocation instructions from the original immutable file, not patched data.
        while pos < z:
            page, n = img.unpack('<II', img.rva(r+pos, 8))
            for j in range(8, n, 2):
                v = img.u16(img.rva(r+pos+j, 2))
                if v >> 12 == 0:
                    continue
                target = page + (v & 4095)
                old = struct.unpack_from('<Q', data, target)[0]
                struct.pack_into('<Q', data, target, (old + delta) & ((1 << 64)-1))
                count += 1
            pos += n
        require(count == img.reloc_count, 'relocation count mismatch')
    return Layout(base, bytes(data), img.entry, count)
