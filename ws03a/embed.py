"""Build-time only: extract the exact owned fixture under a narrow static profile."""
from pathlib import Path
from pecheck import Image

raw=Path('build/ws03a/fixture.exe').read_bytes()
img=Image(raw)
assert len(img.sections)==1 and not img.import_slots and not img.reloc_targets
assert not any(z for _,z in img.dirs)
s=img.sections[0]
assert s.name=='.text' and s.flags & 0xe0000000 == 0x60000000
assert 0 < s.virtual_size <= 4096 and s.virtual_size <= s.raw_size
assert s.rva <= img.entry < s.rva+s.virtual_size
code=raw[s.raw_offset:s.raw_offset+s.virtual_size]
Path('build/ws03a/fixture.h').write_text(
    'static const unsigned char fixture[] = {'+','.join(map(str,code))+'};\n'
    +'static const unsigned int fixture_entry = '+str(img.entry-s.rva)+';\n')
