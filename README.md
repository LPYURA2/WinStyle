# WinStyle
Независимая штатная среда Windows-приложений рядом с .tea в будущей StyleOS. **Скачал → установил → запустил → работаешь.** Пока лабораторный прототип.
## Единая точка входа
[PROJECT](docs/PROJECT.md) → [AGENTS](AGENTS.md) → [STATE](docs/STATE.md) → [NEXT](docs/NEXT.md).
[Концепция](docs/CONCEPT.md) · [Архитектура](docs/ARCHITECTURE.md) · [Интеграция](docs/INTEGRATION.md) · [Дорожная карта](ROADMAP.md) · [История](docs/HISTORY.md) · [Архив версий](docs/VERSIONS.md).
## Принятая база
WS-02B4, 631551159c7bde8935ffdccf33d9f1b095c3857b, CI 45977376972 SUCCESS: 137/137 и 60553 fuzz-входа. Статическая модель PE32+ EXE/DLL, зависимости, IAT, обычные циклы импортов. [Отчёт](docs/WS02B4.md).
Linux x86-64, Python 3.10+, clang, lld-link, gcc, GNU objdump. sh run.sh; sh run_sanitizers.sh. Только собственный WS-01 fixture исполняется.
Main — проверенный код, archive/ — предыдущие проверенные версии, feature/ — разработка. Перед обновлением main сохранить её прежнюю вершину. Не удалять ветки и не переписывать историю. Работа только LPYURA2/WinStyle; StyleOS и ядро не трогать.
