"""Static bounded PE32+ inspection. Never loads or executes image code."""
import struct, sys, json
from dataclasses import dataclass, asdict
MAX_FILE=64*1024*1024
MAX_IMAGE=256*1024*1024
MAX_ITEMS=65536
class Rejected(ValueError): pass
class Unsupported(Rejected): pass
def require(cond, reason):
    if not cond: raise Rejected(reason)
def support(cond, reason):
    if not cond: raise Unsupported(reason)
def align(n,a): return (n+a-1)//a*a
def power2(n): return n>0 and n&(n-1)==0
@dataclass(frozen=True)
class Section:
    name:str; rva:int; virtual_size:int; raw_offset:int; raw_size:int; flags:int
    @property
    def span(self): return max(self.virtual_size,self.raw_size)
class Image:
    def __init__(self,b):
        self.b=b; self.sections=[]; self.dirs=[]; self.imports=[]; self.reloc_count=0; self.unchecked=[]; self.string_bytes=0
        require(len(b)<=MAX_FILE,'file limit')
        require(self.read(0,2)==b'MZ','DOS magic')
        p=self.u32(60); require(p>=64,'PE offset'); require(self.read(p,4)==b'PE\0\0','PE signature')
        machine,n,_,sym,nsym,osz,flags=self.unpack('<HHIIIHH',p+4)
        support(machine==0x8664,'machine is not AMD64'); require(1<=n<=96,'section count')
        require(flags&2,'not executable'); support(not flags&0x3000,'system image or DLL'); support(not flags&0x100,'32-bit flag')
        support(sym==nsym==0,'COFF symbol table')
        self.flags=flags; o=p+24; self.read(o,osz); require(osz>=112,'optional header size')
        support(self.u16(o)==0x20b,'not PE32+'); self.entry=self.u32(o+16); self.base=self.u64(o+24)
        sa,fa=self.unpack('<II',o+32); self.size, self.headers=self.unpack('<II',o+56)
        self.subsystem=self.u16(o+68); support(self.subsystem in (2,3),'not desktop/console EXE')
        support(power2(fa) and 512<=fa<=65536 and power2(sa) and sa>=4096 and sa>=fa,'alignment profile')
        require(self.base%65536==0 and self.base>=65536 and self.base+self.size<=2**47,'image base')
        require(0<self.size<=MAX_IMAGE and self.size%sa==0,'image size')
        t=o+osz; require(t+40*n<=self.headers<=len(b) and self.headers%fa==0,'headers size')
        nd=self.u32(o+108); support(nd<=16,'directory count'); require(112+8*nd<=osz,'directory header truncated')
        for i in range(n):
            s=t+40*i; name=self.read(s,8).split(b'\0')[0].decode('ascii','backslashreplace')
            vs,va,rs,ro=self.unpack('<IIII',s+8); sf=self.u32(s+36)
            section=Section(name,va,vs,ro,rs,sf)
            require(section.span>0 and va%sa==0 and va>=align(self.headers,sa),'section virtual range')
            require(va+align(section.span,sa)<=self.size,'section exceeds image')
            if rs:
                require(ro>=self.headers and ro%fa==0 and rs%fa==0,'section raw alignment'); self.read(ro,rs)
            support(sf&0xa0000000!=0xa0000000,'writable executable section')
            self.sections.append(section)
        self.no_overlap([(s.rva,s.rva+align(s.span,sa)) for s in self.sections],'virtual overlap')
        self.no_overlap([(s.raw_offset,s.raw_offset+s.raw_size) for s in self.sections if s.raw_size],'raw overlap')
        epsec=self.section(self.entry,1); require(epsec.flags&0x20000000,'entry not executable'); self.rva(self.entry,1)
        require(self.entry-epsec.rva<(epsec.virtual_size or epsec.raw_size),'entry in padding')
        for i in range(nd):
            r,z=self.unpack('<II',o+112+8*i); require(bool(r)==bool(z),'half-empty directory')
            self.dirs.append((r,z))
            if not z: continue
            if i==4:
                require(r%8==0 and r>=self.headers,'certificate offset'); self.read(r,z)
                require(all(r+z<=s.raw_offset or r>=s.raw_offset+s.raw_size for s in self.sections if s.raw_size),'certificate overlaps raw data')
            else: self.rva(r,z)
            if i not in (1,5): self.unchecked.append(i)
        if self.directory(1)[1]: self.parse_imports()
        if self.directory(5)[1]: self.parse_relocs()
        if self.directory(12)[1]:
            r,z=self.directory(12); require(r%8==0 and z%8==0,'IAT alignment')
        # All unsupported directories are explicit, never imply readiness to execute.
    def read(self,o,n):
        require(0<=o<=len(self.b) and 0<=n<=len(self.b)-o,'file bounds'); return self.b[o:o+n]
    def unpack(self,fmt,o):
        n=struct.calcsize(fmt); return struct.unpack(fmt,self.read(o,n))
    def u16(self,o): return self.unpack('<H',o)[0]
    def u32(self,o): return self.unpack('<I',o)[0]
    def u64(self,o): return self.unpack('<Q',o)[0]
    @staticmethod
    def no_overlap(ranges,reason):
        ranges.sort(); require(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])),reason)
    def directory(self,i): return self.dirs[i] if i<len(self.dirs) else (0,0)
    def section(self,r,n):
        require(0<=r<self.size and 0<n<=self.size-r,'RVA bounds')
        for s in self.sections:
            if s.rva<=r and r+n<=s.rva+s.span: return s
        raise Rejected('RVA not mapped in section')
    def rva(self,r,n):
        s=self.section(r,n); d=r-s.rva; require(d+n<=s.raw_size,'RVA not backed by file'); return s.raw_offset+d
    def string(self,r):
        s=self.section(r,1); o=self.rva(r,1); end=min(s.raw_offset+s.raw_size,o+4096)
        e=self.b.find(b'\0',o,end); require(e>o,'invalid import string')
        self.string_bytes+=e-o; require(self.string_bytes<=4*1024*1024,'import string budget')
        v=self.b[o:e]; require(all(32<=x<127 for x in v),'non-ASCII import string'); return v.decode('ascii')
    def parse_imports(self):
        r,z=self.directory(1); require(z>=20,'import directory size'); total=0; done=False
        for k in range(min(z//20,4096)):
            a=self.unpack('<IIIII',self.rva(r+k*20,20))
            if not any(a): done=True; break
            ilt,stamp,forward,name,iat=a; support(stamp==0 and forward==0,'bound/forwarded import descriptor')
            require(name and iat,'missing import fields'); require(iat%8==0 and (ilt or iat)%8==0,'thunk alignment')
            dll=self.string(name); names=[]; table=ilt or iat
            # Stay within a single raw-backed section for each table.
            ts=self.section(table,8); ins=self.section(iat,8)
            for j in range(MAX_ITEMS):
                total+=1; require(total<=MAX_ITEMS,'import item limit')
                require(self.section(table+j*8,8)==ts and self.section(iat+j*8,8)==ins,'thunk crosses section')
                v=self.u64(self.rva(table+j*8,8)); self.rva(iat+j*8,8)
                if v==0:
                    require(self.u64(self.rva(iat+j*8,8))==0,'IAT terminator'); break
                if v>>63:
                    require(v&0x7fffffffffff0000==0,'ordinal reserved bits'); names.append('#'+str(v&65535))
                else:
                    require(v<=0xffffffff,'import name RVA'); self.rva(v,2); names.append(self.string(v+2))
            else: raise Rejected('unterminated thunks')
            self.imports.append({'dll':dll,'symbols':names})
        require(done,'unterminated import descriptors')
    def parse_relocs(self):
        r,z=self.directory(5); require(not self.flags&1,'relocations stripped'); pos=0; targets=set(); entries=0; blocks=0
        while pos<z:
            blocks+=1; require(blocks<=MAX_ITEMS,'relocation block limit')
            require(z-pos>=8,'relocation header'); page,n=self.unpack('<II',self.rva(r+pos,8))
            require(page%4096==0 and page<self.size and n>=8 and n%4==0 and n<=z-pos,'relocation block')
            for j in range(8,n,2):
                entries+=1; require(entries<=MAX_ITEMS,'relocation item limit')
                v=self.u16(self.rva(r+pos+j,2)); typ=v>>12
                if not typ: continue
                support(typ==10,'relocation type not DIR64'); target=page+(v&4095); self.section(target,8)
                require(all(x not in targets for x in range(target,target+8)),'overlapping relocations'); targets.update(range(target,target+8)); self.reloc_count+=1
            pos+=n
            require(pos<=z,'relocation end')
    def report(self):
        return {'status':'STATIC_PROFILE_OK','execution_allowed':False,'entry_rva':self.entry,'image_base':self.base,'image_size':self.size,'sections':[asdict(s) for s in self.sections],'imports':self.imports,'dir64_relocations':self.reloc_count,'directories_not_deeply_validated':self.unchecked,'note':'Not a Windows loader, malware scanner, or execution approval.'}
def main():
    if len(sys.argv)!=2: print('Usage: python3 pecheck.py FILE.exe',file=sys.stderr); return 2
    try:
        with open(sys.argv[1],'rb') as f: b=f.read(MAX_FILE+1)
        print(json.dumps(Image(b).report(),indent=2)); return 0
    except Unsupported as e: print(json.dumps({'status':'UNSUPPORTED_PROFILE','reason':str(e),'execution_allowed':False})); return 3
    except (Rejected,OSError) as e: print(json.dumps({'status':'REJECTED','reason':str(e),'execution_allowed':False})); return 1
if __name__=='__main__': sys.exit(main())
