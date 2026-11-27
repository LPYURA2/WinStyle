__declspec(dllimport) int ring_b(int);
__declspec(dllexport) int ring_a(int n) { return n > 0 ? ring_b(n-1)+1 : 0; }
