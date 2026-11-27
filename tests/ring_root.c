__declspec(dllimport) int ring_a(int);
int entry(void) { return ring_a(2); }
