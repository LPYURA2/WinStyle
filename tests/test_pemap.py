import struct
import unittest
from pathlib import Path
from pecheck import Image, Rejected, Unsupported
from pemap import model

B = Path('build/import_reloc.exe').read_bytes()
F = Path('ws01/build/fixture.exe').read_bytes()
I = Image(B)
R = I.rva(*I.directory(5))
PAGE = I.u32(R)
TARGET = PAGE + (I.u16(R+8) & 4095)

class TestLayout(unittest.TestCase):
    def test_headers(self):
        self.assertEqual(model(B).data[:I.headers], B[:I.headers])
    def test_size(self):
        self.assertEqual(len(model(B).data), I.size)
    def test_sections(self):
        for s in I.sections:
            self.assertEqual(model(B).data[s.rva:s.rva+s.raw_size], B[s.raw_offset:s.raw_offset+s.raw_size])
    def test_gaps_zero(self):
        self.assertEqual(model(B).data[I.headers:I.sections[0].rva], bytes(I.sections[0].rva-I.headers))
    def test_rebase(self):
        old = struct.unpack_from('<Q', model(B).data, TARGET)[0]
        for delta in (65536, -65536):
            result = model(B, I.base+delta)
            self.assertEqual(struct.unpack_from('<Q', result.data, TARGET)[0], old+delta)
            self.assertEqual(result.relocations, 1)
    def test_fixed(self):
        with self.assertRaises(Unsupported): model(F, Image(F).base+65536)
    def test_bases(self):
        for base in (0, I.base+1, 2**47, True, 'bad'):
            with self.assertRaises(Rejected): model(B, base)
    def test_invalid(self):
        with self.assertRaises(Rejected): model(B[:50])
    def test_immutable(self):
        with self.assertRaises(Rejected): model(bytearray(B))
        self.assertIsInstance(model(B).data, bytes)
    def test_no_exec(self):
        self.assertFalse(model(B).execution_allowed)
        self.assertEqual(model(B).relocations, 0)
    def test_budget(self):
        b = bytearray(B)
        p = struct.unpack_from('<I', b, 60)[0]
        struct.pack_into('<I', b, p+24+56, 64*1024*1024)
        with self.assertRaisesRegex(Rejected, 'model size limit'): model(bytes(b))
    def test_overlay_not_mapped(self):
        self.assertEqual(model(B+b'overlay').data, model(B).data)
