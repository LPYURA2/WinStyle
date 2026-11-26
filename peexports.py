"""Static DLL export inspection; no binding, loading or execution."""
import json
import sys
from pecheck import Image, MAX_FILE, Rejected, Unsupported, require, support

MAX_EXPORTS = 65536


def inspect_dll(raw):
    require(type(raw) is bytes, 'immutable input required')
    img = Image(raw, allow_dll=True)
    support(img.is_dll, 'not DLL')
    r, z = img.directory(0)
    report = img.report()
    report['image_kind'] = 'DLL'
    report['exports'] = []
    report['export_dll_name'] = None
    if not z:
        return report
    require(z >= 40, 'export header truncated')
    _, _, _, _, name, base, nf, nn, eat, names, ords = img.unpack('<IIHHIIIIIII', img.rva(r, 40))
    require(nf <= MAX_EXPORTS and nn <= MAX_EXPORTS, 'export item limit')
    require(base + nf <= 2**32, 'export ordinal overflow')
    require(name != 0, 'missing DLL export name')
    report['export_dll_name'] = img.string(name)
    def table(ptr, count, width):
        if not count:
            return None
        require(ptr != 0, 'missing export table')
        return img.rva(ptr, count * width)
    e = table(eat, nf, 4)
    n = table(names, nn, 4)
    o = table(ords, nn, 2)
    require(not nn or nf, 'names without functions')
    entries = []
    for i in range(nf):
        target = img.u32(e + 4*i)
        if not target:
            entries.append(None)
            continue
        item = {'ordinal': base+i, 'names': [], 'rva': target, 'forwarder': None}
        if r <= target < r+z:
            value = img.string(target)
            require(target + len(value) + 1 <= r+z, 'forwarder outside export directory')
            module, sep, symbol = value.rpartition('.')
            require(sep and module and symbol, 'invalid forwarder')
            if symbol.startswith('#'):
                digits = symbol[1:]
                require(digits.isascii() and digits.isdigit() and len(digits) <= 10 and int(digits) <= 0xffffffff, 'invalid forwarder ordinal')
            item['forwarder'] = value
        else:
            img.section(target, 1)  # exported data is permitted; no execution approval
        entries.append(item)
    previous = None
    for i in range(nn):
        symbol = img.string(img.u32(n+4*i))
        idx = img.u16(o+2*i)
        require(idx < nf and entries[idx] is not None, 'export name ordinal')
        require(previous is None or previous < symbol, 'export names not strictly sorted')
        previous = symbol
        entries[idx]['names'].append(symbol)
    report['exports'] = [x for x in entries if x is not None]
    report['directories_not_deeply_validated'] = [x for x in img.unchecked if x != 0]
    return report


def main():
    if len(sys.argv) != 2:
        return 2
    try:
        with open(sys.argv[1], 'rb') as f:
            raw = f.read(MAX_FILE+1)
        print(json.dumps(inspect_dll(raw), indent=2))
        return 0
    except Unsupported as e:
        print(json.dumps({'status':'UNSUPPORTED_PROFILE','reason':str(e),'execution_allowed':False}))
        return 3
    except (Rejected, OSError) as e:
        print(json.dumps({'status':'REJECTED','reason':str(e),'execution_allowed':False}))
        return 1

if __name__ == '__main__':
    sys.exit(main())
