# WinStyle
Подсистема совместимости Windows-приложений для StyleOS. **Скачал → установил → запустил → работаешь.** Без ручной настройки VM, контейнеров, префиксов и библиотек. Пока лабораторный прототип.
## Единая точка входа
[PROJECT](docs/PROJECT.md) → [AGENTS](AGENTS.md) → [STATE](docs/STATE.md) → [NEXT](docs/NEXT.md).
[Концепция](docs/CONCEPT.md) · [Архитектура](docs/ARCHITECTURE.md) · [Будущая интеграция](docs/INTEGRATION.md) · [Дорожная карта](ROADMAP.md) · [История](docs/HISTORY.md).
## Принятая база
WS-02B2: статический анализ EXE/DLL, экспорты и forwarder, модель размещения EXE без исполнения. Код 8ca2d310da0a9b737924518dd84684ac7915bb60, CI 45970337644 SUCCESS, 90/90. [Отчёт](docs/WS02B2.md).
Linux x86-64, Python 3.10+, clang, lld-link, gcc, GNU objdump. sh run.sh; sh run_sanitizers.sh. Только собственный WS-01 fixture исполняется. Статический профиль не гарантирует безопасность.
Main — проверенный код; каждый этап в отдельной ветке со своим README. Работа исключительно в LPYURA2/WinStyle, не трогать StyleOS и ядро.
