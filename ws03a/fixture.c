/* Trusted owned PE fixture. No Windows APIs or external dependencies. */
unsigned long long entry(unsigned long long mode, unsigned long long a,
                         unsigned long long b, unsigned long long c) {
    if (mode == 1) __builtin_trap();
    if (mode == 2) for (;;) __asm__ volatile("pause");
    return a + 3*b + 5*c;
}
