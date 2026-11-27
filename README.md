# WinStyle
Независимая штатная среда Windows-приложений рядом с .tea в будущей StyleOS. **Скачал → установил → запустил → пользуешься.** Лабораторный прототип.
## Единая точка входа
[PROJECT](docs/PROJECT.md) → [AGENTS](AGENTS.md) → [STATE](docs/STATE.md) → [NEXT](docs/NEXT.md).
[Концепция](docs/CONCEPT.md) · [Архитектура](docs/ARCHITECTURE.md) · [Интеграция](docs/INTEGRATION.md) · [Дорожная карта](ROADMAP.md) · [История](docs/HISTORY.md) · [Архив версий](docs/VERSIONS.md).
## Принятая база
WS-03A e705bd4166060a540fcccbe3a5240f26b60ce324, CI 45979039941 SUCCESS, 143/143, 60553 прежних fuzz-входа. Статический PE loader model и исполнение только собственных фиксированных fixtures в отдельном host-процессе. [Отчёт](docs/WS03A.md).
Linux x86-64, Python 3.10+, clang, lld-link, gcc, objdump: sh run.sh; sh run_sanitizers.sh. Не sandbox, не запуск произвольных EXE.
Main — проверенный код, archive/ — неизменяемые по соглашению проекта версии, feature/ — разработка. Перед продвижением main архивировать прежний SHA. Работа только LPYURA2/WinStyle; StyleOS и ядро не трогать.
