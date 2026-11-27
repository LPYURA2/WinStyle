# Состояние проекта
Принятая лабораторная база WS-02B3: 6ec426bae707990780888dce8ec0a2fff5ed9040, feature/ws02b3-resolver, CI https://github.com/LPYURA2/WinStyle/actions/runs/45972835515 SUCCESS. 114/114, EXE fuzz 26096, DLL fuzz 14096, layout fuzz 4072, resolver fuzz 8144, всего 52408, 0 неожиданных исключений. WS-01 4/4, GCC/Clang sanitizer PASS (Clang без function; относится к C fixture, не Python). Первый B3 62753a8, CI 45972387545 SUCCESS 106/106. Обычный циклический граф импортов отдельно не проверен.
WS-02B2: 8ca2d310da0a9b737924518dd84684ac7915bb60, CI 45970337644 SUCCESS 90/90.
WS-02B1: 665c67fbbdb6aa29c44a8bd636fbb1b4f2263483, CI 45906662294 SUCCESS; модель 32 МиБ без исполнения.
WS-02A: c2d3e86f7156a61893c8d8a3c650f85c20cc0091, CI 45906593876 SUCCESS.
Не готовы: IAT, динамическая загрузка, Windows API, изоляция, интеграция. Следующая ветка feature/ws02b4-iat. Проверять фактический SHA/CI. Документационные коммиты не меняют принятую реализацию.
