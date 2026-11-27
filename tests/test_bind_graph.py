"""Owned fixtures: ordinary cyclic import graph, and negative IAT preflight."""
import struct
import unittest
from pathlib import Path
from pecheck import Image, Rejected
from pebind import link, ROOT
from pemap import model
from peresolve import plan

R=Path('build/ring_root.exe').read_bytes()
A=Path('build/ring_a.dll').read_bytes()
B=Path('build/ring_b.dll').read_bytes()
CAT={'ring_a.dll':A,'ring_b.dll':B}
EXE=Path('build/import_reloc.exe').read_bytes()
DEP=Path('build/dependency.dll').read_bytes()
I=Image(EXE)
S=I.import_slots[0][2]
DIR=I.u32(60)+24+112

def change(raw, offset, fmt, *values):
    b=bytearray(raw)
    struct.pack_into(fmt,b,offset,*values)
    return bytes(b)

class BindGraph(unittest.TestCase):
    def test_real_cycle_plan(self):
        p=plan(R,CAT)
        self.assertEqual(p.modules,('ring_a.dll','ring_b.dll'))
        self.assertEqual([(v.owner,v.target_module) for v in p.bindings],
                         [(ROOT,'ring_a.dll'),('ring_a.dll','ring_b.dll'),('ring_b.dll','ring_a.dll')])
    def test_real_cycle_bind(self):
        p=link(R,CAT)
        images=dict(p.images)
        self.assertEqual(len(p.patches),3)
        for v in p.patches:
            self.assertEqual(struct.unpack_from('<Q',images[v.owner].data,v.slot_rva)[0],
                             images[v.target].base+v.target_rva)
        self.assertFalse(p.execution_allowed)
    def test_cycle_missing(self):
        with self.assertRaisesRegex(Rejected,'missing DLL: ring_b.dll'):
            link(R,{'ring_a.dll':A})
    def test_cycle_order(self):
        self.assertEqual(link(R,CAT),link(R,{'ring_b.dll':B,'ring_a.dll':A}))
    def test_cycle_only_iat_changes(self):
        p=link(R,CAT)
        for owner,layout in p.images:
            raw=R if owner==ROOT else CAT[owner]
            expected=bytearray(model(raw,allow_dll=owner!=ROOT).data)
            for v in p.patches:
                if v.owner==owner:
                    struct.pack_into('<Q',expected,v.slot_rva,v.model_address)
            self.assertEqual(layout.data,expected)
    def test_iat_terminator_outside_directory(self):
        bad=change(EXE,DIR+12*8+4,'<I',8)
        with self.assertRaisesRegex(Rejected,'slot outside IAT directory'):
            link(bad,{'dependency.dll':DEP})
    def test_iat_directory_collision(self):
        # A previously unused RVA directory overlaps the first IAT slot.
        bad=change(EXE,DIR+2*8,'<II',S,8)
        with self.assertRaisesRegex(Rejected,'IAT directory collision'):
            link(bad,{'dependency.dll':DEP})
    def test_iat_relocation_collision(self):
        # Redirect the fixture's single DIR64 relocation to the IAT slot.
        r,_=I.directory(5)
        offset=I.rva(r,12)
        bad=change(EXE,offset,'<IIHH',S&~4095,12,0xa000|(S&4095),0)
        with self.assertRaisesRegex(Rejected,'IAT relocation collision'):
            link(bad,{'dependency.dll':DEP})
