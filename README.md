# WinStyle — WS-02B2
Подсистема совместимости Windows-приложений для StyleOS. Скачал → установил → запустил → работаешь. Пока лабораторная реализация, не готовый runtime.

## Единая точка входа
[PROJECT](docs/PROJECT.md) → [AGENTS](AGENTS.md) → [STATE](docs/STATE.md) → [NEXT](docs/NEXT.md). [Концепция](docs/CONCEPT.md), [архитектура](docs/ARCHITECTURE.md), [дорожная карта](ROADMAP.md), [история](docs/HISTORY.md).

## Этап WS-02B2
Ветка feature/ws02b2-exports. Статический анализ PE32+ AMD64 DLL: EAT, имена, ordinal, пропуски, forwarder. Проверено на собственных реально скомпонованных DLL, включая перенаправление по имени и номеру, NONAME и одинаковые RVA разных ordinal. Сверка GNU objdump. Локально 88/88 тестов (22 новых относительно B1), WS-01 4/4; старый fuzz 26096, новый fuzz DLL 14096, без неожиданных исключений. CI финального коммита ещё проверить. Предыдущий коммит d69395b37efb176fef862390238f42852a699bd2 прошёл CI 45908050414. [Отчёт](docs/WS02B2.md).

## Запуск тестов
Linux x86-64, Python 3.10+, clang, lld-link, cc, GNU binutils (objdump), GCC для sanitizer. sh run.sh; sh run_sanitizers.sh. Анализ: python3 peexports.py build/export_cases.dll. Произвольные EXE и DLL не исполняются. Разрешён только собственный лабораторный fixture WS-01. Статический профиль не означает безопасность. Не проверены связывание, разрешение цепочек forwarder, полный Windows API и интеграция.

Работа только LPYURA2/WinStyle. StyleOS, Style Kernel и LPYURA2/OS не трогать.
