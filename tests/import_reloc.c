__declspec(dllimport) int demo(int);
int value=7;
int *volatile ptr=&value;
int entry(void) {return demo(*ptr);}
