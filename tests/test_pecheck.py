import unittest,struct
from pathlib import Path
from pecheck import Image,Rejected,Unsupported
F=Path('ws01/build/fixture.exe').read_bytes(); B=Path('build/import_reloc.exe').read_bytes()
P=struct.unpack_from('<I',B,60)[0]; O=P+24; S=O+struct.unpack_from('<H',B,P+20)[0]; D=O+112
I=Image(B); IMP=I.rva(*I.directory(1)); REL=I.rva(*I.directory(5)); ILT=I.rva(struct.unpack_from('<I',B,IMP)[0],8)
def mutate(o,fmt,v,b=B):
    b=bytearray(b); struct.pack_into('<'+fmt,b,o,v); return bytes(b)
class Positive(unittest.TestCase):
    def test_simple(self): self.assertEqual(Image(F).imports,[])
    def test_import(self): self.assertEqual(Image(B).imports,[{'dll':'dependency.dll','symbols':['demo']}])
    def test_relocation(self): self.assertEqual(Image(B).reloc_count,1)
    def test_never_execute(self): self.assertIs(Image(B).report()['execution_allowed'],False)
    def test_overlay(self): self.assertEqual(Image(B+b'overlay').imports, I.imports)
    def test_iat_disclosed(self): self.assertIn(12,Image(B).unchecked)
    def test_ordinal(self): self.assertEqual(Image(mutate(ILT,'Q',0x8000000000000001)).imports[0]['symbols'],['#1'])
class Negative(unittest.TestCase):
    pass
CASES=[
 ('dos_magic',0,'H',0),('pe_offset',60,'I',0xffffffff),('pe_before_dos',60,'I',4),('pe_magic',P,'I',0),
 ('machine',P+4,'H',0xaa64),('section_zero',P+6,'H',0),('section_limit',P+6,'H',97),('no_exec',P+22,'H',0),('dll',P+22,'H',0x2002),('driver',P+22,'H',0x1002),('coff_symbols',P+12,'I',1),
 ('optional_small',P+20,'H',111),('optional_huge',P+20,'H',65535),('pe32',O,'H',0x10b),('subsystem',O+68,'H',1),('entry_zero',O+16,'I',0),('entry_data',O+16,'I',0x3000),('entry_padding',O+16,'I',0x1100),('image_base',O+24,'Q',0xffffffffffff0000),('file_alignment',O+36,'I',513),('section_alignment',O+32,'I',512),('image_limit',O+56,'I',0xfffff000),('header_limit',O+60,'I',0xffffffff),('directory_count',O+108,'I',17),('raw_offset',S+20,'I',0xfffffe00),('raw_overlap',S+40+20,'I',I.sections[0].raw_offset),('raw_header_overlap',S+20,'I',0),('virtual_overlap',S+40+12,'I',I.sections[0].rva),('virtual_outside',S+12,'I',0xfffff000),('section_huge',S+8,'I',0xffffffff),('rwx',S+36,'I',0xe0000020),('import_dir_half',D+8,'I',0),('import_dir_short',D+12,'I',19),('import_dir_no_terminator',D+12,'I',20),('import_name',IMP+12,'I',0xffffffff),('iat_zero',IMP+16,'I',0),('iat_align',IMP+16,'I',1),('thunk_bad_rva',ILT,'Q',0x100000000),('ordinal_bits',ILT,'Q',0x8000000000010000),('reloc_block_size',REL+4,'I',0),('reloc_page',REL,'I',0xfffff000),('reloc_type',REL+8,'H',0x3000),('reloc_duplicate',REL+10,'H',struct.unpack_from('<H',B,REL+8)[0]),('reloc_stripped',P+22,'H',0x23),('certificate_overlap',D+32,'I',I.sections[0].raw_offset),('iat_size',D+12*8+4,'I',7)]
def make(o,fmt,v):
    def test(self):
        with self.assertRaises(Rejected): Image(mutate(o,fmt,v))
    return test
for name,o,fmt,v in CASES: setattr(Negative,'test_'+name,make(o,fmt,v))
# Certificate overlap with both fields populated (not just a half-empty directory).
def cert(self):
    with self.assertRaisesRegex(Rejected,'certificate overlaps'): Image(mutate(D+36,'I',8,mutate(D+32,'I',I.sections[0].raw_offset)))
Negative.test_cert_overlap_full=cert
if __name__=='__main__': unittest.main()
