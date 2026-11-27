"""Deterministic bounded fuzz of the non-executing linker on owned PE fixtures."""
import random
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pecheck import Rejected
from pebind import link, ROOT

rng=random.Random(2026112704)
raws=[Path('build/ring_root.exe').read_bytes(),Path('build/ring_a.dll').read_bytes(),Path('build/ring_b.dll').read_bytes()]
counts=[0,0]

def check(inputs):
    try:
        result=link(inputs[0],{'ring_a.dll':inputs[1],'ring_b.dll':inputs[2]})
        images=dict(result.images)
        assert result.execution_allowed is False
        assert ROOT in images
        ranges=sorted((v.base,v.base+len(v.data)) for v in images.values())
        assert all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:]))
        seen=set()
        for p in result.patches:
            assert (p.owner,p.slot_rva) not in seen
            seen.add((p.owner,p.slot_rva))
            assert 0<=p.slot_rva<=len(images[p.owner].data)-8
            assert 0<=p.target_rva<len(images[p.target].data)
            assert p.model_address==images[p.target].base+p.target_rva
            assert struct.unpack_from('<Q',images[p.owner].data,p.slot_rva)[0]==p.model_address
        assert all(type(v.data) is bytes and not v.execution_allowed for v in images.values())
        counts[0]+=1
    except Rejected:
        counts[1]+=1

check(raws)
for i,raw in enumerate(raws):
    for n in range(len(raw)):
        inputs=list(raws)
        inputs[i]=raw[:n]
        check(inputs)
for _ in range(2000):
    inputs=list(raws)
    i=rng.randrange(3)
    b=bytearray(inputs[i])
    for __ in range(rng.randrange(1,9)):
        b[rng.randrange(len(b))]^=rng.randrange(1,256)
    if rng.randrange(7)==0:
        del b[rng.randrange(len(b)):]
    inputs[i]=bytes(b)
    check(inputs)
assert counts[0]>0 and counts[1]>0
print(f'bind fuzz: {sum(counts)} cases; accepted={counts[0]}, rejected={counts[1]}, 0 unexpected exceptions')
