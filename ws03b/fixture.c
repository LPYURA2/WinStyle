/* Owned PE fixture: one Win32 import, no CRT. */
__declspec(dllimport) unsigned long GetCurrentProcessId(void);
unsigned long long entry(unsigned long long a) {
    return (unsigned long long)GetCurrentProcessId() + a;
}
