# WinStyle
Независимая штатная среда Windows-приложений рядом с .tea в будущей StyleOS. **Скачал → установил → запустил → работаешь.** Пока лабораторный прототип.
## Единая точка входа
[PROJECT](docs/PROJECT.md) → [AGENTS](AGENTS.md) → [STATE](docs/STATE.md) → [NEXT](docs/NEXT.md).
[Концепция](docs/CONCEPT.md) · [Архитектура](docs/ARCHITECTURE.md) · [Интеграция](docs/INTEGRATION.md) · [Дорожная карта](ROADMAP.md) · [История](docs/HISTORY.md).
## Принятая база
WS-02B3: статический анализ PE32+ EXE/DLL, экспорты, модель размещения и резолвер зависимостей. Код 6ec426bae707990780888dce8ec0a2fff5ed9040, CI 45972835515 SUCCESS: 114/114, 52408 fuzz-входов. [Отчёт](docs/WS02B3.md).
Linux x86-64, Python 3.10+, clang, lld-link, gcc, GNU objdump. sh run.sh; sh run_sanitizers.sh. Только собственный WS-01 fixture исполняется. Статический профиль не гарантирует безопасность.
Main — проверенный код. Работа исключительно в LPYURA2/WinStyle, StyleOS и ядро не трогать.
