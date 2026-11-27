__declspec(dllimport) int ring_a(int);
__declspec(dllexport) int ring_b(int n) { return n > 0 ? ring_a(n-1)+1 : 0; }
