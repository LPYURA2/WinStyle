/* Trusted build artifact only. No arbitrary PE loading or syscall isolation. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>
#include "fixture.h"

typedef uint32_t (__attribute__((ms_abi)) *api_fn)(void);
typedef uint64_t (__attribute__((ms_abi)) *entry_fn)(uint64_t);
static unsigned calls;
static uint32_t __attribute__((ms_abi,noinline)) ws_GetCurrentProcessId(void) {
    ++calls;
    return (uint32_t)getpid();
}
static int limit(int kind, rlim_t value) {
    struct rlimit r={value,value};
    return setrlimit(kind,&r);
}
int main(void) {
    if(limit(RLIMIT_CORE,0)||limit(RLIMIT_CPU,3)||
       limit(RLIMIT_AS,128u*1024u*1024u)||limit(RLIMIT_FSIZE,4096)) return 70;
    if(sysconf(_SC_PAGESIZE)!=4096) return 70;
    _Static_assert(sizeof(api_fn)==8,"x86-64 pointer required");
    _Static_assert(FIX_IAT+8<=sizeof fixture,"IAT bound");
    _Static_assert(FIX_ENTRY>=FIX_CODE && FIX_ENTRY<FIX_CODE+FIX_CODE_SIZE,"entry bound");
    _Static_assert(FIX_CODE+FIX_CODE_SIZE<=sizeof fixture,"code bound");
    void *mem=mmap(NULL,sizeof fixture,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(mem==MAP_FAILED) return 70;
    unsigned char *p=mem;
    memcpy(p,fixture,sizeof fixture);
    api_fn api=ws_GetCurrentProcessId;
    memcpy(p+FIX_IAT,&api,sizeof api);
    /* Full image becomes R; only fixed code pages become RX. Never RWX. */
    if(mprotect(p,sizeof fixture,PROT_READ)||
       mprotect(p+FIX_CODE,FIX_CODE_SIZE,PROT_READ|PROT_EXEC)) {
        munmap(mem,sizeof fixture);
        return 70;
    }
    entry_fn entry=(entry_fn)(p+FIX_ENTRY);
    uint64_t result=entry(7);
    uint32_t pid=(uint32_t)getpid();
    if(munmap(mem,sizeof fixture)) return 70;
    printf("PID=%u RESULT=%llu CALLS=%u\n",pid,(unsigned long long)result,calls);
    return calls==1 && result==(uint64_t)pid+7 ? 0:73;
}
