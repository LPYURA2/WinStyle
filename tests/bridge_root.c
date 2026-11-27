__declspec(dllimport) int wrap(int);
int entry(void) { return wrap(7); }
