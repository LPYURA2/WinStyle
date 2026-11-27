# Состояние проекта
Принятая лабораторная база WS-02B2: 8ca2d310da0a9b737924518dd84684ac7915bb60, feature/ws02b2-exports, CI https://github.com/LPYURA2/WinStyle/actions/runs/45970337644 SUCCESS. Перенесена fast-forward в main. 90/90 тестов, WS-01 4/4, EXE fuzz 26096, DLL fuzz 14096, ноль неожиданных исключений; GCC и Clang ASan/UBSan PASS (Clang без function). В предыдущем CI 83c2705 два теста переносимости не прошли; исправлены. 
WS-02B1: 665c67fbbdb6aa29c44a8bd636fbb1b4f2263483, CI 45906662294 SUCCESS; модель 32 МиБ без исполнения, отдельный fuzz модели ещё не проведён.
WS-02A: c2d3e86f7156a61893c8d8a3c650f85c20cc0091, CI 45906593876 SUCCESS.
Не готовы: связывание импортов, динамическая загрузка, Windows API, изоляция недоверенного исполнения, интеграция в StyleOS. Текущая рабочая ветка feature/ws02b3-resolver. Проверять её фактический SHA и CI. Документационные коммиты не меняют принятую реализацию.
