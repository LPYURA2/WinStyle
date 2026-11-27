"""Non-executable, transactional IAT model. Addresses are integers, not host pointers."""
from dataclasses import dataclass
import struct
from pecheck import Image, require
from pemap import Layout, model, MAX_MODEL
from peresolve import plan, module_key

MAX_TOTAL_IMAGE = 64 * 1024 * 1024
ROOT = '<exe>'

@dataclass(frozen=True)
class Patch:
    owner: str
    slot_rva: int
    target: str
    target_rva: int
    model_address: int

@dataclass(frozen=True)
class Linked:
    images: tuple[tuple[str, Layout], ...]
    patches: tuple[Patch, ...]
    execution_allowed: bool = False

def link(raw, catalog, *, bases=None):
    require(type(raw) is bytes, 'immutable EXE required')
    require(type(catalog) is dict, 'explicit catalog required')
    # plan validates catalog names, collisions, contents, and budgets.
    catalog = dict(catalog)
    resolved = plan(raw, catalog)
    canonical = {module_key(k): v for k, v in catalog.items()}
    sources = {ROOT: raw, **{k:canonical[k] for k in resolved.modules}}
    if bases is None:
        bases = {}
    require(type(bases) is dict and all(k in sources for k in bases),
            'unknown model base')
    bases = dict(bases)
    metadata = {k:Image(v, allow_dll=k!=ROOT) for k,v in sources.items()}
    require(sum(i.size for i in metadata.values()) <= MAX_TOTAL_IMAGE,
            'total image budget')
    ranges = []
    selected = {}
    for k,i in metadata.items():
        base = bases.get(k,i.base)
        require(type(base) is int and base >= 65536 and base % 65536 == 0
                and base+i.size <= 2**47, 'model base')
        require(i.size <= MAX_MODEL, 'model size limit')
        selected[k] = base
        ranges.append((base,base+i.size))
    Image.no_overlap(ranges,'model address collision')

    grouped = {k:[] for k in sources}
    for binding in resolved.bindings:
        grouped[binding.owner].append(binding)
    patches = []
    for k,i in metadata.items():
        slots = i.import_slots
        require(len(slots)==len(grouped[k]), 'binding count mismatch')
        if not slots and not i.iat_terminators:
            continue
        start,size = i.directory(12)
        require(size > 0, 'explicit IAT directory required')
        # Every IAT slot and terminator must be distinct, backed and non-executable.
        all_slots = [s[2] for s in slots] + i.iat_terminators
        Image.no_overlap([(s,s+8) for s in all_slots], 'IAT slot collision')
        reloc_bytes = {byte for r in i.reloc_targets for byte in range(r,r+8)}
        for s in all_slots:
            require(start <= s and s+8 <= start+size, 'slot outside IAT directory')
            require(not i.section(s,8).flags & 0x20000000, 'executable IAT')
            i.rva(s,8)
            require(not any(b in reloc_bytes for b in range(s,s+8)),
                    'IAT relocation collision')
            # Reject overlap with other declared RVA directory ranges.
            for idx,(r,z) in enumerate(i.dirs):
                if idx in (4,12) or not z:
                    continue
                require(s+8 <= r or s >= r+z, 'IAT directory collision')
        for (dll,symbol,s,original),binding in zip(slots,grouped[k]):
            require(module_key(dll)==binding.imported_module
                    and type(symbol) is type(binding.symbol)
                    and symbol==binding.symbol, 'binding identity mismatch')
            require(i.u64(i.rva(s,8))==original, 'IAT differs from lookup')
            target = metadata[binding.target_module]
            target.section(binding.target_rva,1)
            address = selected[binding.target_module]+binding.target_rva
            patches.append(Patch(k,s,binding.target_module,binding.target_rva,address))

    # No mutable state leaves this function on failure. Map only after preflight.
    layouts = {k:model(v,selected[k],allow_dll=k!=ROOT) for k,v in sources.items()}
    edits = {}
    for p in patches:
        if p.owner not in edits:
            edits[p.owner] = bytearray(layouts[p.owner].data)
        struct.pack_into('<Q',edits[p.owner],p.slot_rva,p.model_address)
    result = []
    for k,l in layouts.items():
        data = bytes(edits[k]) if k in edits else l.data
        result.append((k,Layout(l.base,data,l.entry_rva,l.relocations)))
    return Linked(tuple(result),tuple(patches))
