__declspec(dllimport) int demo(int);
__declspec(dllexport) int wrap(int x) { return demo(x)+2; }
