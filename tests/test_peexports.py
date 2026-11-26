import struct
import unittest
from pathlib import Path
from pecheck import Image, Rejected, Unsupported
from peexports import inspect_dll

B = Path('build/dependency.dll').read_bytes()
I = Image(B, allow_dll=True)
R,Z = I.directory(0)
E = I.rva(R,40)
P = struct.unpack_from('<I',B,60)[0]
D = P+24+112
EAT = I.rva(I.u32(E+28),4)
N = I.rva(I.u32(E+32),4)
O = I.rva(I.u32(E+36),2)

def change(off, fmt, val, raw=B):
    b=bytearray(raw)
    struct.pack_into('<'+fmt,b,off,val)
    return bytes(b)

class Exports(unittest.TestCase):
    def test_real(self):
        r=inspect_dll(B)
        self.assertEqual(r['exports'][0]['names'],['demo'])
        self.assertEqual(r['export_dll_name'],'dependency.dll')
        self.assertEqual(r['exports'][0]['ordinal'],1)
        self.assertNotIn(0,r['directories_not_deeply_validated'])
        self.assertFalse(r['execution_allowed'])
    def test_old_profile(self):
        with self.assertRaises(Unsupported): Image(B)
    def test_no_entry(self):
        self.assertEqual(I.entry,0)
    def test_exe_rejected(self):
        with self.assertRaises(Unsupported): inspect_dll(Path('build/import_reloc.exe').read_bytes())
    def test_mutable(self):
        with self.assertRaises(Rejected): inspect_dll(bytearray(B))
    def test_ordinal_only(self):
        r=inspect_dll(change(E+24,'I',0))
        self.assertEqual(r['exports'][0]['names'],[])
    def test_no_exports(self):
        self.assertEqual(inspect_dll(change(D,'Q',0))['exports'],[])
    def test_forwarder(self):
        # Reuse an existing in-directory string as a structurally valid forwarder.
        r=inspect_dll(change(EAT,'I',I.u32(E+12)))
        self.assertEqual(r['exports'][0]['forwarder'],'dependency.dll')
    def test_bad_export_header(self):
        with self.assertRaises(Rejected): inspect_dll(change(D+4,'I',39))
    def test_bad_count(self):
        with self.assertRaises(Rejected): inspect_dll(change(E+20,'I',65537))
    def test_ordinal_overflow(self):
        with self.assertRaises(Rejected): inspect_dll(change(E+20,'I',2,change(E+16,'I',0xffffffff)))
    def test_bad_table(self):
        with self.assertRaises(Rejected): inspect_dll(change(E+28,'I',0xfffffffc))
    def test_bad_name(self):
        with self.assertRaises(Rejected): inspect_dll(change(N,'I',0xffffffff))
    def test_bad_ordinal(self):
        with self.assertRaises(Rejected): inspect_dll(change(O,'H',1))
    def test_named_hole(self):
        with self.assertRaises(Rejected): inspect_dll(change(EAT,'I',0))
    def test_bad_target(self):
        with self.assertRaises(Rejected): inspect_dll(change(EAT,'I',0xffffffff))
    def test_forwarder_truncated(self):
        # Export directory ends before DLL name's NUL, but remaining file bytes exist.
        addr=I.u32(E+12)
        raw=change(D+4,'I',addr-R+1,change(EAT,'I',addr))
        with self.assertRaises(Rejected): inspect_dll(raw)
