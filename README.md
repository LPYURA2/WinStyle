# WinStyle — WS-02B4
Цель: скачал → установил → запустил → работаешь. WinStyle — самостоятельная штатная среда рядом с .tea.
[PROJECT](docs/PROJECT.md) · [STATE](docs/STATE.md) · [NEXT](docs/NEXT.md) · [INTEGRATION](docs/INTEGRATION.md).
Ветка feature/ws02b4-iat. Первый коммит 9dfa043339476432c087583a43e3bee23265b7a4: CI 45975496596 SUCCESS, 129/129 и 52408 прежних fuzz-входов. Расширены тесты: реальный цикл обычных импортов A↔B, проверка IAT preflight и отдельный fuzz связывания; 8 новых тестов, ожидаемо 137. Новый CI ещё проверить, локально не запускалось. [Отчёт](docs/WS02B4.md).
Linux x86-64: sh run.sh; sh run_sanitizers.sh. Только статическая модель, не исполнение. Main — WS-02B3. StyleOS и ядро не трогать.
