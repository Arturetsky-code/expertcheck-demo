# ExpertCheck 10.0 Alpha 1 — Evidence-Driven Requirements Engine

## Цель
Переход от semantic search по требованиям к evidence-driven проверке.

## Основные изменения
- Table Cell Reconstruction 2.0: таблицы Задания читаются через PyMuPDF `find_tables()`; геометрический parser оставлен fallback.
- Requirement Scope & Contract Engine: область требования, метод проверки, ожидаемые разделы и минимальный состав доказательств.
- Project-global числовые требования (например, продолжительность смены) могут проверяться без искусственного object owner.
- Object/equipment-specific значения по-прежнему требуют совпадения владельца.
- Normative KB 4.0 разделяет LAW_REQUIREMENT, ENGINEERING_RULE и EXPERT_PRACTICE_RULE.
- Неверифицированный пункт НТД = KB_GAP, а не риск проекта.
- Evidence Reasoner получает только конкретное требование и evidence packet; `NOT_FOUND` не может стать нарушением.
- Global Non-Finding Rule применён к рискам ИРД: отсутствие автоматической находки больше не формирует риск.
- Отчёты показывают покрытие проверки Задания и НТД вместо количества псевдорисков.

## Реальный regression по ЗНП ДСК
- 56 атомарных требований;
- 56/56 восстановлены из конкретных ячеек (`TABLE_CELL_LOCKED`);
- строка 15: «Продолжительность смены – 12 часов»;
- строка 22: «Производственная мощность 1 600 тыс. тонн в год»;
- строка 23: состав объектов по Приложению 1;
- строка 27: ДСК 500 т/ч, автосамосвал 32 м³ и другие условия разделены на отдельные требования.

## Тесты
- 254 passed;
- 8 historical PDF-dependent tests cannot run because their external fixtures are absent from `/mnt/data`;
- smoke test OK;
- compileall OK.
