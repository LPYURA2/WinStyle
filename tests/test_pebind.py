import struct
import unittest
from pathlib import Path
from unittest.mock import patch
from pecheck import Image, Rejected, Unsupported
from pebind import link, ROOT
from pemap import model

EXE=Path('build/import_reloc.exe').read_bytes()
DEP=Path('build/dependency.dll').read_bytes()
BRIDGE=Path('build/bridge.dll').read_bytes()
GRAPH=Path('build/bridge_root.exe').read_bytes()
FIX=Path('ws01/build/fixture.exe').read_bytes()
CAT={'dependency.dll':DEP,'bridge.dll':BRIDGE}
I=Image(EXE)
D=Image(DEP,allow_dll=True)
B=Image(BRIDGE,allow_dll=True)
SLOT=I.import_slots[0][2]

def modify(raw,off,fmt,value):
    b=bytearray(raw)
    struct.pack_into(fmt,b,off,value)
    return bytes(b)

class Link(unittest.TestCase):
    def test_direct(self):
        r=link(EXE,CAT)
        images=dict(r.images)
        self.assertEqual(tuple(images),(ROOT,'dependency.dll'))
        self.assertEqual(len(r.patches),1)
        p=r.patches[0]
        self.assertEqual(p.slot_rva,SLOT)
        self.assertEqual(p.model_address,D.base+p.target_rva)
        self.assertEqual(struct.unpack_from('<Q',images[ROOT].data,SLOT)[0],p.model_address)
        self.assertFalse(r.execution_allowed)
        self.assertTrue(all(not v.execution_allowed for v in images.values()))
    def test_transitive(self):
        r=link(GRAPH,CAT)
        images=dict(r.images)
        self.assertEqual(tuple(images),(ROOT,'bridge.dll','dependency.dll'))
        self.assertEqual([(p.owner,p.target) for p in r.patches],
                         [(ROOT,'bridge.dll'),('bridge.dll','dependency.dll')])
        for p in r.patches:
            self.assertEqual(struct.unpack_from('<Q',images[p.owner].data,p.slot_rva)[0],
                             images[p.target].base+p.target_rva)
    def test_patch_only(self):
        r=link(EXE,CAT)
        mapped=model(EXE).data
        actual=dict(r.images)[ROOT].data
        self.assertEqual(actual[:SLOT],mapped[:SLOT])
        self.assertEqual(actual[SLOT+8:],mapped[SLOT+8:])
    def test_rebase_exe(self):
        r=link(EXE,CAT,bases={ROOT:I.base+65536})
        self.assertEqual(dict(r.images)[ROOT].base,I.base+65536)
        self.assertEqual(dict(r.images)[ROOT].relocations,1)
    def test_collision(self):
        with self.assertRaisesRegex(Rejected,'address collision'):
            link(GRAPH,CAT,bases={'bridge.dll':D.base})
    def test_fixed_base(self):
        with self.assertRaises(Unsupported):
            link(FIX,{},bases={ROOT:Image(FIX).base+65536})
    def test_missing(self):
        with self.assertRaisesRegex(Rejected,'missing DLL'):
            link(GRAPH,{'bridge.dll':BRIDGE})
    def test_bad_iat(self):
        bad=modify(EXE,I.rva(SLOT,8),'<Q',123)
        with self.assertRaisesRegex(Rejected,'IAT differs'):
            link(bad,CAT)
    def test_missing_iat_directory(self):
        p=I.u32(60)+24+112+12*8
        bad=modify(EXE,p,'<Q',0)
        with self.assertRaisesRegex(Rejected,'explicit IAT'):
            link(bad,CAT)
    def test_unknown_base(self):
        with self.assertRaisesRegex(Rejected,'unknown model base'):
            link(EXE,CAT,bases={'unused.dll':65536})
    def test_budget(self):
        with patch('pebind.MAX_TOTAL_IMAGE',I.size+D.size-1):
            with self.assertRaisesRegex(Rejected,'total image budget'):
                link(EXE,CAT)
    def test_no_import(self):
        r=link(FIX,{})
        self.assertEqual(r.patches,())
        self.assertEqual(dict(r.images)[ROOT],model(FIX))
    def test_reproducible(self):
        self.assertEqual(link(GRAPH,CAT),link(GRAPH,dict(reversed(list(CAT.items())))))
    def test_rollback(self):
        before=EXE
        with self.assertRaises(Rejected):
            link(EXE,{})
        self.assertEqual(EXE,before)
        self.assertEqual(link(EXE,CAT),link(EXE,CAT))
    def test_dll_model_opt_in(self):
        with self.assertRaises(Rejected):
            model(DEP)
        self.assertFalse(model(DEP,allow_dll=True).execution_allowed)
