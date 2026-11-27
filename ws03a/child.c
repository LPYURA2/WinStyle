/* Trusted fixture only; resource limits are not a security sandbox. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>
#include "fixture.h"

typedef uint64_t (__attribute__((ms_abi)) *entry_fn)(uint64_t,uint64_t,uint64_t,uint64_t);

static int limit(int kind, rlim_t value) {
    struct rlimit r={value,value};
    return setrlimit(kind,&r);
}

int main(int argc,char **argv) {
    if (argc!=2) return 64;
    if (limit(RLIMIT_CORE,0) || limit(RLIMIT_CPU,3) ||
        limit(RLIMIT_AS,128u*1024u*1024u) || limit(RLIMIT_FSIZE,4096))
        return 70;
    uint64_t mode;
    if (!strcmp(argv[1],"normal")) mode=0;
    else if (!strcmp(argv[1],"fault")) mode=1;
    else if (!strcmp(argv[1],"hang")) mode=2;
    else if (!strcmp(argv[1],"output")) {
        char b[1024]; memset(b,'X',sizeof b);
        for (unsigned i=0;i<16;i++)
            if (write(STDOUT_FILENO,b,sizeof b)!=(ssize_t)sizeof b) return 71;
        return 72;
    } else return 64;

    long n=sysconf(_SC_PAGESIZE);
    if(n<4096 || sizeof fixture>(size_t)n || fixture_entry>=sizeof fixture) return 70;
    void *mem=mmap(NULL,(size_t)n,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(mem==MAP_FAILED) return 70;
    memcpy(mem,fixture,sizeof fixture);
    if(mprotect(mem,(size_t)n,PROT_READ|PROT_EXEC)) { munmap(mem,(size_t)n); return 70; }
    entry_fn fn=(entry_fn)((unsigned char*)mem+fixture_entry);
    uint64_t result=fn(mode,1,2,3);
    if(munmap(mem,(size_t)n)) return 70;
    printf("RESULT=%llu\n",(unsigned long long)result);
    return result==22 ? 0 : 73;
}
