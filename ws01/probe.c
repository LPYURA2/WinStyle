/* Host-only experiment. Never loads a user-supplied executable. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include "fixture.h"
static uint16_t u16(size_t o) { return (uint16_t)fixture[o] | (uint16_t)fixture[o+1]<<8; }
static uint32_t u32(size_t o) { return (uint32_t)u16(o) | (uint32_t)u16(o+2)<<16; }
static int fits(size_t o,size_t n) { return o<=sizeof fixture && n<=sizeof fixture-o; }
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"Rejected fixture: %s\n",#c); return 1; } } while(0)
typedef uint64_t (__attribute__((ms_abi)) *entry_fn)(uint64_t,uint64_t,uint64_t,uint64_t);
int main(void) {
    CHECK(fits(0,64) && u16(0)==0x5a4d);
    size_t p=u32(60); CHECK(fits(p,24) && u32(p)==0x4550 && u16(p+4)==0x8664);
    size_t opt=p+24, n=u16(p+20); CHECK(n>=112 && fits(opt,n) && u16(opt)==0x20b);
    CHECK(u16(p+6)==1); /* exact restricted fixture profile */
    uint32_t ep=u32(opt+16), dirs=u32(opt+108);
    CHECK(dirs<=16 && n>=112+8*dirs);
    for (unsigned i=0;i<dirs;i++) CHECK(u32(opt+112+8*i)==0 && u32(opt+116+8*i)==0);
    size_t s=opt+n; CHECK(fits(s,40) && !memcmp(fixture+s,".text\0\0\0",8));
    uint32_t vs=u32(s+8), va=u32(s+12), raw=u32(s+16), off=u32(s+20), flags=u32(s+36);
    CHECK((flags&0xe0000000u)==0x60000000u && vs>0 && vs<=4096 && raw>=vs && fits(off,raw));
    CHECK(ep>=va && ep-va<vs);
    long page=sysconf(_SC_PAGESIZE); CHECK(page>=4096);
    void *mem=mmap(NULL,(size_t)page,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); CHECK(mem!=MAP_FAILED);
    memcpy(mem,fixture+off,vs);
    if(mprotect(mem,(size_t)page,PROT_READ|PROT_EXEC)!=0) { munmap(mem,(size_t)page); return 1; }
    entry_fn fn=(entry_fn)((unsigned char*)mem+(ep-va));
    uint64_t cases[][5]={{1,2,3,4,50},{0,0,0,0,0},{11,22,33,44,550},{UINT64_MAX,1,0,0,2}};
    int failed=0;
    for(size_t i=0;i<sizeof cases/sizeof cases[0];i++) {
        uint64_t *c=cases[i], r=fn(c[0],c[1],c[2],c[3]);
        int ok=r==c[4]; failed+=!ok;
        printf("case %zu: %s (actual=%llu expected=%llu)\n",i+1,ok?"PASS":"FAIL",(unsigned long long)r,(unsigned long long)c[4]);
    }
    munmap(mem,(size_t)page);
    printf("%d/4 PASS\n",4-failed); return failed!=0;
}
