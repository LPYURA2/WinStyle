"""Build-time validation of a fixed, owned fixture; not a security verifier."""
from pathlib import Path
from pecheck import Image, require
from pemap import model

MAX_FIXTURE=65536

def inspect_fixture(raw):
    require(type(raw) is bytes,'immutable fixture')
    i=Image(raw)
    require(i.size<=MAX_FIXTURE and i.size%4096==0,'fixture size')
    require(not i.reloc_targets,'fixture relocations unsupported')
    require(len(i.import_slots)==1 and len(i.iat_terminators)==1,'one import required')
    dll,symbol,slot,original=i.import_slots[0]
    require(dll.lower()=='kernel32.dll' and symbol=='GetCurrentProcessId','unexpected API')
    require(i.u64(i.rva(slot,8))==original,'IAT differs from lookup')
    r,z=i.directory(12)
    term=i.iat_terminators[0]
    require(z and r<=slot and slot+8<=r+z and term==slot+8 and term+8<=r+z,'IAT range')
    require(not i.section(slot,16).flags&0x20000000,'executable IAT')
    code=[s for s in i.sections if s.flags&0x20000000]
    require(len(code)==1 and code[0].name=='.text','one code section')
    s=code[0]
    require(s.rva%4096==0 and s.flags&0xe0000000==0x60000000,'code protection')
    span=((s.span+4095)//4096)*4096
    require(s.rva+span<=i.size,'code range')
    require(all(not sec.flags&0x80000000 for sec in i.sections),'writable section unsupported')
    require(all(not z or n in (1,3,12) for n,(_,z) in enumerate(i.dirs)),'unsupported fixture directory')
    require(s.rva<=i.entry<s.rva+s.virtual_size,'entry range')
    return model(raw).data, i.entry, slot, s.rva, span

def main():
    image,entry,slot,code,span=inspect_fixture(Path('build/ws03b/fixture.exe').read_bytes())
    Path('build/ws03b/fixture.h').write_text(
        'static const unsigned char fixture[] = {'+','.join(map(str,image))+'};\n'
        +f'enum {{ FIX_ENTRY={entry}, FIX_IAT={slot}, FIX_CODE={code}, FIX_CODE_SIZE={span} }};\n')

if __name__=='__main__':
    main()
